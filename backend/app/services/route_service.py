"""Route CRUD, validation and the enable gate.

Every rule from the architecture is enforced here rather than in the API layer,
because the same rules must hold for a worker-initiated change:

* the domain belongs to the active organization (a foreign id is a 404, never a
  403 that confirms it exists);
* the hostname is **covered** by that domain, computed label-wise by
  :func:`app.core.dnsname.hostname_is_covered` — never by substring;
* the node belongs to the organization and passes the routing pre-flight;
* the container lives on *that* node and publishes the requested port (the
  container-internal port is not addressable and never accepted);
* a route can never become enabled merely because its rows were saved:
  :func:`enable_route` re-checks the domain's *current* status, the container's
  *current* state and the node's *current* pre-flight, then hands the change to
  the apply pipeline.

Enabling also attaches the HTTP uptime monitor (opt-out per route) and disabling
parks it, so the monitor never probes a route that is not being served.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, TypedDict

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.dnsname import (
    InvalidName,
    canonicalize_name,
    canonicalize_path,
    hostname_is_covered,
)
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.core.logging import get_logger
from app.core.pagination import PageParams, paginate
from app.models import Container, Domain, Monitor, Route, Server
from app.models.enums import (
    ActorType,
    ContainerStatus,
    DomainStatus,
    MonitorStatus,
    MonitorTargetType,
    RouteConfigState,
)
from app.schemas.route import RouteCreate, RouteUpdate
from app.services import audit_service, event_bus, proxy_service

log = get_logger("nexusops.routes")

#: How long an auto-attached route monitor may wait between checks.
MONITOR_INTERVAL_SECONDS = 60
#: Consecutive failures before the auto monitor opens an incident.
MONITOR_FAILURE_THRESHOLD = 3


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _actor(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


async def get_route(db: AsyncSession, route_id: uuid.UUID) -> Route:
    route = await db.get(Route, route_id)
    if route is None:
        raise NotFound("Route not found", code="ROUTE_NOT_FOUND")
    return route


async def list_routes(
    db: AsyncSession,
    params: PageParams,
    *,
    domain_id: uuid.UUID | None = None,
    node_id: uuid.UUID | None = None,
    enabled: bool | None = None,
    config_state: RouteConfigState | None = None,
) -> tuple[list[Route], int]:
    stmt = select(Route)
    if domain_id is not None:
        stmt = stmt.where(Route.domain_id == domain_id)
    if node_id is not None:
        stmt = stmt.where(Route.node_id == node_id)
    if enabled is not None:
        stmt = stmt.where(Route.enabled.is_(enabled))
    if config_state is not None:
        stmt = stmt.where(Route.config_state == config_state)
    stmt = stmt.order_by(Route.hostname.asc(), Route.path.asc())
    return await paginate(db, stmt, params)


class RouteMetadata(TypedDict):
    """The name/row lookups a route list needs, keyed by the ids routes carry.

    Typed rather than ``dict[str, dict[str, Any]]`` so a caller cannot silently
    read ``.get()`` with the wrong key type — the keys are UUIDs, and mypy proves
    every lookup at the call site matches the dict it is looking in.
    """

    domain_names: dict[uuid.UUID, str]
    node_names: dict[uuid.UUID, str]
    containers: dict[uuid.UUID, Container]


async def relevant_metadata(db: AsyncSession, routes: list[Route]) -> RouteMetadata:
    """Names for the ids a route list shows, in three queries rather than 3N."""
    if not routes:
        return {"domain_names": {}, "node_names": {}, "containers": {}}
    domain_ids = {route.domain_id for route in routes}
    node_ids = {route.node_id for route in routes}
    container_ids = {route.container_id for route in routes if route.container_id}
    domains = {
        row.id: row.name
        for row in (await db.execute(select(Domain).where(Domain.id.in_(domain_ids))))
        .scalars()
        .all()
    }
    nodes = {
        row.id: row.name
        for row in (await db.execute(select(Server).where(Server.id.in_(node_ids)))).scalars().all()
    }
    containers: dict[uuid.UUID, Container] = {}
    if container_ids:
        containers = {
            row.id: row
            for row in (await db.execute(select(Container).where(Container.id.in_(container_ids))))
            .scalars()
            .all()
        }
    return {
        "domain_names": dict(domains),
        "node_names": dict(nodes),
        "containers": containers,
    }


# --- validation helpers --------------------------------------------------------


async def _resolve_domain(db: AsyncSession, domain_id: uuid.UUID) -> Domain:
    domain = await db.get(Domain, domain_id)
    if domain is None:
        raise NotFound("Domain not found", code="DOMAIN_NOT_FOUND")
    return domain


async def _resolve_node(db: AsyncSession, node_id: uuid.UUID) -> Server:
    node = await db.get(Server, node_id)
    if node is None:
        raise NotFound("Node not found", code="NODE_NOT_FOUND")
    return node


async def _resolve_container(
    db: AsyncSession, *, container_id: uuid.UUID, node: Server
) -> Container:
    """The container must exist, be on *node*, and be inside the organization.

    The tenant part is free: ``db.get`` runs under the org scope, so a container
    in another organization is simply absent. The node check is the real rule —
    a route may only ever point at an upstream on its own node in Phase 4.
    """
    container = await db.get(Container, container_id)
    if container is None:
        raise NotFound("Container not found", code="CONTAINER_NOT_FOUND")
    if container.server_id != node.id:
        raise UnprocessableEntity(
            "The container must run on the route's node",
            code="CONTAINER_NOT_ON_NODE",
        )
    return container


def _require_published_port(container: Container, port: int) -> None:
    """Refuse a port the container does not actually publish on the node."""
    usable = {item.host_port for item in proxy_service.usable_upstream_ports(container)}
    if port not in usable:
        if port in proxy_service.RESERVED_HOST_PORTS:
            raise UnprocessableEntity(
                f"Port {port} is reserved by the node's proxy and cannot be a route upstream",
                code="PORT_RESERVED",
            )
        raise UnprocessableEntity(
            f"Container '{container.name}' does not publish TCP port {port} on this node. "
            "Pick a published port from the container's inventory.",
            code="PORT_NOT_PUBLISHED",
        )


async def _require_verified_hostname_owner(db: AsyncSession, *, hostname: str) -> None:
    """A redirect target must be a name this organization has verified."""
    candidate = canonicalize_name(hostname, allow_wildcard=True)
    rows = (
        (await db.execute(select(Domain).where(Domain.status == DomainStatus.VERIFIED).limit(200)))
        .scalars()
        .all()
    )
    if not any(hostname_is_covered(candidate, domain.name) for domain in rows):
        raise UnprocessableEntity(
            "The redirect target must be a hostname covered by one of this organization's "
            "verified domains",
            code="REDIRECT_TARGET_UNVERIFIED",
        )


async def _validate_shape(
    db: AsyncSession,
    *,
    domain: Domain,
    hostname: str,
    path: str,
    node: Server,
    container: Container,
    port: int,
    redirect: dict[str, Any] | None,
) -> None:
    if not hostname_is_covered(hostname, domain.name):
        raise UnprocessableEntity(
            f"'{hostname}' is not covered by the domain '{domain.name}'. A route may use the "
            "domain name itself, a single-label subdomain of it, or the domain's wildcard form.",
            code="HOSTNAME_NOT_COVERED",
        )
    if path.startswith("/.") or "//" in path or ".." in path:
        raise UnprocessableEntity("Unsupported path", code="ROUTE_PATH_INVALID")
    if redirect is not None:
        await _require_verified_hostname_owner(db, hostname=redirect["to_host"])
    if container.server_id != node.id:
        raise UnprocessableEntity(
            "The container must run on the route's node", code="CONTAINER_NOT_ON_NODE"
        )
    _require_published_port(container, port)


async def _conflicting_route(
    db: AsyncSession,
    *,
    node_id: uuid.UUID,
    hostname: str,
    path: str,
    exclude: uuid.UUID | None = None,
) -> Route | None:
    stmt = select(Route).where(
        Route.node_id == node_id,
        Route.hostname == hostname,
        Route.path == path,
        Route.enabled.is_(True),
    )
    if exclude is not None:
        stmt = stmt.where(Route.id != exclude)
    return (await db.execute(stmt.limit(1))).scalar_one_or_none()


# --- CRUD ----------------------------------------------------------------------


async def create_route(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    payload: RouteCreate,
    request: Request | None = None,
) -> Route:
    """Create a route. ``enabled=true`` runs the full gate before it is set."""
    try:
        hostname = canonicalize_name(payload.hostname, allow_wildcard=True)
        path = canonicalize_path(payload.path)
    except InvalidName as exc:
        raise UnprocessableEntity(exc.message, code=exc.code) from exc

    domain = await _resolve_domain(db, payload.domain_id)
    node = await _resolve_node(db, payload.node_id)
    container = await _resolve_container(db, container_id=payload.container_id, node=node)
    redirect = payload.redirect.model_dump() if payload.redirect else None
    await _validate_shape(
        db,
        domain=domain,
        hostname=hostname,
        path=path,
        node=node,
        container=container,
        port=payload.port,
        redirect=redirect,
    )
    # Creation is gated on the node's live pre-flight, not only enable: a route
    # saved against a node that cannot serve HTTP is a row that can never be
    # enabled, and the refusal is far more useful at the moment of creation.
    # ``enable_route`` runs the same gate again, because node state moves.
    await proxy_service.require_eligible(node)

    route = Route(
        domain_id=domain.id,
        hostname=hostname,
        path=path,
        node_id=node.id,
        container_id=container.id,
        port=payload.port,
        scheme="http",
        headers=[header.model_dump() for header in payload.headers],
        rate_limit=payload.rate_limit.model_dump() if payload.rate_limit else None,
        redirect=redirect,
        enabled=False,
        config_state=RouteConfigState.PENDING,
        monitor_optout=payload.monitor_optout,
    )
    db.add(route)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(
            "An enabled route already answers for this hostname and path on this node",
            code="ROUTE_CONFLICT",
        ) from exc

    await audit_service.record(
        db,
        ctx,
        action="route.created",
        resource_type="route",
        resource_id=route.id,
        metadata={
            "hostname": hostname,
            "path": path,
            "node_id": str(node.id),
            "port": payload.port,
            "domain": domain.name,
        },
        request=request,
    )
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="ROUTE_CREATED",
        message=f"Route {hostname}{path} created on {node.name}",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="route",
        resource_id=str(route.id),
        data={"hostname": hostname, "path": path},
    )
    if payload.enabled:
        # The gate runs as a separate step so a route is never *saved* enabled:
        # it is saved, validated against live state, then enabled (which queues
        # the apply).
        await enable_route(db, ctx, route_id=route.id, request=request)
        await db.refresh(route)
    return route


async def update_route(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    route_id: uuid.UUID,
    payload: RouteUpdate,
    request: Request | None = None,
) -> Route:
    """Update a route's definition; a change to an enabled route re-applies."""
    route = await get_route(db, route_id)
    data = payload.model_dump(exclude_unset=True)

    domain = await _resolve_domain(db, route.domain_id)
    node = await _resolve_node(db, data.get("node_id") or route.node_id)
    # ``container_id`` is nullable on the row (SET NULL when a container is
    # deleted), so an update of a route whose upstream was removed must say so
    # rather than passing ``None`` where a UUID is required.
    container_id = data.get("container_id") or route.container_id
    if container_id is None:
        raise UnprocessableEntity(
            "The route has no container; set container_id first",
            code="CONTAINER_REQUIRED",
        )
    container = await _resolve_container(db, container_id=container_id, node=node)
    try:
        hostname = (
            canonicalize_name(data["hostname"], allow_wildcard=True)
            if data.get("hostname")
            else route.hostname
        )
        path = canonicalize_path(data["path"]) if data.get("path") else route.path
    except InvalidName as exc:
        raise UnprocessableEntity(exc.message, code=exc.code) from exc
    redirect = (
        data["redirect"]
        if "redirect" in data and data["redirect"] is not None
        else (None if "redirect" in data else route.redirect)
    )
    await _validate_shape(
        db,
        domain=domain,
        hostname=hostname,
        path=path,
        node=node,
        container=container,
        port=data.get("port") or route.port,
        redirect=redirect,
    )

    route.hostname = hostname
    route.path = path
    route.node_id = node.id
    route.container_id = container.id
    if data.get("port"):
        route.port = data["port"]
    if "headers" in data and data["headers"] is not None:
        route.headers = data["headers"]
    if "rate_limit" in data:
        route.rate_limit = data["rate_limit"]
    if "redirect" in data:
        route.redirect = data["redirect"]
    if "monitor_optout" in data and data["monitor_optout"] is not None:
        route.monitor_optout = data["monitor_optout"]
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(
            "An enabled route already answers for this hostname and path on this node",
            code="ROUTE_CONFLICT",
        ) from exc

    await audit_service.record(
        db,
        ctx,
        action="route.updated",
        resource_type="route",
        resource_id=route.id,
        metadata={"fields": sorted(data), "hostname": route.hostname, "path": route.path},
        request=request,
    )
    if route.enabled:
        await proxy_service.enqueue_apply(
            db, node=node, requested_by_id=ctx.user_id if ctx else None, reason="route_updated"
        )
    return route


