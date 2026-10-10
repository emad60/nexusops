"""Proxy orchestration: node eligibility, rendering, apply dispatch, results, drift.

This is the only layer that knows about both the database and the provider. Four
responsibilities are kept apart on purpose:

* **Eligibility** — the node's reported nginx capability *and* its routing
  pre-flight are evaluated here, and the same check runs at route creation, at
  enable time and again immediately before an apply, because node state changes
  underneath a stored route.
* **Rendering** — delegated entirely to the provider
  (:mod:`app.providers.nginx`); this module only resolves rows into the plain
  inputs the renderer takes.
* **Dispatch** — bundles become whitelisted ``nginx.*`` operations through
  :func:`app.services.operation_service.queue_operation`, so the capability,
  permission and params guards are the same ones every other operation passes.
* **Results** — an agent's report is asserted, not verified: it is attributed to
  the route ids in the bundle manifest, and it only ever moves ``config_state``
  and the node's bounded ``proxy_state``.

Nothing here writes configuration text anywhere except into operation params
(and never into audit metadata or event payloads).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import Conflict, NotFound
from app.core.logging import get_logger
from app.models import Container, Domain, Operation, Route, Server
from app.models.enums import (
    ContainerStatus,
    DomainStatus,
    EventLevel,
    ListenerOwnership,
    OperationType,
    ProxyApplyOutcome,
    RouteConfigState,
    ServerStatus,
)
from app.providers.nginx import RenderError
from app.providers.nginx import provider as nginx_provider
from app.providers.proxy import ResolvedNode, ResolvedRoute
from app.schemas.proxy import NginxBundle, bundle_summary
from app.schemas.route import (
    NodeProxyCapabilityOut,
    NodeProxyStatusOut,
    UpstreamContainerOut,
    UpstreamPortOut,
)
from app.services import audit_service, event_bus, operation_service

log = get_logger("nexusops.proxy")

#: A capability report is only trusted while the node is still heartbeating. A
#: node that stopped reporting may have had nginx stopped, replaced or broken
#: since — and applying configuration to it is exactly the risk the pre-flight
#: exists to avoid.
CAPABILITY_STALE_AFTER = timedelta(minutes=5)

#: How long a node whose live bundle already *is* the desired one may go without
#: a fresh fingerprint before the reconciler asks for one. A status poll costs a
#: round trip to the node, so a converged node is re-checked on an interval — and
#: a node that is known **not** to match is never merely asked again: that poll
#: loop cannot converge (see :func:`reconcile_node`).
STATUS_REFRESH_AFTER = timedelta(minutes=10)

#: Bounded retry schedule for a node that keeps failing to converge. Attempt *n*
#: waits ``min(RECOVERY_BACKOFF_MAX, RECOVERY_BACKOFF_START * 2 ** (n - 1))``, so
#: a node whose apply keeps failing — the exact shape of a hand-broken nginx — is
#: retried at a bounded rate instead of on every sweep tick. ``recovery_attempts``
#: is reset by the first successful apply.
RECOVERY_BACKOFF_START = timedelta(minutes=1)
RECOVERY_BACKOFF_MAX = timedelta(minutes=30)

# --- reconciliation reason codes ----------------------------------------------
#
# ``reconcile_node`` returns one of these instead of a boolean: "did anything
# happen" is not the useful answer (a node already in sync and a node that cannot
# be reached both change nothing), while *why* is what an operator and the sweep
# counters need.
RECONCILE_IN_SYNC = "in_sync"
RECONCILE_STATUS_REQUESTED = "status_requested"
RECONCILE_RECOVERY_QUEUED = "recovery_queued"
RECONCILE_APPLY_IN_FLIGHT = "apply_in_flight"
RECONCILE_DEFERRED = "deferred"
RECONCILE_BLOCKED = "blocked"
RECONCILE_NO_CHANGE = "no_change"
RECONCILE_IDLE = "idle"

#: Host ports the proxy owns on a node. A container publishing on one of these
#: can never be routed to: nginx needs them for the routes themselves.
RESERVED_HOST_PORTS: frozenset[int] = frozenset({80, 443})

#: Addresses that mean "every interface" or "loopback"; both are reachable from
#: the node's own proxy over the loopback address.
_WILDCARD_BINDS = frozenset({"", "0.0.0.0", "::", "[::]", "*"})  # noqa: S104 - a published host address, not a listen socket


def _utcnow() -> datetime:
    return datetime.now(UTC)


def provider() -> Any:
    """The active :class:`~app.providers.proxy.ProxyProvider`.

    One implementation in Phase 4. The indirection is the seam the architecture
    asked for; it is deliberately not a registry.
    """
    return nginx_provider


# --- capability & eligibility -------------------------------------------------


def capability_of(node: Server) -> dict[str, Any]:
    """The node's reported nginx capability entry, or an empty dict (unreported)."""
    capabilities = node.capabilities or {}
    report = capabilities.get("nginx")
    return report if isinstance(report, dict) else {}


def _listener_state(report: dict[str, Any], port: int) -> ListenerOwnership:
    raw = report.get(f"listener_{port}")
    if not isinstance(raw, str):
        return ListenerOwnership.UNKNOWN
    try:
        return ListenerOwnership(raw)
    except ValueError:
        # An unrecognised state is unreadable, not free.
        return ListenerOwnership.UNKNOWN


def capability_out(node: Server) -> NodeProxyCapabilityOut:
    report = capability_of(node)
    return NodeProxyCapabilityOut(
        present=bool(report.get("present")),
        version=report.get("version") if isinstance(report.get("version"), str) else None,
        running=report.get("running") if isinstance(report.get("running"), bool) else None,
        config_test_ok=(
            report.get("config_test_ok") if isinstance(report.get("config_test_ok"), bool) else None
        ),
        routing_eligible=report.get("routing_eligible") is True,
        reason=str(report.get("reason") or "")[:200],
        listener_80=_listener_state(report, 80).value,
        listener_443=_listener_state(report, 443).value,
    )


