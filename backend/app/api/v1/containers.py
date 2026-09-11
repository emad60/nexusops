"""Container API: listing/detail, lifecycle actions, removal, logs, streaming.

Permissions (from the platform RBAC registry):
  * reads & logs          -> ``container.read`` / ``container.logs``
  * lifecycle actions     -> ``container.lifecycle``
  * destructive removal   -> ``container.remove``
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import suppress
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

import orjson
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, literal, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, DbSessionDep, require_permission
from app.core.channels import container_log_channel
from app.core.db import get_sessionmaker
from app.core.errors import BadRequest, NotFound
from app.core.logging import get_logger
from app.core.pagination import (
    CursorPage,
    CursorParams,
    Page,
    PageParams,
    cursor_params,
    decode_cursor,
    encode_cursor,
    page_params,
    paginate,
)
from app.core.redis_client import get_redis
from app.models import Container, DockerHost, LogEntry, Server
from app.models.enums import ContainerHealth, ContainerStatus, LogLevel
from app.providers.base import LogLine
from app.schemas.container import (
    ContainerDetailOut,
    ContainerOut,
    ContainerRemoveOut,
    LogEntryOut,
    host_ref,
    server_ref,
)
from app.services import container_service, docker_host_service

log = get_logger("nexusops.containers.api")

router = APIRouter(prefix="/containers", tags=["containers"])

_ReadPerm = Annotated[AuthContext, Depends(require_permission("container.read"))]
_LogsPerm = Annotated[AuthContext, Depends(require_permission("container.logs"))]
_LifecyclePerm = Annotated[AuthContext, Depends(require_permission("container.lifecycle"))]
_RemovePerm = Annotated[AuthContext, Depends(require_permission("container.remove"))]

_SORT_COLUMNS = {
    "name": Container.name,
    "status": Container.status,
    "cpu_percent": Container.cpu_percent,
    "mem_used_mb": Container.mem_used_mb,
    "observed_at": Container.observed_at,
}
_POLL_INTERVAL_S = 2.0


def _ev(value: Any) -> str:
    """String form of an enum-typed column value (str at runtime)."""
    return str(getattr(value, "value", value))


def _like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def _load_container(db: AsyncSession, container_id: UUID) -> Container:
    row = await db.get(Container, container_id)
    if row is None:
        raise NotFound("Container not found")
    return row


async def _ref_maps(
    db: AsyncSession, rows: list[Container]
) -> tuple[dict[UUID, DockerHost], dict[UUID, Server]]:
    """Batch-load host/server summaries for a page of containers."""
    host_ids = {row.docker_host_id for row in rows}
    server_ids = {row.server_id for row in rows if row.server_id is not None}
    hosts: dict[UUID, DockerHost] = {}
    servers: dict[UUID, Server] = {}
    if host_ids:
        found = await db.execute(select(DockerHost).where(DockerHost.id.in_(host_ids)))
        hosts = {h.id: h for h in found.scalars().all()}
    if server_ids:
        server_rows = await db.execute(select(Server).where(Server.id.in_(server_ids)))
        servers = {s.id: s for s in server_rows.scalars().all()}
    return hosts, servers


def _container_out(
    row: Container,
    hosts: dict[UUID, DockerHost],
    servers: dict[UUID, Server],
    *,
    detail: bool = False,
) -> ContainerOut | ContainerDetailOut:
    """Serialize one row; env values never leave the database (keys only)."""
    host = hosts.get(row.docker_host_id)
    server = servers.get(row.server_id) if row.server_id is not None else None
    data: dict[str, Any] = {
        "id": row.id,
        "container_id": row.container_id,
        "name": row.name,
        "image_ref": row.image_ref,
        "status": _ev(row.status),
        "health": _ev(row.health),
        "env_keys": list(row.env_keys or []),
        "labels": dict(row.labels or {}),
        "ports": list(row.ports or []),
        "restart_count": int(row.restart_count or 0),
        "cpu_percent": row.cpu_percent,
        "mem_used_mb": row.mem_used_mb,
        "mem_limit_mb": row.mem_limit_mb,
        "net_rx_kb_s": row.net_rx_kb_s,
        "net_tx_kb_s": row.net_tx_kb_s,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "observed_at": row.observed_at,
        "simulated": bool(row.simulated),
        "host": host_ref(host.id, host.name, _ev(host.status)) if host else None,
        "server": server_ref(server.id, server.name, _ev(server.status)) if server else None,
    }
    if detail:
        return ContainerDetailOut(**data, command=row.command, mounts=list(row.mounts or []))
    return ContainerOut(**data)


@router.get("", response_model=Page[ContainerOut], summary="List containers")
async def list_containers(
    db: DbSessionDep,
    _: _ReadPerm,
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: Annotated[str | None, Query(alias="status", max_length=120)] = None,
    health: Annotated[str | None, Query(max_length=16)] = None,
    host_id: UUID | None = Query(None),
    server_id: UUID | None = Query(None),
    q: Annotated[str | None, Query(max_length=120)] = None,
    sort: Annotated[str, Query()] = "observed_at",
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> Page[ContainerOut]:
    """Offset-paginated listing with filters and a whitelisted sort key."""
    stmt = select(Container)

    if status_filter:
        values: list[ContainerStatus] = []
        for part in status_filter.split(","):
            raw = part.strip().upper()
            if not raw:
                continue
            try:
                values.append(ContainerStatus(raw))
            except ValueError as exc:
                raise BadRequest(
                    f"Unknown container status: {part.strip()}", code="INVALID_FILTER"
                ) from exc
        if values:
            stmt = stmt.where(Container.status.in_(values))

    if health:
        try:
            stmt = stmt.where(Container.health == ContainerHealth(health.upper()))
        except ValueError as exc:
            raise BadRequest(f"Unknown health value: {health}", code="INVALID_FILTER") from exc

    if host_id is not None:
        stmt = stmt.where(Container.docker_host_id == host_id)
    if server_id is not None:
        stmt = stmt.where(Container.server_id == server_id)
    if q:
        pattern = _like_pattern(q)
        stmt = stmt.where(or_(Container.name.ilike(pattern), Container.image_ref.ilike(pattern)))

    column = _SORT_COLUMNS.get(sort)
    if column is None:
        allowed = ", ".join(sorted(_SORT_COLUMNS))
        raise BadRequest(f"sort must be one of: {allowed}", code="INVALID_SORT")
    ordered = column.desc().nullslast() if order == "desc" else column.asc().nullslast()
    stmt = stmt.order_by(ordered, Container.id.asc())

    rows, total = await paginate(db, stmt, params)
    hosts, servers = await _ref_maps(db, rows)
    return Page[ContainerOut](
        items=[_container_out(row, hosts, servers) for row in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/{container_id}", response_model=ContainerDetailOut, summary="Inspect a container")
async def get_container(
    db: DbSessionDep, _: _ReadPerm, container_id: UUID
) -> ContainerOut | ContainerDetailOut:
    """Full detail view including command line and mount table."""
    row = await _load_container(db, container_id)
    hosts, servers = await _ref_maps(db, [row])
    return _container_out(row, hosts, servers, detail=True)


async def _perform_action(
    db: AsyncSession,
    ctx: AuthContext,
    container_id: UUID,
    action: str,
    request: Request,
) -> ContainerOut:
    """Shared flow behind the five lifecycle action routes."""
    row = await _load_container(db, container_id)
    host = await docker_host_service.get_host(db, row.docker_host_id)
    updated = await container_service.trigger_action(
        db, container=row, host=host, action=action, ctx=ctx, request=request
    )
    hosts, servers = await _ref_maps(db, [updated])
    out = _container_out(updated, hosts, servers)
    assert isinstance(out, ContainerOut)
    return out


_ACTIONS: tuple[str, ...] = ("start", "stop", "restart", "pause", "unpause")


def _action_route(action: str) -> Callable[..., Coroutine[Any, Any, ContainerOut]]:
    async def _endpoint(
        db: DbSessionDep,
        ctx: _LifecyclePerm,
        container_id: UUID,
        request: Request,
    ) -> ContainerOut:
        return await _perform_action(db, ctx, container_id, action, request)

    _endpoint.__name__ = f"{action}_container"
    _endpoint.__doc__ = f"Run '{action}' on a container and return its updated state."
    return _endpoint


for _action in _ACTIONS:
    router.post(
        "/{container_id}/" + _action,
        response_model=ContainerOut,
        summary=f"{_action.capitalize()} a container",
    )(_action_route(_action))


@router.delete("/{container_id}", response_model=ContainerRemoveOut, summary="Remove a container")
async def remove_container_endpoint(
    db: DbSessionDep,
    ctx: _RemovePerm,
    container_id: UUID,
    request: Request,
    confirm: Annotated[
        str,
        Query(
            min_length=1, max_length=200, description="Exact container name; confirms destruction"
        ),
    ],
) -> ContainerRemoveOut:
    """Destructive removal gated by exact-name confirmation."""
    row = await _load_container(db, container_id)
    host = await docker_host_service.get_host(db, row.docker_host_id)
    await container_service.remove_container(
        db, container=row, host=host, confirm_name=confirm, ctx=ctx, request=request
    )
    return ContainerRemoveOut(id=container_id, removed=True)


@router.get(
    "/{container_id}/logs",
    response_model=CursorPage[LogEntryOut],
    summary="Historical container logs",
)
async def list_container_logs(
    db: DbSessionDep,
    _: _LogsPerm,
    container_id: UUID,
    params: Annotated[CursorParams, Depends(cursor_params)],
    level: Annotated[str | None, Query(max_length=8)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> CursorPage[LogEntryOut]:
    """Keyset-paginated log rows ordered newest-first (ts DESC, id DESC)."""
    await _load_container(db, container_id)

    cursor = decode_cursor(params.cursor)
    if params.cursor and cursor is None:
        raise BadRequest("Malformed cursor", code="INVALID_CURSOR")

    stmt = select(LogEntry).where(LogEntry.container_id == container_id)
    if level:
        try:
            stmt = stmt.where(LogEntry.level == LogLevel(level.upper()))
        except ValueError as exc:
            raise BadRequest(f"Unknown log level: {level}", code="INVALID_FILTER") from exc
    if q:
        stmt = stmt.where(LogEntry.message.ilike(_like_pattern(q), escape="\\"))
    if cursor is not None:
        # literal() produces the same bind params the plain-value coercion does.
        stmt = stmt.where(
            tuple_(LogEntry.ts, LogEntry.id) < tuple_(literal(cursor.ts), literal(cursor.id))
        )

    stmt = stmt.order_by(LogEntry.ts.desc(), LogEntry.id.desc()).limit(params.limit + 1)
    rows = list((await db.execute(stmt)).scalars().all())

    has_more = len(rows) > params.limit
    page_rows = rows[: params.limit]
    next_cursor = (
        encode_cursor(page_rows[-1].ts, page_rows[-1].id) if has_more and page_rows else None
    )
    return CursorPage[LogEntryOut](
        items=[
            LogEntryOut(
                id=row.id,
                ts=row.ts,
                stream=row.stream,
                level=_ev(row.level),
                message=row.message,
            )
            for row in page_rows
        ],
        next_cursor=next_cursor,
        has_more=has_more,
    )


# --- live streaming contract --------------------------------------------------


def _decode_frame(raw: Any) -> LogLine | None:
    """Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine."""
    try:
        payload = orjson.loads(raw)
        ts_raw = payload.get("ts")
        ts = datetime.fromisoformat(str(ts_raw)) if ts_raw else datetime.now(UTC)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return LogLine(
            ts=ts,
            stream=str(payload.get("stream") or "stdout")[:8],
            message=str(payload.get("message") or ""),
        )
    except Exception:  # malformed frames are skipped, never fatal
        return None


async def _max_log_id(container_id: UUID) -> int:
    """Highest persisted log id for a container (poll fallback watermark)."""
    async with get_sessionmaker()() as session:
        current = await session.scalar(
            select(func.max(LogEntry.id)).where(LogEntry.container_id == container_id)
        )
    return int(current or 0)


async def _poll_new_lines(container_id: UUID, last_seen: dict[str, int]) -> list[LogLine]:
    """Fetch log rows persisted after ``last_seen['id']`` (poll fallback)."""
    async with get_sessionmaker()() as session:
        rows = (
            (
                await session.execute(
                    select(LogEntry)
                    .where(LogEntry.container_id == container_id, LogEntry.id > last_seen["id"])
                    .order_by(LogEntry.id.asc())
                    .limit(200)
                )
            )
            .scalars()
            .all()
        )
    lines = [LogLine(ts=row.ts, stream=row.stream or "stdout", message=row.message) for row in rows]
    if rows:
        last_seen["id"] = int(rows[-1].id)
    return lines


async def stream_container_logs(container_id: UUID) -> AsyncIterator[LogLine]:
    """Live-tail a container's logs.

    Primary source is the Redis pub/sub channel
    ``channels.container_log_channel(str(container_id))`` whose frames are JSON
    ``{ts, stream, message}``; every 2s of silence triggers a poll fallback
    that replays any :class:`LogEntry` rows missed while Redis was quiet.
    Closes the subscription cleanly on cancellation.
    """
    channel = container_log_channel(str(container_id))
    pubsub = get_redis().pubsub()
    last_seen = {"id": await _max_log_id(container_id)}
    await pubsub.subscribe(channel)
    try:
        while True:
            delivered = False
            try:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=_POLL_INTERVAL_S
                )
            except Exception as exc:  # Redis hiccup must not kill the stream
                log.warning("log_stream_pubsub_error", error=str(exc))
                await asyncio.sleep(_POLL_INTERVAL_S)
                continue
            if message and message.get("type") == "message":
                line = _decode_frame(message.get("data"))
                if line is not None:
                    delivered = True
                    yield line
            for line in await _poll_new_lines(container_id, last_seen):
                delivered = True
                yield line
            if not delivered:
                await asyncio.sleep(_POLL_INTERVAL_S)
    finally:
        with suppress(Exception):
            await pubsub.aclose()


__all__ = ["router", "stream_container_logs"]