async def enable_route(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    route_id: uuid.UUID,
    request: Request | None = None,
) -> Route:
    """Turn a route live — the only place ``enabled`` becomes true.

    Three independent conditions, each re-read *now* rather than trusted from the
    row that was saved earlier: the domain is verified, the node still passes the
    routing pre-flight, and the upstream container is running with the port it
    published. Then the monitor is attached and the bundle is applied.
    """
    route = await get_route(db, route_id)
    domain = await _resolve_domain(db, route.domain_id)
    if DomainStatus(domain.status) is not DomainStatus.VERIFIED:
        raise Conflict(
            f"Domain '{domain.name}' is {DomainStatus(domain.status).value.lower()}, so its "
            "routes cannot be enabled. Verify ownership first.",
            code="DOMAIN_NOT_VERIFIED",
        )
    node = await _resolve_node(db, route.node_id)
    await proxy_service.require_eligible(node)
    if route.container_id is None:
        raise Conflict(
            "The route has no upstream container; select a container and port first",
            code="ROUTE_UPSTREAM_MISSING",
        )
    container = await _resolve_container(db, container_id=route.container_id, node=node)
    _require_published_port(container, route.port)
    if container.status != ContainerStatus.RUNNING:
        raise Conflict(
            f"Container '{container.name}' is {str(container.status).lower()}; start it "
            "before enabling this route",
            code="UPSTREAM_NOT_RUNNING",
        )
    conflict = await _conflicting_route(
        db, node_id=node.id, hostname=route.hostname, path=route.path, exclude=route.id
    )
    if conflict is not None:
        raise Conflict(
            f"'{route.hostname}{route.path}' is already served by another enabled route on "
            "this node",
            code="ROUTE_CONFLICT",
        )

    was_enabled = route.enabled
    route.enabled = True
    route.config_state = RouteConfigState.PENDING
    route.last_apply_error = ""
    await db.flush()
    await _sync_route_monitor(db, route=route, ctx=ctx)

    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="ROUTE_ENABLED",
        message=f"Route {route.hostname}{route.path} enabled on {node.name}",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="route",
        resource_id=str(route.id),
        data={"hostname": route.hostname, "path": route.path},
    )
    await audit_service.record(
        db,
        ctx,
        action="route.enabled",
        resource_type="route",
        resource_id=route.id,
        metadata={"hostname": route.hostname, "path": route.path, "was_enabled": was_enabled},
        request=request,
    )
    await proxy_service.enqueue_apply(
        db, node=node, requested_by_id=ctx.user_id if ctx else None, reason="route_enabled"
    )
    return route