def eligibility_error(node: Server, *, now: datetime | None = None) -> tuple[str, str] | None:
    """Why NexusOps may not manage routing on this node — or ``None`` when it may.

    Deliberately more than "nginx is installed": the binary existing says nothing
    about whether *this* node's nginx owns the listeners the routes need, and
    reporting a successful pre-flight merely because a package is present is the
    exact failure mode the pre-flight exists to prevent. The returned code is
    stable and the message names the precise conflict.
    """
    moment = now or _utcnow()
    report = capability_of(node)
    if not report:
        return (
            "NODE_CAPABILITY_UNVERIFIED",
            f"Node '{node.name}' has not reported an nginx capability; upgrade its agent "
            "to protocol 2 and make sure nginx is installed and running",
        )
    if not report.get("present"):
        return (
            "NGINX_NOT_INSTALLED",
            f"Nginx was not found on '{node.name}'. Install nginx on the node, then enroll "
            "or restart the agent so it re-reports",
        )
    if report.get("routing_eligible") is not True:
        # The agent runs the listener/service pre-flight itself and reports one
        # verdict plus a precise reason. Trusting that verdict first keeps the
        # refusal in the node's own words ("port 80 is held by …") instead of the
        # control plane guessing from one flag among several.
        reason = str(report.get("reason") or "").strip()
        return (
            "NGINX_PREFLIGHT_FAILED",
            reason
            or f"The routing pre-flight on '{node.name}' did not pass; check the node's "
            "listeners and nginx state",
        )
    if report.get("running") is not True:
        return (
            "NGINX_NOT_RUNNING",
            f"The nginx service on '{node.name}' is not running (or its master process "
            "could not be found); start it before adding routes",
        )
    if report.get("config_test_ok") is not True:
        return (
            "NGINX_CONFIG_TEST_UNAVAILABLE",
            f"Nginx on '{node.name}' could not validate its configuration; fix "
            "`nginx -t` before routing through this node",
        )
    state_80 = _listener_state(report, 80)
    if state_80 is not ListenerOwnership.MANAGED:
        return (
            "NGINX_LISTENER_CONFLICT",
            _listener_conflict_message(node, 80, state_80),
        )
    state_443 = _listener_state(report, 443)
    if state_443 not in (ListenerOwnership.MANAGED, ListenerOwnership.FREE):
        # 443 is reserved for Phase 5 (certificates) and therefore needs to be
        # either unused or already held by the *managed* nginx. Another process
        # there is a conflict to resolve now, not after certificates ship.
        return (
            "NGINX_LISTENER_CONFLICT",
            _listener_conflict_message(node, 443, state_443),
        )
    if node.status != ServerStatus.ONLINE:
        return (
            "NODE_OFFLINE",
            f"Node '{node.name}' is not online; routing changes cannot be applied to it",
        )
    heartbeat = node.last_heartbeat_at
    if heartbeat is None or (moment - heartbeat) > CAPABILITY_STALE_AFTER:
        return (
            "NODE_CAPABILITY_STALE",
            f"Node '{node.name}' has not reported in recently, so its routing pre-flight "
            "may be out of date; wait for the next heartbeat",
        )
    return None


def _listener_conflict_message(node: Server, port: int, state: ListenerOwnership) -> str:
    if state is ListenerOwnership.OTHER:
        return (
            f"NexusOps routing needs exclusive use of port {port} on '{node.name}' — "
            f"port {port} is held by another process. Stop it (or point nginx at it) and "
            "re-run the pre-flight"
        )
    if state is ListenerOwnership.FREE:
        return (
            f"Port {port} on '{node.name}' is free but the running nginx does not own a "
            f"listener for it; NexusOps cannot confirm it manages that listener"
        )
    return (
        f"The listener owner for port {port} on '{node.name}' could not be determined "
        "safely; NexusOps will not route through a node it cannot inspect"
    )


async def require_eligible(node: Server) -> None:
    """Raise a named conflict when routing may not be managed on this node."""
    problem = eligibility_error(node)
    if problem is not None:
        code, message = problem
        raise Conflict(message, code=code)
    # The agent must also be able to run nginx operations at all; the dispatch
    # guard enforces this too, and doing it here as well keeps the refusal at the
    # point of the user request rather than at apply time.
    operation_service.ensure_node_can_run(node, OperationType.NGINX_APPLY)


# --- upstream resolution ------------------------------------------------------


def upstream_host_for(host_ip: str | None) -> str:
    """The address nginx should proxy to for one published binding.

    A wildcard bind and a loopback bind both become ``127.0.0.1`` (the node's own
    proxy can always reach them there); a binding to a specific address — e.g. a
    docker bridge or a private interface address — is used as reported.
    """
    candidate = (host_ip or "").strip()
    if candidate in _WILDCARD_BINDS:
        return "127.0.0.1"
    if candidate in ("127.0.0.1", "::1", "[::1]"):
        return "127.0.0.1"
    return candidate


def usable_upstream_ports(container: Container) -> list[UpstreamPortOut]:
    """The published ports of *container* that a route may actually point at.

    Honest by construction: an unpublished (expose-only) port, a UDP-only port and
    a port that collides with the proxy's own 80/443 are all excluded, because a
    route to them cannot work. An empty list means "no usable upstream here",
    which the UI shows as such instead of offering something that will 502.
    """
    ports: list[UpstreamPortOut] = []
    for raw in container.ports or []:
        if not isinstance(raw, dict):
            continue
        host_port = raw.get("host_port")
        container_port = raw.get("container_port")
        protocol = str(raw.get("protocol") or "tcp").lower()
        if not isinstance(host_port, int) or not isinstance(container_port, int):
            continue
        if protocol != "tcp":
            continue
        if not (1 <= host_port <= 65535) or not (1 <= container_port <= 65535):
            continue
        if host_port in RESERVED_HOST_PORTS:
            continue
        host_ip = str(raw.get("host_ip") or "")
        ports.append(
            UpstreamPortOut(
                host_port=host_port,
                container_port=container_port,
                protocol=protocol,
                bind_address=host_ip,
                upstream_host=upstream_host_for(host_ip),
            )
        )
    ports.sort(key=lambda p: p.host_port)
    return ports


