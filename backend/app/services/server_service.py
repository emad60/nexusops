"""Server domain service: CRUD, tagging, enrollment, heartbeats, staleness.

All functions are pure-async with the session as first argument so they can be
unit-tested against any database. HTTP concerns (audit rows, request objects)
stay in the router layer; lifecycle events are published here.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import orjson
from sqlalchemy import ColumnElement, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import AuthContext
from app.core.channels import server_metrics_channel
from app.core.config import get_settings
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.logging import get_logger
from app.core.pagination import PageParams, paginate
from app.core.redis_client import get_redis
from app.models import (
    Alert,
    Container,
    DockerHost,
    MetricSnapshot,
    Server,
    ServerTag,
    SystemEvent,
    Tag,
)
from app.models.enums import (
    ActorType,
    AlertSeverity,
    ContainerHealth,
    ContainerStatus,
    DockerHostStatus,
    EventLevel,
    MetricGranularity,
    ServerStatus,
)
from app.schemas.agent import (
    AGENT_CONTAINER_CAP,
    AgentContainerIn,
    AgentHeartbeatIn,
    AgentHelloIn,
    AgentHelloOut,
)
from app.schemas.server import ServerCreate, ServerUpdate
from app.services.event_bus import publish

log = get_logger("nexusops.servers")

_SORTABLE = {
    "created_at": Server.created_at,
    "name": Server.name,
    "status": Server.status,
    "last_heartbeat_at": Server.last_heartbeat_at,
}


def _utc_today() -> str:
    return datetime.now(UTC).date().isoformat()


def _actor_kwargs(ctx: AuthContext | None) -> dict[str, Any]:
    if ctx is None:
        return {"actor_type": ActorType.SYSTEM}
    return {"actor_id": ctx.user_id, "actor_type": ActorType.USER}


def _order_clause(sort: str | None) -> ColumnElement[Any]:
    """Translate ``name`` / ``-created_at`` style sort keys to ORDER BY."""
    raw = (sort or "-created_at").strip()
    descending = raw.startswith("-")
    key = raw[1:] if descending else raw
    column = _SORTABLE.get(key)
    if column is None:
        raise BadRequest(
            f"Unsupported sort field: {key!r}. "
            f"Allowed: {', '.join(sorted(_SORTABLE))} with optional '-' prefix.",
            code="INVALID_SORT",
        )
    return column.desc() if descending else column.asc()


async def get_server(db: AsyncSession, server_id: uuid.UUID) -> Server:
    """Load one server or raise 404. docker_host is preloaded for serialization."""
    stmt = select(Server).options(selectinload(Server.docker_host)).where(Server.id == server_id)
    server = (await db.execute(stmt)).scalar_one_or_none()
    if server is None:
        raise NotFound("Server not found")
    return server


async def list_servers(
    db: AsyncSession,
    *,
    statuses: Sequence[ServerStatus] | None = None,
    environment: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    simulated: bool | None = None,
    sort: str | None = "-created_at",
    params: PageParams,
) -> tuple[list[Server], int]:
    """Filter + paginate servers. Returns ``(rows, total)``."""
    stmt = select(Server).options(selectinload(Server.docker_host))
    if statuses:
        stmt = stmt.where(Server.status.in_(list(statuses)))
    if environment:
        stmt = stmt.where(Server.environment == environment)
    if tag:
        tagged = (
            select(ServerTag.server_id).join(Tag, Tag.id == ServerTag.tag_id).where(Tag.name == tag)
        )
        stmt = stmt.where(Server.id.in_(tagged))
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Server.name.ilike(pattern),
                Server.hostname.ilike(pattern),
                Server.ip_address.ilike(pattern),
            )
        )
    if simulated is not None:
        stmt = stmt.where(Server.simulated.is_(simulated))
    stmt = stmt.order_by(_order_clause(sort))
    rows, total = await paginate(db, stmt, params)
    return rows, total


async def _resolve_tags(db: AsyncSession, names: Sequence[str]) -> list[Tag]:
    """Fetch existing tags by name and case-preservingly create missing ones."""
    wanted = [n for n in dict.fromkeys(names) if n]
    if not wanted:
        return []
    existing = list((await db.execute(select(Tag).where(Tag.name.in_(wanted)))).scalars().all())
    found = {t.name: t for t in existing}
    for name in wanted:
        if name not in found:
            tag = Tag(name=name)
            db.add(tag)
            found[name] = tag
    return [found[name] for name in wanted]


async def create_server(
    db: AsyncSession, *, payload: ServerCreate, ctx: AuthContext | None = None
) -> Server:
    """Register a server; enforces unique names and auto-creates tags."""
    duplicate = (
        await db.execute(select(Server.id).where(Server.name == payload.name))
    ).scalar_one_or_none()
    if duplicate is not None:
        raise Conflict(f"A server named {payload.name!r} already exists", code="DUPLICATE_NAME")

    server = Server(
        name=payload.name,
        hostname=payload.hostname,
        ip_address=payload.ip_address or "",
        os_name=payload.os_name,
        os_version=payload.os_version,
        arch=payload.arch,
        environment=payload.environment,
        location=payload.location,
        description=payload.description,
        heartbeat_interval_seconds=payload.heartbeat_interval_seconds,
        offline_after_seconds=payload.offline_after_seconds,
        simulated=payload.simulated,
        status=ServerStatus.UNKNOWN,
    )
    server.tags = await _resolve_tags(db, payload.tags)
    db.add(server)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise Conflict(
            f"A server named {payload.name!r} already exists", code="DUPLICATE_NAME"
        ) from exc

    await _publish_server_event(
        db,
        type="SERVER_CREATED",
        message=f"Server {server.name} registered",
        ctx=ctx,
        resource_id=server.id,
        data={"name": server.name, "environment": server.environment},
    )
    # Re-fetch so relationships (docker_host) are loaded for serialization.
    return await get_server(db, server.id)


async def update_server(
    db: AsyncSession, *, server_id: uuid.UUID, payload: ServerUpdate, ctx: AuthContext | None = None
) -> Server:
    """Apply a partial update; ``tags`` replaces the whole set when provided."""
    server = await get_server(db, server_id)
    data = payload.model_dump(exclude_unset=True)

    new_name = data.get("name")
    if new_name is not None and new_name != server.name:
        duplicate = (
            await db.execute(select(Server.id).where(Server.name == new_name))
        ).scalar_one_or_none()
        if duplicate is not None:
            raise Conflict(f"A server named {new_name!r} already exists", code="DUPLICATE_NAME")

    tags = data.pop("tags", None)
    for field, value in data.items():
        setattr(server, field, value)
    if tags is not None:
        server.tags = await _resolve_tags(db, tags)
    await db.flush()

    await _publish_server_event(
        db,
        type="SERVER_UPDATED",
        message=f"Server {server.name} updated",
        ctx=ctx,
        resource_id=server.id,
        data={"fields": sorted([*data.keys(), *(["tags"] if tags is not None else [])])},
    )
    return server


async def delete_server(
    db: AsyncSession, *, server_id: uuid.UUID, ctx: AuthContext | None = None
) -> dict[str, str]:
    """Hard-delete a server; FK cascades remove children, audit keeps history."""
    server = await get_server(db, server_id)
    snapshot = {"name": server.name, "hostname": server.hostname}
    await db.delete(server)
    await db.flush()
    await publish(
        db,
        type="SERVER_DELETED",
        message=f"Server {snapshot['name']} deleted",
        **_actor_kwargs(ctx),
        resource_type="server",
        resource_id=str(server_id),
        data=snapshot,
    )
    return snapshot


async def rotate_agent_token(db: AsyncSession, *, server_id: uuid.UUID) -> tuple[str, Server]:
    """Regenerate the enrollment token. The previous token stops working."""
    from app.core.security import generate_agent_token

    server = await get_server(db, server_id)
    raw, _prefix, token_hash = generate_agent_token()
    server.agent_token_hash = token_hash
    server.agent_enrolled_at = None
    await db.flush()
    return raw, server


async def register_agent_hello(
    db: AsyncSession, *, server: Server, payload: AgentHelloIn
) -> AgentHelloOut:
    """Mark the agent enrolled and persist its static host facts."""
    server.agent_enrolled_at = datetime.now(UTC)
    if payload.os_name:
        server.os_name = payload.os_name
    if payload.os_version:
        server.os_version = payload.os_version
    if payload.arch:
        server.arch = payload.arch
    if payload.hostname:
        server.hostname = payload.hostname
    if payload.cpu_cores:
        server.cpu_cores = payload.cpu_cores
    if payload.memory_total_mb:
        server.memory_total_mb = payload.memory_total_mb
    if payload.disk_total_gb:
        server.disk_total_gb = payload.disk_total_gb
    await db.flush()
    from app.schemas.agent import AgentHelloOut

    return AgentHelloOut(
        server_id=server.id,
        name=server.name,
        heartbeat_interval_seconds=server.heartbeat_interval_seconds,
        offline_after_seconds=server.offline_after_seconds,
    )


# --- Heartbeat & staleness ----------------------------------------------------


async def process_heartbeat(
    db: AsyncSession,
    *,
    server: Server,
    payload: AgentHeartbeatIn,
    agent_version: str = "",
) -> None:
    """Apply a heartbeat: refresh facts, store a RAW metric, mirror containers.

    Transitions the server to ONLINE (with a once-per-day deduplicated event)
    whenever the previous status differed.
    """
    now = datetime.now(UTC)
    prev_status: ServerStatus | str = server.status

    server.last_heartbeat_at = now
    if agent_version:
        server.agent_version = agent_version
    if payload.os_name:
        server.os_name = payload.os_name
    if payload.arch:
        server.arch = payload.arch
    for attr in ("cpu_cores", "memory_total_mb", "disk_total_gb"):
        value = getattr(payload, attr, None)
        if value is not None:
            setattr(server, attr, value)
    server.uptime_seconds = payload.uptime_seconds

    if prev_status != ServerStatus.ONLINE:
        server.status = ServerStatus.ONLINE
        await publish(
            db,
            type="SERVER_ONLINE",
            message=f"{server.name} came online",
            actor_type=ActorType.AGENT,
            resource_type="server",
            resource_id=str(server.id),
            dedup_key=f"srv-online:{server.id}:{_utc_today()}",
        )

    db.add(
        MetricSnapshot(
            server_id=server.id,
            granularity=MetricGranularity.RAW,
            recorded_at=now,
            cpu_percent=payload.cpu_percent,
            mem_used_mb=payload.mem_used_mb,
            mem_percent=payload.mem_percent,
            disk_used_gb=payload.disk_used_gb,
            disk_percent=payload.disk_percent,
            net_rx_kb_s=payload.net_rx_kb_s,
            net_tx_kb_s=payload.net_tx_kb_s,
            load1=payload.load1,
            uptime_seconds=payload.uptime_seconds,
        )
    )
    await _publish_live_frame(server=server, payload=payload, ts=now)
    if payload.containers:
        await upsert_containers(db, server=server, entries=payload.containers)


async def _publish_live_frame(*, server: Server, payload: AgentHeartbeatIn, ts: datetime) -> None:
    """Best-effort push of a lightweight metric frame for live dashboards."""
    frame = {
        "server_id": str(server.id),
        "ts": ts.isoformat(),
        "cpu_percent": payload.cpu_percent,
        "mem_percent": payload.mem_percent,
        "mem_used_mb": payload.mem_used_mb,
        "disk_percent": payload.disk_percent,
    }
    try:
        await get_redis().publish(
            server_metrics_channel(str(server.id)), orjson.dumps(frame).decode()
        )
    except Exception as exc:  # Redis down must never break ingestion
        log.warning("live_metric_publish_failed", server_id=str(server.id), error=str(exc))


async def mark_stale_servers(db: AsyncSession) -> list[dict[str, str]]:
    """Flip ONLINE servers past their offline threshold to OFFLINE and back.

    Uses status-guarded bulk UPDATE ... RETURNING so concurrent workers cannot
    double-transition a server. Emits SERVER_OFFLINE/SERVER_ONLINE events plus
    a CRITICAL alert row for each outage. Returns the transitions for logging.
    """
    default_after = get_settings().server_offline_after_seconds
    threshold = func.coalesce(Server.offline_after_seconds, default_after)
    grace = func.make_interval(0, 0, 0, 0, 0, 0, threshold)

    stale = await db.execute(
        update(Server)
        .where(
            Server.status == ServerStatus.ONLINE,
            Server.last_heartbeat_at.is_not(None),
            Server.last_heartbeat_at < func.now() - grace,
        )
        .values(status=ServerStatus.OFFLINE)
        .returning(Server.id, Server.name)
        .execution_options(synchronize_session=False)
    )
    went_offline = stale.all()

    recovered = await db.execute(
        update(Server)
        .where(
            Server.status == ServerStatus.OFFLINE,
            Server.last_heartbeat_at.is_not(None),
            Server.last_heartbeat_at >= func.now() - grace,
        )
        .values(status=ServerStatus.ONLINE)
        .returning(Server.id, Server.name)
        .execution_options(synchronize_session=False)
    )
    came_online = recovered.all()

    transitions: list[dict[str, str]] = []
    today = _utc_today()
    for row in went_offline:
        transitions.append({"server_id": str(row.id), "to": "OFFLINE"})
        await publish(
            db,
            type="SERVER_OFFLINE",
            level=EventLevel.WARNING,
            message=f"{row.name} went offline",
            resource_type="server",
            resource_id=str(row.id),
            dedup_key=f"srv-offline:{row.id}:{today}",
        )
        db.add(
            Alert(
                severity=AlertSeverity.CRITICAL,
                title=f"{row.name} went offline",
                body="No heartbeat was received within the configured offline threshold.",
                event_type="SERVER_OFFLINE",
                source="server",
                resource_type="server",
                resource_id=str(row.id),
            )
        )
    for row in came_online:
        transitions.append({"server_id": str(row.id), "to": "ONLINE"})
        await publish(
            db,
            type="SERVER_ONLINE",
            message=f"{row.name} came online",
            resource_type="server",
            resource_id=str(row.id),
            dedup_key=f"srv-online:{row.id}:{today}",
        )

    if transitions:
        log.info("server_staleness_swept", offline=len(went_offline), online=len(came_online))
    return transitions


# --- Containers ---------------------------------------------------------------


async def ensure_docker_host(db: AsyncSession, *, server: Server) -> DockerHost:
    """Return the agent-backed Docker host for a server, creating it if needed."""
    host = (
        await db.execute(select(DockerHost).where(DockerHost.server_id == server.id))
    ).scalar_one_or_none()
    if host is not None:
        return host
    host = DockerHost(
        server_id=server.id,
        name=f"agent-{server.name}",
        endpoint_url=f"agent://{server.name}",
        status=DockerHostStatus.UNKNOWN,
    )
    db.add(host)
    await db.flush()
    return host


async def upsert_containers(
    db: AsyncSession, *, server: Server, entries: Sequence[AgentContainerIn]
) -> None:
    """Mirror observed container state, diffing RUNNING transitions into events."""
    host = await ensure_docker_host(db, server=server)
    ids = [entry.container_id for entry in entries]
    rows = list(
        (
            await db.execute(
                select(Container).where(
                    Container.docker_host_id == host.id,
                    Container.container_id.in_(ids),
                )
            )
        )
        .scalars()
        .all()
    )
    by_cid = {row.container_id: row for row in rows}
    now = datetime.now(UTC)
    pending_events: list[tuple[str, Container, str, EventLevel]] = []

    for entry in entries:
        row = by_cid.get(entry.container_id)
        prior_status = row.status if row is not None else None
        prior_restarts = row.restart_count if row is not None else 0
        if row is None:
            row = Container(
                docker_host_id=host.id,
                server_id=server.id,
                container_id=entry.container_id,
                ports=[],
                env_keys=[],
                labels={},
                mounts=[],
                observed_at=now,
            )
            db.add(row)
            by_cid[entry.container_id] = row

        row.name = entry.name
        row.image_ref = entry.image_ref
        row.status = entry.status
        row.health = entry.health or ContainerHealth.NONE
        row.restart_count = entry.restart_count
        if entry.cpu_percent is not None:
            row.cpu_percent = entry.cpu_percent
        if entry.mem_used_mb is not None:
            row.mem_used_mb = entry.mem_used_mb
        if entry.mem_limit_mb is not None:
            row.mem_limit_mb = entry.mem_limit_mb
        row.observed_at = now
        row.simulated = True
        row.server_id = server.id

        cid = row.container_id
        if entry.status == ContainerStatus.RUNNING and prior_status != ContainerStatus.RUNNING:
            pending_events.append(("CONTAINER_STARTED", row, cid, EventLevel.INFO))
        elif prior_status == ContainerStatus.RUNNING and entry.status != ContainerStatus.RUNNING:
            pending_events.append(("CONTAINER_STOPPED", row, cid, EventLevel.WARNING))
        elif row.restart_count > prior_restarts:
            pending_events.append(("CONTAINER_RESTARTED", row, cid, EventLevel.INFO))

    await db.flush()  # rows need PKs before events reference them
    today = _utc_today()
    prefix_for = {"CONTAINER_STARTED": "ctr-started", "CONTAINER_STOPPED": "ctr-stopped"}
    for event_type, row, cid, level in pending_events:
        key = prefix_for.get(event_type, f"ctr-{event_type.split('_')[-1].lower()}")
        await publish(
            db,
            type=event_type,
            level=level,
            message=f"Container {row.name} on {server.name}: "
            f"{event_type.removeprefix('CONTAINER_').lower().replace('_', ' ')}",
            actor_type=ActorType.AGENT,
            resource_type="container",
            resource_id=str(row.id),
            data={"container_id": cid, "server_id": str(server.id)},
            dedup_key=f"{key}:{row.id}:{today}",
        )

    # Containers seen on this host before but absent from this heartbeat have
    # been removed from the daemon (docker rm, compose recreate, prune) — the
    # same reconciliation the real sync path applies. Only trust absence below
    # the agent's cap: a truncated payload says nothing about what it dropped.
    if len(entries) < AGENT_CONTAINER_CAP:
        missing = await db.execute(
            select(Container).where(
                Container.docker_host_id == host.id,
                Container.container_id.not_in(set(ids)),
            )
        )
        for row in missing.scalars().all():
            await publish(
                db,
                type="CONTAINER_REMOVED",
                level=EventLevel.WARNING,
                message=f"container disappeared: {row.name}",
                actor_type=ActorType.AGENT,
                resource_type="container",
                resource_id=str(row.id),
                data={"container_name": row.name, "server_id": str(server.id)},
                dedup_key=f"container_removed:{row.container_id}:{today}",
            )
            await db.delete(row)


# --- Reads used by detail views -------------------------------------------------


async def recent_events(
    db: AsyncSession, *, server_id: uuid.UUID, limit: int = 20
) -> Sequence[SystemEvent]:
    stmt = (
        select(SystemEvent)
        .where(SystemEvent.resource_type == "server", SystemEvent.resource_id == str(server_id))
        .order_by(SystemEvent.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def container_counts(db: AsyncSession, *, server_id: uuid.UUID) -> dict[str, int]:
    total = (
        await db.execute(
            select(func.count()).select_from(Container).where(Container.server_id == server_id)
        )
    ).scalar_one()
    running = (
        await db.execute(
            select(func.count())
            .select_from(Container)
            .where(Container.server_id == server_id, Container.status == ContainerStatus.RUNNING)
        )
    ).scalar_one()
    return {"containers_running": int(running), "containers_total": int(total)}


# --- Tags -----------------------------------------------------------------------


async def list_tags_with_usage(db: AsyncSession) -> list[tuple[Tag, int]]:
    """All tags ordered by name with their server usage counts."""
    stmt = (
        select(Tag, func.count(ServerTag.server_id))
        .outerjoin(ServerTag, ServerTag.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    return [(tag, int(count)) for tag, count in (await db.execute(stmt)).all()]


async def upsert_tag(db: AsyncSession, *, name: str, color: str) -> Tag:
    """Create a tag or update its colour; names are matched exactly."""
    tag = (await db.execute(select(Tag).where(Tag.name == name))).scalar_one_or_none()
    if tag is None:
        tag = Tag(name=name, color=color)
        db.add(tag)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            tag = (await db.execute(select(Tag).where(Tag.name == name))).scalar_one()
    elif tag.color != color:
        tag.color = color
        await db.flush()
    return tag


async def tag_usage_count(db: AsyncSession, *, tag_id: uuid.UUID) -> int:
    count = (
        await db.execute(
            select(func.count()).select_from(ServerTag).where(ServerTag.tag_id == tag_id)
        )
    ).scalar_one()
    return int(count)


async def _publish_server_event(
    db: AsyncSession,
    *,
    type: str,
    message: str,
    ctx: AuthContext | None,
    resource_id: uuid.UUID,
    data: dict[str, Any],
) -> None:
    await publish(
        db,
        type=type,
        message=message,
        **_actor_kwargs(ctx),
        resource_type="server",
        resource_id=str(resource_id),
        data=data,
    )