async def disable_route(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    route_id: uuid.UUID,
    request: Request | None = None,
) -> Route:
    """Pull a route from the node's configuration.

    The change is *not* live until the node applies the new bundle, so the state
    is left ``PENDING`` and the operator sees "applying" rather than a claim that
    traffic already stopped.
    """
    route = await get_route(db, route_id)
    node = await _resolve_node(db, route.node_id)
    was_enabled = route.enabled
    route.enabled = False
    route.config_state = RouteConfigState.PENDING
    route.last_apply_error = ""
    if route.monitor_id is not None:
        monitor = await db.get(Monitor, route.monitor_id)
        if monitor is not None and monitor.enabled:
            monitor.enabled = False
            monitor.status = MonitorStatus.PAUSED
    await db.flush()

    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="ROUTE_DISABLED",
        message=f"Route {route.hostname}{route.path} disabled on {node.name}",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="route",
        resource_id=str(route.id),
        data={"hostname": route.hostname, "path": route.path},
    )
    await audit_service.record(
        db,
        ctx,
        action="route.disabled",
        resource_type="route",
        resource_id=route.id,
        metadata={"hostname": route.hostname, "was_enabled": was_enabled},
        request=request,
    )
    await proxy_service.enqueue_apply(
        db, node=node, requested_by_id=ctx.user_id if ctx else None, reason="route_disabled"
    )
    return route