def container_out(container: Container) -> UpstreamContainerOut:
    ports = usable_upstream_ports(container)
    reason = None
    if container.status != ContainerStatus.RUNNING:
        reason = "the container is not running"
    elif not ports:
        reason = "no published TCP port other than the proxy's own 80/443"
    return UpstreamContainerOut(
        id=container.id,
        container_id=container.container_id,
        name=container.name,
        image_ref=container.image_ref or "",
        status=container.status,
        upstream_ports=ports,
        unavailable_reason=reason,
    )


async def usable_upstreams(db: AsyncSession, *, node_id: uuid.UUID) -> list[UpstreamContainerOut]:
    """Containers on *node_id* that can back a route, for the route editor."""
    rows = (
        (
            await db.execute(
                select(Container)
                .where(Container.server_id == node_id)
                .order_by(Container.name.asc())
                .limit(200)
            )
        )
        .scalars()
        .all()
    )
    return [container_out(row) for row in rows]


# --- rendering ----------------------------------------------------------------


async def _resolved_for(db: AsyncSession, route: Route) -> ResolvedRoute | None:
    """Flatten one enabled route into renderer input, or ``None`` if unrenderable.

    A route whose container or published port disappeared is *excluded* and marked
    stale — never rendered with a guessed upstream. That is what keeps a removed
    container from becoming traffic to the wrong address.
    """
    if route.container_id is None:
        await _mark_route_stale(db, route, "the route has no upstream container")
        return None
    container = await db.get(Container, route.container_id)
    if container is None:
        await _mark_route_stale(db, route, "the upstream container no longer exists")
        return None
    if container.server_id != route.node_id:
        await _mark_route_stale(db, route, "the upstream container is on a different node")
        return None
    bindings = {port.host_port: port for port in usable_upstream_ports(container)}
    binding = bindings.get(route.port)
    if binding is None:
        await _mark_route_stale(
            db,
            route,
            f"port {route.port} is no longer published for this container",
        )
        return None
    if container.status != ContainerStatus.RUNNING:
        # A stopped container has no live upstream; the route keeps its records
        # but leaves the rendered tree until it runs again.
        await _mark_route_stale(db, route, "the upstream container is not running")
        return None
    return ResolvedRoute(
        id=str(route.id),
        hostname=route.hostname,
        path=route.path,
        upstream_host=binding.upstream_host,
        upstream_port=binding.host_port,
        headers=tuple(route.headers or ()),
        rate_limit=dict(route.rate_limit) if route.rate_limit else None,
        redirect=dict(route.redirect) if route.redirect else None,
        metadata={"node_id": str(route.node_id), "domain_id": str(route.domain_id)},
    )


async def _mark_route_stale(db: AsyncSession, route: Route, detail: str) -> None:
    if route.config_state != RouteConfigState.STALE or route.last_apply_error != detail:
        route.config_state = RouteConfigState.STALE
        route.last_apply_error = detail[:500]
        await db.flush()


# --- removal: requested is not confirmed --------------------------------------


def removal_requested_detail(reason: str) -> str:
    """The honest state of a route that left the desired tree but is not gone.

    One sentence, built here so the renderer, the release path, the audit trail,
    the events feed and the UI all reuse it and no path can spell "requested" the
    way it spells "confirmed". Note what it does **not** say: that the route
    stopped being served.
    """
    return (
        f"removal requested: {reason.strip().rstrip('.')}; no node has confirmed the removal yet"
    )[:500]


def removal_confirmed_detail(node_name: str) -> str:
    """What an agent's applied bundle that omits the route actually proves."""
    return (f"removal confirmed: {node_name} applied a configuration without this route")[:500]


async def mark_removal_requested(db: AsyncSession, *, route: Route, reason: str) -> bool:
    """Record that *route* must leave its node's configuration. True when new.

    Called from the two places a route can stop being eligible — the renderer
    (:func:`render_for_node`) and the cross-organization release path — and it
    deliberately does **not** touch ``removal_confirmed_at``. A confirmation stays
    a fact while the route is still excluded, so a re-render on the next sweep
    tick can neither erase it nor manufacture one: the only writer of that column
    is the apply-result handler, driven by what a node said it applied.

    ``config_state`` becomes ``STALE`` (not confirmed live at the desired
    configuration, which is exactly true), ``last_apply_error`` keeps the plain
    *reason* — why the route is excluded, which is what an operator needs first —
    and the half of the removal is carried by the two timestamps, surfaced as
    ``RouteRemovalState`` on the read model.
    """
    now = _utcnow()
    detail = reason.strip()[:500]
    first = route.removal_requested_at is None
    changed = first or route.config_state != RouteConfigState.STALE
    route.config_state = RouteConfigState.STALE
    if first:
        route.removal_requested_at = now
        # The *first* writer of an episode states why, and later ticks do not
        # rewrite it: the release path knows the name was claimed by another
        # organization, while the renderer — which runs again on every sweep —
        # only knows the domain is not serving. Letting the later, vaguer reason
        # win would erase the specific one within seconds.
        route.last_apply_error = detail
    if changed:
        await db.flush()
    return first


