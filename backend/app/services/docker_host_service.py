"""Docker host management: CRUD, ping, provider-backed inventory reads.

Permission mapping note: docker hosts attach to servers, so mutating this
resource requires the ``server.*`` permissions (server.create / server.update /
server.delete); reads use ``container.read``.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.logging import get_logger
from app.core.pagination import PageParams, paginate
from app.core.ssrf import assert_safe_tcp_endpoint
from app.models import Container, DockerHost, Server
from app.models.enums import AuditResult, DockerHostStatus, EventLevel
from app.providers.base import DockerProviderError
from app.providers.docker_factory import describe_provider_error, provider_for
from app.schemas.docker_host import (
    DockerHostCreate,
    DockerHostPingOut,
    DockerHostUpdate,
)
from app.services import audit_service, event_bus

log = get_logger("nexusops.docker_hosts")


async def _require_server(db: AsyncSession, server_id: uuid.UUID) -> None:
    if await db.get(Server, server_id) is None:
        raise NotFound("Referenced server does not exist", code="SERVER_NOT_FOUND")


async def _assert_name_free(db: AsyncSession, name: str, *, exclude: uuid.UUID | None) -> None:
    stmt = select(func.count()).select_from(DockerHost).where(DockerHost.name == name)
    if exclude is not None:
        stmt = stmt.where(DockerHost.id != exclude)
    if int(await db.scalar(stmt) or 0) > 0:
        raise Conflict(
            f"A docker host named '{name}' already exists.",
            code="DOCKER_HOST_NAME_TAKEN",
        )


async def list_hosts(
    db: AsyncSession,
    *,
    params: PageParams,
    status_filter: str | None = None,
    q: str | None = None,
) -> tuple[list[DockerHost], int]:
    """Offset-paginated host listing with optional status/name filters."""
    stmt = select(DockerHost).order_by(DockerHost.name.asc())
    if status_filter:
        try:
            status_value = DockerHostStatus(status_filter.upper())
        except ValueError as exc:
            raise BadRequest(
                f"Unknown docker host status: {status_filter}", code="INVALID_FILTER"
            ) from exc
        stmt = stmt.where(DockerHost.status == status_value)
    if q:
        stmt = stmt.where(DockerHost.name.ilike(f"%{q}%"))
    return await paginate(db, stmt, params)


async def get_host(db: AsyncSession, host_id: uuid.UUID) -> DockerHost:
    """Load one host or raise NotFound."""
    host = await db.get(DockerHost, host_id)
    if host is None:
        raise NotFound("Docker host not found")
    return host


def endpoint_scheme(endpoint_url: str) -> str:
    """Scheme part of an endpoint URL ('' when inherited from the agent)."""
    url = endpoint_url or ""
    return url.split("://", 1)[0] if "://" in url else ""


async def _assert_endpoint_allowed(endpoint_url: str) -> None:
    """Guard ``tcp://`` endpoints against private/internal targets.

    Monitors and webhooks are SSRF-checked at create/update; a docker host
    endpoint makes the server open connections to an arbitrary host:port and
    must not skip that guard (strict mode). ``unix://`` endpoints are local
    sockets and agent-inherited endpoints have no direct target — both exempt.
    """
    if endpoint_scheme(endpoint_url) != "tcp":
        return
    # Resolution is blocking; keep it off the event loop. Raises
    # BadRequest(ENDPOINT_BLOCKED) when the target is not allowed.
    await asyncio.to_thread(assert_safe_tcp_endpoint, endpoint_url)


async def create_host(
    db: AsyncSession,
    *,
    payload: DockerHostCreate,
    ctx: AuthContext | None = None,
    request: Request | None = None,
) -> DockerHost:
    """Register a docker host; names are unique across hosts."""
    await _assert_name_free(db, payload.name, exclude=None)
    await _assert_endpoint_allowed(payload.endpoint_url)
    if payload.server_id is not None:
        await _require_server(db, payload.server_id)

    host = DockerHost(
        name=payload.name,
        endpoint_url=payload.endpoint_url,
        tls_verify=payload.tls_verify,
        server_id=payload.server_id,
        status=DockerHostStatus.UNKNOWN,
        last_error="",
    )
    db.add(host)
    await db.flush()
    await audit_service.record(
        db,
        ctx,
        action="docker.host_create",
        resource_type="docker_host",
        resource_id=host.id,
        metadata={
            "name": host.name,
            "endpoint_scheme": endpoint_scheme(host.endpoint_url),
            "server_id": str(payload.server_id) if payload.server_id else None,
        },
        request=request,
    )
    await event_bus.publish(
        db,
        type="DOCKER_HOST_CREATED",
        message=f"docker host registered: {host.name}",
        actor_id=ctx.user_id if ctx else None,
        resource_type="docker_host",
        resource_id=str(host.id),
        data={"name": host.name},
    )
    return host


async def update_host(
    db: AsyncSession,
    *,
    host: DockerHost,
    payload: DockerHostUpdate,
    ctx: AuthContext | None = None,
    request: Request | None = None,
) -> DockerHost:
    """Apply a partial update built from an ``exclude_unset`` payload."""
    changes = payload.model_dump(exclude_unset=True)

    if "name" in changes:
        await _assert_name_free(db, changes["name"], exclude=host.id)
    if "endpoint_url" in changes:
        await _assert_endpoint_allowed(changes["endpoint_url"] or "")
    if changes.get("server_id"):
        await _require_server(db, changes["server_id"])

    for field_name, value in changes.items():
        setattr(host, field_name, value)
    # Endpoint/verify changes invalidate previous health readings.
    if "endpoint_url" in changes or "tls_verify" in changes:
        host.status = DockerHostStatus.UNKNOWN
        host.last_error = ""

    await db.flush()
    await audit_service.record(
        db,
        ctx,
        action="docker.host_update",
        resource_type="docker_host",
        resource_id=host.id,
        metadata={"fields": sorted(changes)},
        request=request,
    )
    return host


async def delete_host(
    db: AsyncSession,
    *,
    host: DockerHost,
    ctx: AuthContext | None = None,
    request: Request | None = None,
) -> None:
    """Hard-delete a host; child containers/images cascade via FK."""
    container_count = int(
        await db.scalar(
            select(func.count()).select_from(Container).where(Container.docker_host_id == host.id)
        )
        or 0
    )
    host_id, host_name = host.id, host.name
    await audit_service.record(
        db,
        ctx,
        action="docker.host_delete",
        resource_type="docker_host",
        resource_id=host_id,
        metadata={"name": host_name, "containers_deleted": container_count},
        request=request,
    )
    await event_bus.publish(
        db,
        type="DOCKER_HOST_DELETED",
        level=EventLevel.WARNING,
        message=f"docker host deleted: {host_name}",
        actor_id=ctx.user_id if ctx else None,
        resource_type="docker_host",
        resource_id=str(host_id),
        data={"name": host_name, "containers_deleted": container_count},
    )
    await db.delete(host)


async def ping_host(
    db: AsyncSession,
    *,
    host: DockerHost,
    ctx: AuthContext | None = None,
    request: Request | None = None,
) -> DockerHostPingOut:
    """Probe the provider endpoint and persist reachability state."""
    now = datetime.now(UTC)

    try:
        provider = provider_for(host)
    except BadRequest as exc:
        # Agent-inherited endpoints have no direct provider to probe.
        host.last_checked_at = now
        await audit_service.record(
            db,
            ctx,
            action="docker.host_ping",
            resource_type="docker_host",
            resource_id=host.id,
            result=AuditResult.ERROR,
            metadata={"error": "UNSUPPORTED_ENDPOINT"},
            request=request,
        )
        return DockerHostPingOut(
            status="UNKNOWN",
            checked_at=now,
            latency_ms=None,
            error=str(exc.message)[:480],
        )

    started = time.perf_counter()
    try:
        reachable = bool(await asyncio.to_thread(provider.ping))
    except DockerProviderError as exc:
        error_text = describe_provider_error(exc)
        host.status = DockerHostStatus.UNAVAILABLE
        host.last_error = error_text
        host.last_checked_at = now
        await audit_service.record(
            db,
            ctx,
            action="docker.host_ping",
            resource_type="docker_host",
            resource_id=host.id,
            result=AuditResult.ERROR,
            metadata={"error": error_text},
            request=request,
        )
        return DockerHostPingOut(
            status="UNAVAILABLE", checked_at=now, latency_ms=None, error=error_text
        )

    latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
    host.status = DockerHostStatus.AVAILABLE if reachable else DockerHostStatus.UNAVAILABLE
    host.last_error = "" if reachable else "daemon did not answer ping"
    host.last_checked_at = now
    await audit_service.record(
        db,
        ctx,
        action="docker.host_ping",
        resource_type="docker_host",
        resource_id=host.id,
        metadata={"latency_ms": latency_ms},
        request=request,
    )
    return DockerHostPingOut(
        status=str(getattr(host.status, "value", host.status)),
        checked_at=now,
        latency_ms=latency_ms if reachable else None,
        error="" if reachable else "daemon did not answer ping",
    )


async def _provider_inventory(
    db: AsyncSession,
    host: DockerHost,
    op_name: str,
) -> list[dict[str, Any]]:
    """Run an inventory call; degrade gracefully on provider failure.

    Unreachable hosts are marked UNAVAILABLE and the caller responds with an
    empty list instead of a 500.
    """
    try:
        provider = provider_for(host)
        result: list[dict[str, Any]] = await asyncio.to_thread(getattr(provider, op_name))
    except DockerProviderError as exc:
        error_text = describe_provider_error(exc)
        host.status = DockerHostStatus.UNAVAILABLE
        host.last_error = error_text
        host.last_checked_at = datetime.now(UTC)
        await db.commit()
        log.warning("inventory_failed", host=str(host.id), op=op_name, error=error_text)
        return []
    return result


async def list_images(db: AsyncSession, host: DockerHost) -> list[dict[str, Any]]:
    """Images on a host; empty list when the host is unreachable."""
    return await _provider_inventory(db, host, "images")


async def list_volumes(db: AsyncSession, host: DockerHost) -> list[dict[str, Any]]:
    """Volumes on a host; empty list when the host is unreachable."""
    return await _provider_inventory(db, host, "volumes")


async def list_networks(db: AsyncSession, host: DockerHost) -> list[dict[str, Any]]:
    """Networks on a host; empty list when the host is unreachable."""
    return await _provider_inventory(db, host, "networks")