async def delete_route(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    route_id: uuid.UUID,
    request: Request | None = None,
) -> None:
    """Delete a route. The fragment disappears on the node's next apply."""
    route = await get_route(db, route_id)
    node = await _resolve_node(db, route.node_id)
    hostname, path, was_enabled = route.hostname, route.path, route.enabled
    route.enabled = False
    await db.flush()
    await db.delete(route)
    await db.flush()
    await event_bus.publish(
        db,
        type="ROUTE_DELETED",
        message=f"Route {hostname}{path} deleted",
        resource_type="route",
        resource_id=str(route.id),
        data={"hostname": hostname, "path": path},
    )
    await audit_service.record(
        db,
        ctx,
        action="route.deleted",
        resource_type="route",
        resource_id=route.id,
        metadata={"hostname": hostname, "path": path, "was_enabled": was_enabled},
        request=request,
    )
    # Deleting the last route still has to reach the node, so the fragment is
    # removed from the live tree rather than only from the database.
    await proxy_service.enqueue_apply(
        db, node=node, requested_by_id=ctx.user_id if ctx else None, reason="route_deleted"
    )


async def _sync_route_monitor(db: AsyncSession, *, route: Route, ctx: AuthContext | None) -> None:
    """Attach (or re-enable) the route's HTTP uptime monitor.

    HTTP only — there is no TLS in Phase 4, so the probe target is
    ``http://<hostname><path>``. The monitor rides the existing check → incident
    → notification pipeline unchanged; the route id is what makes it a
    ``ROUTE`` target rather than a URL target.
    """
    if route.monitor_optout:
        return
    target_host = route.hostname[2:] if route.hostname.startswith("*.") else route.hostname
    url = f"http://{target_host}{route.path}"[:1000]
    if route.monitor_id is not None:
        monitor = await db.get(Monitor, route.monitor_id)
        if monitor is not None:
            monitor.url = url
            monitor.enabled = True
            if monitor.status == MonitorStatus.PAUSED:
                monitor.status = MonitorStatus.PENDING
            monitor.next_check_at = _utcnow()
            await db.flush()
            return
    monitor = Monitor(
        name=f"Route {route.hostname}{route.path}"[:160],
        project_id=None,
        target_type=MonitorTargetType.ROUTE,
        route_id=route.id,
        url=url,
        method="GET",
        interval_seconds=MONITOR_INTERVAL_SECONDS,
        timeout_seconds=10.0,
        expected_status=200,
        headers={},
        enabled=True,
        failure_threshold=MONITOR_FAILURE_THRESHOLD,
        status=MonitorStatus.PENDING,
        next_check_at=_utcnow(),
        created_by_id=ctx.user_id if ctx else None,
    )
    db.add(monitor)
    await db.flush()
    route.monitor_id = monitor.id
    await db.flush()


async def route_status_detail(route: Route) -> str:
    """A short, sanitized explanation of ``config_state`` for the UI."""
    state = RouteConfigState(route.config_state)
    if state is RouteConfigState.IN_SYNC:
        return "Configuration applied on the node"
    if state is RouteConfigState.PENDING:
        return "Waiting for the node to apply the configuration"
    if state is RouteConfigState.STALE:
        return route.last_apply_error or "Not currently served by the node"
    return route.last_apply_error or "The node failed to apply the configuration"


async def route_counts_for_node(db: AsyncSession, node_id: uuid.UUID) -> dict[str, int]:
    row = (
        await db.execute(
            select(
                func.count().label("total"),
                func.count().filter(Route.enabled.is_(True)).label("enabled"),
            ).where(Route.node_id == node_id)
        )
    ).one()
    return {"total": int(row.total or 0), "enabled": int(row.enabled or 0)}