async def _confirm_pending_removals(
    db: AsyncSession, *, node: Server, applied: list[str], now: datetime
) -> list[Route]:
    """Mark the removals an applied bundle proves, and return them.

    *applied* is the route-id manifest the agent echoed back, so "the node no
    longer serves this" is read from the node's own report rather than from the
    fact that the control plane stopped rendering it. Only routes whose removal
    was already **requested** and never confirmed qualify — a route excluded for
    an unrelated reason (a stopped upstream, say) keeps its own explanation
    instead of being relabelled as a removal.

    Returns the rows so the caller can audit and announce them.
    """
    rows = (
        (
            await db.execute(
                select(Route).where(
                    Route.node_id == node.id,
                    Route.enabled.is_(True),
                    Route.removal_requested_at.is_not(None),
                    Route.removal_confirmed_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    served = set(applied)
    confirmed: list[Route] = []
    for route in rows:
        if str(route.id) in served:
            continue
        # The *why* stays on the row (it is what the operator reads); what changes
        # is that the node's own report now backs the removal.
        route.removal_confirmed_at = now
        confirmed.append(route)
    if confirmed:
        await db.flush()
    return confirmed


async def _mark_enabled_routes_stale(db: AsyncSession, *, node: Server, detail: str) -> None:
    """Mark every enabled route on *node* unresolved, with one reason.

    Used when the desired tree itself could not be computed: none of these routes
    can be confirmed against a bundle that does not exist, and saying so is the
    honest report. It never claims a route stopped serving — ``STALE`` is "not
    confirmed live at the desired configuration", which is exactly the case.
    """
    rows = (
        (await db.execute(select(Route).where(Route.node_id == node.id, Route.enabled.is_(True))))
        .scalars()
        .all()
    )
    for route in rows:
        await _mark_route_stale(db, route, detail)


async def render_for_node(db: AsyncSession, *, node: Server) -> tuple[NginxBundle, list[Route]]:
    """Render the complete desired state for *node* from the database.

    Only **enabled routes on verified domains** are eligible, which is the single
    place that rule is applied — the renderer never decides ownership. Routes that
    cannot currently be rendered are excluded and marked stale as a side effect;
    the caller owns the transaction.
    """
    rows = (
        await db.execute(
            select(Route, Domain)
            .join(Domain, Domain.id == Route.domain_id)
            .where(Route.node_id == node.id, Route.enabled.is_(True))
            .order_by(Route.hostname.asc(), Route.path.asc())
        )
    ).all()
    resolved: list[ResolvedRoute] = []
    included: list[Route] = []
    for route, domain in rows:
        status = DomainStatus(domain.status)
        if status is not DomainStatus.VERIFIED:
            # Domain lost its proof (or never had it): the route is pulled from
            # the rendered tree immediately and labelled as a removal the node has
            # not confirmed. It is not "stale" in the vague sense any more — it is
            # excluded, and whether it still answers is a fact only the node has.
            await mark_removal_requested(
                db, route=route, reason=f"the domain is {status.value.lower()}"
            )
            continue
        item = await _resolved_for(db, route)
        if item is None:
            continue
        if route.removal_requested_at is not None or route.removal_confirmed_at is not None:
            # Desired again, so the removal episode is over: the markers clear here
            # while ``config_state`` still reports that the apply which puts the
            # route back in service has not happened yet.
            route.removal_requested_at = None
            route.removal_confirmed_at = None
            await db.flush()
        resolved.append(item)
        included.append(route)

    try:
        bundle = provider().render(ResolvedNode(id=str(node.id), name=node.name), resolved)
    except RenderError as exc:
        # A corrupt row must not produce a half-rendered tree: refuse the whole
        # bundle, name the reason, and leave the node's live configuration alone.
        log.error("nginx_render_refused", node=str(node.id), error=str(exc)[:200])
        raise Conflict(
            "The desired configuration could not be rendered; fix the affected route",
            code="ROUTE_RENDER_FAILED",
            details={"reason": str(exc)[:200]},
        ) from exc
    return bundle, included


async def expected_bundle_id(db: AsyncSession, *, node: Server) -> str | None:
    """The bundle fingerprint the node *should* be running, or ``None`` if it has
    no enabled routes and never applied one."""
    if not await _has_enabled_routes(db, node_id=node.id):
        state = node.proxy_state or {}
        if not state.get("applied_bundle_id"):
            return None
    bundle, _ = await render_for_node(db, node=node)
    return bundle.bundle_id


async def _has_enabled_routes(db: AsyncSession, *, node_id: uuid.UUID) -> bool:
    found = await db.scalar(
        select(Route.id).where(Route.node_id == node_id, Route.enabled.is_(True)).limit(1)
    )
    return found is not None


# --- apply dispatch -----------------------------------------------------------


async def enqueue_apply(
    db: AsyncSession,
    *,
    node: Server,
    requested_by_id: uuid.UUID | None = None,
    reason: str,
    force: bool = False,
) -> Operation | None:
    """Render and queue ``nginx.apply`` for *node*.

    Returns the operation, or ``None`` when there is nothing to do (no routes and
    nothing previously applied) or when an apply is already in flight — the
    desired state is idempotent, so a duplicate op only adds agent load.

    Raises the same named conflicts as :func:`require_eligible`, so an operator
    sees *why* a route could not be applied rather than a silent no-op.
    """
    await require_eligible(node)
    bundle, included = await render_for_node(db, node=node)
    state = dict(node.proxy_state or {})
    applied = state.get("applied_bundle_id")
    if bundle.bundle_id == applied and not force:
        log.info(
            "nginx_apply_skipped_unchanged",
            node=str(node.id),
            bundle_id=bundle.bundle_id,
            reason=reason,
        )
        return None
    if not bundle.manifest and not applied:
        return None
    if not force and await operation_service.has_live_operation(
        db, node_id=node.id, op_type=OperationType.NGINX_APPLY
    ):
        log.info("nginx_apply_already_in_flight", node=str(node.id), reason=reason)
        return None

    for route in included:
        route.config_state = RouteConfigState.PENDING
    await db.flush()

    operation = await operation_service.queue_operation(
        db,
        node=node,
        op_type=OperationType.NGINX_APPLY,
        params=provider().apply_params(bundle),
        requested_by_id=requested_by_id,
    )
    state["expected_bundle_id"] = bundle.bundle_id
    state["last_apply_requested_at"] = _utcnow().isoformat()
    node.proxy_state = state
    await db.flush()
    await audit_service.record(
        db,
        None,
        action="route.apply_requested",
        resource_type="node",
        resource_id=node.id,
        org_id=node.org_id,
        metadata={"reason": reason[:120], **bundle_summary(bundle)},
    )
    return operation


async def enqueue_bootstrap(
    db: AsyncSession, *, node: Server, requested_by_id: uuid.UUID | None = None
) -> Operation | None:
    """Queue ``nginx.bootstrap`` once, when the capability first appears."""
    report = capability_of(node)
    if not report.get("present"):
        return None
    state = dict(node.proxy_state or {})
    if state.get("bootstrapped_at") and not state.get("bootstrap_error"):
        return None
    if await operation_service.has_live_operation(
        db, node_id=node.id, op_type=OperationType.NGINX_BOOTSTRAP
    ):
        return None
    try:
        operation = await operation_service.queue_operation(
            db,
            node=node,
            op_type=OperationType.NGINX_BOOTSTRAP,
            params={},
            requested_by_id=requested_by_id,
        )
    except Conflict as exc:
        # The node cannot take nginx operations at all right now; that is a
        # reportable state, not an error for the caller of a hello.
        log.info("nginx_bootstrap_refused", node=str(node.id), code=exc.code)
        return None
    await audit_service.record(
        db,
        None,
        action="nginx.bootstrap_requested",
        resource_type="node",
        resource_id=node.id,
        org_id=node.org_id,
    )
    return operation


async def after_hello(db: AsyncSession, *, node: Server) -> None:
    """React to a node reporting its capabilities.

    Called from the hello endpoint: if the node now reports nginx, queue the
    idempotent ``nginx.bootstrap`` once. Nothing here installs or upgrades nginx —
    that stays a customer-side prerequisite, and the pre-flight is what reports
    whether it is satisfied.
    """
    state = dict(node.proxy_state or {})
    state["last_hello_at"] = _utcnow().isoformat()
    node.proxy_state = state
    await db.flush()
    if not capability_of(node).get("present"):
        return
    await enqueue_bootstrap(db, node=node)


async def request_status(db: AsyncSession, *, node: Server) -> Operation | None:
    """Ask the node for its live proxy state, unless a report is already pending."""
    if await operation_service.has_live_operation(
        db, node_id=node.id, op_type=OperationType.NGINX_STATUS
    ):
        return None
    try:
        return await operation_service.queue_operation(
            db,
            node=node,
            op_type=OperationType.NGINX_STATUS,
            params={},
        )
    except Conflict as exc:
        log.info("nginx_status_refused", node=str(node.id), code=exc.code)
        return None


# --- reconciliation -----------------------------------------------------------


def recovery_backoff(attempts: int) -> timedelta:
    """How long to wait before the next automatic recovery attempt.

    Exponential from :data:`RECOVERY_BACKOFF_START`, capped at
    :data:`RECOVERY_BACKOFF_MAX`. ``attempts`` is 1-based.
    """
    exponent = min(max(int(attempts), 1) - 1, 10)
    return min(RECOVERY_BACKOFF_START * (2**exponent), RECOVERY_BACKOFF_MAX)


def _is_due(raw: Any, window: timedelta) -> bool:
    """Whether a stored timestamp is missing or older than *window*."""
    stamp = _parse_dt(raw)
    return stamp is None or (_utcnow() - stamp) >= window


async def reconcile_node(db: AsyncSession, *, node: Server) -> str:
    """Bring one node's live configuration back to the desired bundle — bounded.

    This is the unattended half of the apply pipeline, and the rule it exists to
    enforce is short: **a difference between the desired bundle and what the node
    is running is repaired, not merely observed.** Asking an out-of-sync node for
    its fingerprint again cannot converge — the node is not misreporting, it is
    running the wrong configuration — so a status poll happens only once there is
    nothing left to repair, and a detected difference queues (at most) one apply.

    Every bound is explicit:

    * one apply at a time — a live ``nginx.apply`` short-circuits the branch, and
      :func:`enqueue_apply` refuses a duplicate anyway;
    * nothing is queued to a node that cannot take it (offline, stale capability,
      listener conflict): the routes stay unresolved and the next tick retries,
      which is also why an offline node never accumulates a queue;
    * a node that keeps failing backs off through ``next_recovery_at`` instead of
      being re-applied on every tick;
    * a difference is reported as repaired only from an actual apply outcome
      (:func:`_handle_apply_result`), never from the attempt.

    Returns one of the ``RECONCILE_*`` reason codes. The caller owns the
    transaction and the tenancy scope: this is per-node work and runs inside the
    node's own organization.
    """
    state = dict(node.proxy_state or {})
    applied = str(state.get("applied_bundle_id") or "")
    live = str(state.get("live_bundle_id") or "")
    confirmed = applied or live

    try:
        bundle, included = await render_for_node(db, node=node)
    except Conflict as exc:
        # The desired tree cannot be computed, so nothing on this node can be
        # confirmed against it. Leave the live configuration untouched and say so.
        await _mark_enabled_routes_stale(
            db,
            node=node,
            detail=f"the desired configuration could not be rendered: {exc.message}",
        )
        state["reconcile_error"] = exc.message[:200]
        node.proxy_state = state
        await db.flush()
        log.warning("nginx_reconcile_blocked", node=str(node.id), code=exc.code)
        return RECONCILE_BLOCKED

    if not await _has_enabled_routes(db, node_id=node.id) and not confirmed:
        # Nothing is served from here and nothing ever was.
        return RECONCILE_IDLE

    desired = bundle.bundle_id
    if desired == confirmed:
        state["drift"] = False
        state["drift_since"] = None
        state["reconcile_error"] = ""
        node.proxy_state = state
        await db.flush()
        # Converged. Only now is a fingerprint worth asking for, and only when the
        # last one is old enough to matter.
        if not _is_due(state.get("last_status_at"), STATUS_REFRESH_AFTER):
            return RECONCILE_IN_SYNC
        queued = await request_status(db, node=node)
        return RECONCILE_STATUS_REQUESTED if queued is not None else RECONCILE_IN_SYNC

    # A genuine difference. The render above already marked every route it had to
    # exclude as STALE *with the reason it was excluded* (the domain is no longer
    # verified, the upstream is gone, …), so the operator reads why the route is
    # not being served; the routes it kept become PENDING when the apply is
    # queued. Nothing here has claimed a route stopped serving yet.
    next_at = _parse_dt(state.get("next_recovery_at"))
    if next_at is not None and next_at > _utcnow():
        log.info(
            "nginx_recovery_backoff",
            node=str(node.id),
            attempts=int(state.get("recovery_attempts") or 0),
        )
        return RECONCILE_DEFERRED
    if await operation_service.has_live_operation(
        db, node_id=node.id, op_type=OperationType.NGINX_APPLY
    ):
        return RECONCILE_APPLY_IN_FLIGHT
    try:
        operation = await enqueue_apply(db, node=node, reason="sweep_drift_recovery")
    except Conflict as exc:
        state["reconcile_error"] = exc.message[:200]
        node.proxy_state = state
        await db.flush()
        log.info("nginx_reconcile_deferred", node=str(node.id), code=exc.code)
        return RECONCILE_DEFERRED
    if operation is None:
        return RECONCILE_NO_CHANGE

    state = dict(node.proxy_state or {})
    state["recovery_pending"] = True
    state["recovery_queued_at"] = _utcnow().isoformat()
    state["reconcile_error"] = ""
    node.proxy_state = state
    await db.flush()
    log.info(
        "nginx_recovery_queued",
        node=str(node.id),
        bundle_id=desired,
        routes=len(included),
    )
    return RECONCILE_RECOVERY_QUEUED


# --- result handling ----------------------------------------------------------


def _sanitized_error(operation: Operation) -> str:
    message = operation.error_message or ""
    if not message:
        output = operation.result or {}
        message = str(output.get("error") or output.get("reason") or "")
    if not message:
        # ``status`` is a plain String column, so a loaded row hands back a str.
        message = f"the node reported {str(operation.status).lower()}"
    return " ".join(message.split())[:480]


async def handle_operation_result(db: AsyncSession, operation: Operation) -> None:
    """Attribute a finished ``nginx.*`` operation to routes and node state.

    Called from the agent result endpoint for every operation type; non-nginx
    types return immediately. The bundle manifest is what ties a report to
    specific routes, so a route is only ever marked applied/failed if *this*
    bundle actually carried it.
    """
    if operation.type not in (
        OperationType.NGINX_APPLY,
        OperationType.NGINX_STATUS,
        OperationType.NGINX_BOOTSTRAP,
    ):
        return
    node = await db.get(Server, operation.node_id)
    if node is None:  # the node was deleted between apply and result
        return
    # ``type`` is a plain String column, so a row loaded from the DB hands back a
    # ``str``; ``==`` (StrEnum equality) is required — ``is`` silently falls
    # through to the bootstrap branch for every apply.
    if operation.type == OperationType.NGINX_APPLY:
        await _handle_apply_result(db, node=node, operation=operation)
    elif operation.type == OperationType.NGINX_STATUS:
        await _handle_status_result(db, node=node, operation=operation)
    else:
        await _handle_bootstrap_result(db, node=node, operation=operation)


async def _routes_for_manifest(db: AsyncSession, manifest: list[str]) -> list[Route]:
    ids: list[uuid.UUID] = []
    for raw in manifest:
        try:
            ids.append(uuid.UUID(str(raw)))
        except (ValueError, TypeError):
            continue
    if not ids:
        return []
    rows = (await db.execute(select(Route).where(Route.id.in_(ids)))).scalars().all()
    return list(rows)


def _apply_outcome(operation: Operation) -> ProxyApplyOutcome:
    output = operation.result or {}
    raw = str(output.get("outcome") or "")
    try:
        return ProxyApplyOutcome(raw)
    except ValueError:
        return ProxyApplyOutcome.APPLIED if operation.ok else ProxyApplyOutcome.FAILED


def _string_list(value: Any) -> list[str] | None:
    """The stringified ids in *value*, or ``None`` when it is not a list at all.

    ``None`` and ``[]`` are deliberately different answers: a report that carried
    an empty manifest says the apply produced no routes, while one that carried no
    manifest at all says nothing and must be filled in from the operation params.
    """
    if not isinstance(value, list):
        return None
    return [str(item) for item in value]


async def _handle_apply_result(db: AsyncSession, *, node: Server, operation: Operation) -> None:
    output = operation.result or {}
    bundle_id = str(output.get("bundle_id") or "")[:64] or None
    reported = _string_list(output.get("manifest"))
    if reported is None:
        # Older/partial reports fall back to the operation's own params, which the
        # control plane wrote — not to whatever the agent felt like sending.
        params = operation.params or {}
        bundle = params.get("bundle")
        manifest = _string_list(bundle.get("manifest") if isinstance(bundle, dict) else None) or []
    else:
        manifest = reported
    routes = await _routes_for_manifest(db, manifest)

    # The agent's own ``outcome`` carries more than ok/not-ok: a failed apply that
    # restored the previous tree (``rolled_back``) is materially different from
    # one that could not (``rollback_failed``), and the routes' state must say
    # which happened. Only a report with no usable outcome falls back to the
    # ok flag.
    outcome = _apply_outcome(operation)
    if outcome not in (
        ProxyApplyOutcome.APPLIED,
        ProxyApplyOutcome.ROLLED_BACK,
        ProxyApplyOutcome.ROLLBACK_FAILED,
    ):
        outcome = ProxyApplyOutcome.FAILED

    detail = "" if outcome is ProxyApplyOutcome.APPLIED else _sanitized_error(operation)
    state = dict(node.proxy_state or {})
    now = _utcnow()
    # Whether the reconciler queued this apply: only then is an applied bundle a
    # *recovery* worth announcing as one.
    was_recovery = bool(state.get("recovery_pending"))
    attempts = int(state.get("recovery_attempts") or 0)

    if outcome is ProxyApplyOutcome.APPLIED:
        for route in routes:
            route.config_state = RouteConfigState.IN_SYNC
            route.last_applied_at = now
            route.last_bundle_id = bundle_id
            route.last_apply_error = ""
            # Served again: whatever removal episode this route was in is over, so
            # a later loss starts a fresh one rather than inheriting a stale
            # confirmation.
            route.removal_requested_at = None
            route.removal_confirmed_at = None
        state["applied_bundle_id"] = bundle_id
        state["live_bundle_id"] = bundle_id
        state["last_applied_at"] = now.isoformat()
        state["last_apply_outcome"] = outcome.value
        state["last_apply_error"] = ""
        state["drift"] = False
        state["drift_since"] = None
        # Converged: the retry budget resets, so the *next* failure starts its
        # backoff from the beginning rather than inheriting an old one.
        state["recovery_pending"] = False
        state["recovery_attempts"] = 0
        state["next_recovery_at"] = None
        state["reconcile_error"] = ""
    elif outcome is ProxyApplyOutcome.ROLLED_BACK:
        # The previous configuration is live again. The bundle manifest is the
        # full *desired* tree, so it names routes that were already serving from
        # the restored bundle as well as the new one that failed: only the latter
        # become STALE. A route still confirmed at the bundle that is live now
        # keeps its IN_SYNC state.
        live = str(state.get("live_bundle_id") or "")
        for route in routes:
            if live and route.last_bundle_id == live:
                # The bundle this route was confirmed against is live again.
                route.config_state = RouteConfigState.IN_SYNC
                route.last_apply_error = ""
                continue
            route.config_state = RouteConfigState.STALE
            route.last_apply_error = detail or "the new configuration was rolled back"
        state["last_apply_outcome"] = outcome.value
        state["last_apply_error"] = detail  # keep applied_bundle_id: unchanged live tree
    else:
        # failed and rollback_failed both leave the new bundle unapplied. A failed
        # rollback additionally means the live tree may no longer match what the
        # control plane believes — reported as a terminal, visible state rather
        # than silence.
        for route in routes:
            route.config_state = RouteConfigState.FAILED
            route.last_apply_error = detail or "the configuration was not applied"
        state["last_apply_outcome"] = outcome.value
        state["last_apply_error"] = detail
        if outcome is ProxyApplyOutcome.ROLLBACK_FAILED:
            state["drift"] = True
    if outcome is not ProxyApplyOutcome.APPLIED:
        # The node is still on its previous configuration, so whatever difference
        # triggered this apply is still outstanding. Count the attempt and push the
        # next automatic one out: a node that fails every apply must not be
        # retried on every sweep tick. ``recovery_pending`` deliberately stays set,
        # so the apply that finally succeeds is still reported as the recovery.
        state["recovery_attempts"] = attempts + 1
        state["next_recovery_at"] = (now + recovery_backoff(attempts + 1)).isoformat()
    node.proxy_state = state
    await db.flush()

    for route in routes:
        await audit_service.record(
            db,
            None,
            action=(
                "route.applied"
                if outcome is ProxyApplyOutcome.APPLIED
                else "route.rolled_back"
                if outcome is ProxyApplyOutcome.ROLLED_BACK
                else "route.rollback_failed"
                if outcome is ProxyApplyOutcome.ROLLBACK_FAILED
                else "route.apply_failed"
            ),
            resource_type="route",
            resource_id=route.id,
            org_id=node.org_id,
            actor_email=f"agent:{node.name}",
            metadata={"bundle_id": bundle_id, "outcome": outcome.value, "error": detail[:200]},
        )
        await event_bus.publish(
            db,
            type=(
                "ROUTE_APPLIED" if outcome is ProxyApplyOutcome.APPLIED else "ROUTE_APPLY_FAILED"
            ),
            level=EventLevel.INFO if outcome is ProxyApplyOutcome.APPLIED else EventLevel.WARNING,
            org_id=node.org_id,
            message=(
                f"Route {route.hostname}{route.path} applied on {node.name}"
                if outcome is ProxyApplyOutcome.APPLIED
                else f"Route {route.hostname}{route.path} was not applied on {node.name}"
            ),
            resource_type="route",
            resource_id=str(route.id),
            data={"hostname": route.hostname, "path": route.path, "outcome": outcome.value},
        )

    # Removals this applied bundle proves, reported only now: the routes above are
    # the ones the node is serving, and these are the ones it just stopped serving.
    # Nothing here runs for a failed or rolled-back apply, which is the whole point
    # — an offline or failing node cannot produce this list.
    confirmed_removals: list[Route] = []
    if outcome is ProxyApplyOutcome.APPLIED:
        confirmed_removals = await _confirm_pending_removals(
            db, node=node, applied=manifest, now=now
        )
    for route in confirmed_removals:
        await audit_service.record(
            db,
            None,
            action="route.removal_confirmed",
            resource_type="route",
            resource_id=route.id,
            org_id=node.org_id,
            actor_email=f"agent:{node.name}",
            metadata={"bundle_id": bundle_id, "hostname": route.hostname, "path": route.path},
        )
        await event_bus.publish(
            db,
            type="ROUTE_REMOVAL_CONFIRMED",
            level=EventLevel.INFO,
            org_id=node.org_id,
            message=(f"Route {route.hostname}{route.path}: {removal_confirmed_detail(node.name)}"),
            resource_type="route",
            resource_id=str(route.id),
            data={"hostname": route.hostname, "path": route.path, "bundle_id": bundle_id},
        )

    if was_recovery and outcome is ProxyApplyOutcome.APPLIED:
        # Announced from the *outcome*, never from the attempt: the difference is
        # only repaired once a node has actually applied the bundle. A queued or
        # merely attempted apply publishes nothing here.
        await event_bus.publish(
            db,
            type="NGINX_DRIFT_RECOVERED",
            level=EventLevel.INFO,
            org_id=node.org_id,
            message=f"{node.name} was re-applied and now matches the desired configuration",
            resource_type="node",
            resource_id=str(node.id),
            data={"bundle_id": bundle_id, "routes": len(routes)},
        )
        await audit_service.record(
            db,
            None,
            action="nginx.drift_recovered",
            resource_type="node",
            resource_id=node.id,
            org_id=node.org_id,
            actor_email=f"agent:{node.name}",
            metadata={"bundle_id": bundle_id},
        )

    if outcome is ProxyApplyOutcome.ROLLBACK_FAILED:
        from app.models import Alert
        from app.models.enums import AlertSeverity

        db.add(
            Alert(
                org_id=node.org_id,
                severity=AlertSeverity.CRITICAL,
                title=f"Nginx rollback failed on {node.name}",
                body=(
                    "The new configuration failed to apply and the previous configuration "
                    "could not be restored. Routes on this node may be unavailable."
                ),
                event_type="ROUTE_APPLY_FAILED",
                source="proxy",
                resource_type="node",
                resource_id=str(node.id),
            )
        )
        await db.flush()


async def _handle_status_result(db: AsyncSession, *, node: Server, operation: Operation) -> None:
    """Record what the node says it has live, and detect drift."""
    state = dict(node.proxy_state or {})
    output = operation.result or {}
    now = _utcnow()
    state["last_status_at"] = now.isoformat()
    if not operation.ok:
        state["last_status_error"] = _sanitized_error(operation)
        node.proxy_state = state
        await db.flush()
        return
    state["last_status_error"] = ""
    live = str(output.get("live_bundle_id") or output.get("bundle_id") or "")[:64]
    state["live_bundle_id"] = live or None
    if isinstance(output.get("nginx_version"), str):
        state["nginx_version"] = output["nginx_version"][:64]
    if isinstance(output.get("config_test_ok"), bool):
        state["config_test_ok"] = output["config_test_ok"]

    expected = None
    try:
        expected = await expected_bundle_id(db, node=node)
    except Conflict as exc:
        state["last_status_error"] = exc.message[:200]
    drift = bool(expected) and (live or None) != expected
    state["drift"] = drift
    # When the difference was first seen. Reported by the status read model so a
    # long-standing divergence is distinguishable from one that just appeared.
    state["drift_since"] = (state.get("drift_since") or now.isoformat()) if drift else None
    node.proxy_state = state
    await db.flush()
    if not drift:
        return

    routes = (
        (await db.execute(select(Route).where(Route.node_id == node.id, Route.enabled.is_(True))))
        .scalars()
        .all()
    )
    for route in routes:
        if route.config_state != RouteConfigState.STALE:
            route.config_state = RouteConfigState.STALE
            route.last_apply_error = (
                "configuration drift: the live bundle does not match the desired one"
            )
    await db.flush()
    # The difference is recorded here and repaired by the reconciler
    # (:func:`reconcile_node`), which owns the retry bounds and the apply queue.
    # Asking for another fingerprint from this path would leave the node exactly
    # as it is — that is the loop this separation exists to prevent.
    await event_bus.publish(
        db,
        type="NGINX_DRIFT_DETECTED",
        level=EventLevel.WARNING,
        org_id=node.org_id,
        message=f"Configuration drift detected on {node.name}",
        resource_type="node",
        resource_id=str(node.id),
        data={"expected": expected, "live": live or None, "routes": len(routes)},
    )
    await audit_service.record(
        db,
        None,
        action="nginx.drift_detected",
        resource_type="node",
        resource_id=node.id,
        org_id=node.org_id,
        actor_email=f"agent:{node.name}",
        metadata={"expected_bundle_id": expected, "live_bundle_id": live or None},
    )


async def _handle_bootstrap_result(db: AsyncSession, *, node: Server, operation: Operation) -> None:
    """Record a bootstrap outcome. Bootstrap never carries configuration text."""
    state = dict(node.proxy_state or {})
    if operation.ok:
        state["bootstrapped_at"] = _utcnow().isoformat()
        state["bootstrap_error"] = ""
        action = "nginx.bootstrap_completed"
    else:
        state["bootstrap_error"] = _sanitized_error(operation)
        action = "nginx.bootstrap_failed"
    node.proxy_state = state
    await db.flush()
    await audit_service.record(
        db,
        None,
        action=action,
        resource_type="node",
        resource_id=node.id,
        org_id=node.org_id,
        actor_email=f"agent:{node.name}",
        metadata={"error": state.get("bootstrap_error", "")[:200]},
    )


# --- node proxy status --------------------------------------------------------


async def node_proxy_status(db: AsyncSession, *, node: Server) -> NodeProxyStatusOut:
    """The bounded proxy view for one node: capability, drift, route states."""
    state = node.proxy_state or {}
    capability = capability_out(node)
    problem = eligibility_error(node)
    counts = (
        await db.execute(
            select(
                func.count().label("total"),
                func.count().filter(Route.enabled.is_(True)).label("enabled"),
                func.count()
                .filter(Route.config_state == RouteConfigState.IN_SYNC)
                .label("in_sync"),
                func.count().filter(Route.config_state == RouteConfigState.STALE).label("stale"),
                func.count().filter(Route.config_state == RouteConfigState.FAILED).label("failed"),
                func.count()
                .filter(
                    Route.enabled.is_(True),
                    Route.removal_requested_at.is_not(None),
                    Route.removal_confirmed_at.is_(None),
                )
                .label("removal_pending"),
                func.max(Route.last_applied_at).label("last_applied"),
            ).where(Route.node_id == node.id)
        )
    ).one()

    expected = None
    try:
        expected = await expected_bundle_id(db, node=node)
    except Conflict:
        expected = state.get("expected_bundle_id")

    live = state.get("live_bundle_id")
    drift: bool | None = None
    if expected is not None:
        drift = (live or None) != expected
    elif state.get("drift") is not None:
        drift = bool(state.get("drift"))

    return NodeProxyStatusOut(
        id=node.id,
        created_at=node.created_at,
        updated_at=node.updated_at,
        node_id=node.id,
        node_name=node.name,
        provider=provider().name,
        capability=capability,
        eligible=problem is None,
        ineligible_reason=problem[1] if problem else "",
        expected_bundle_id=expected,
        live_bundle_id=live if isinstance(live, str) else None,
        drift=drift,
        last_status_at=_parse_dt(state.get("last_status_at")),
        last_status_error=str(state.get("last_status_error") or "")[:200],
        route_total=int(counts.total or 0),
        route_enabled=int(counts.enabled or 0),
        route_in_sync=int(counts.in_sync or 0),
        route_stale=int(counts.stale or 0),
        route_failed=int(counts.failed or 0),
        route_removal_pending=int(counts.removal_pending or 0),
        last_applied_at=counts.last_applied,
        last_apply_error=str(state.get("last_apply_error") or "")[:200],
    )


def _parse_dt(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        value = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def get_route_or_404(db: AsyncSession, route_id: uuid.UUID) -> Route:
    route = await db.get(Route, route_id)
    if route is None:
        raise NotFound("Route not found", code="ROUTE_NOT_FOUND")
    return route


__all__ = [
    "CAPABILITY_STALE_AFTER",
    "RECOVERY_BACKOFF_MAX",
    "RECOVERY_BACKOFF_START",
    "RESERVED_HOST_PORTS",
    "STATUS_REFRESH_AFTER",
    "after_hello",
    "capability_of",
    "capability_out",
    "container_out",
    "eligibility_error",
    "enqueue_apply",
    "enqueue_bootstrap",
    "expected_bundle_id",
    "get_route_or_404",
    "handle_operation_result",
    "mark_removal_requested",
    "node_proxy_status",
    "provider",
    "reconcile_node",
    "recovery_backoff",
    "removal_confirmed_detail",
    "removal_requested_detail",
    "render_for_node",
    "request_status",
    "require_eligible",
    "upstream_host_for",
    "usable_upstream_ports",
    "usable_upstreams",
]
