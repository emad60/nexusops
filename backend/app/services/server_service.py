"""Server domain service: CRUD, tagging, enrollment, heartbeats, staleness.

All functions are pure-async with the session as first argument so they can be
unit-tested against any database. HTTP concerns (audit rows, request objects)
stay in the router layer; lifecycle events are published here.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
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
    AgentCredential,
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


async def rotate_agent_token(
    db: AsyncSession,
    *,
    server_id: uuid.UUID,
    ctx: AuthContext | None = None,
    grace_seconds: int | None = None,
) -> tuple[str, Server]:
    """Rotate a node's credential with a bounded dual-token grace window.

    Rotation is **not** revocation (``revoke_agent_token``): a running agent must
    survive a rotation without a reinstall. The mechanics:

    * the *new* hash becomes ``token_hash``;
    * the agent's current hash moves to ``previous_token_hash`` and stays
      accepted until ``previous_expires_at``;
    * the new raw token is stored Fernet-encrypted in
      ``pending_token_ciphertext`` so the next heartbeat authenticated with the
      **old** token can receive it (hello only happens at process start, so the
      heartbeat is the only channel a running agent keeps).
    * ``grace_seconds=0`` produces an immediate switch — the compromise path is
      still ``revoke``, but a zero grace is available for an operator who wants
      rotation semantics without a window.

    Only hashes and ciphertext are persisted; the raw value exists solely in
    this return value and the client response.
    """
    from app.core.config import get_settings
    from app.core.security import encrypt_str, generate_agent_token

    server = await get_server(db, server_id)
    raw, _prefix, token_hash = generate_agent_token()
    now = datetime.now(UTC)
    effective_grace = (
        get_settings().agent_rotation_grace_seconds if grace_seconds is None else grace_seconds
    )
    credential = await db.get(AgentCredential, server.id)
    if credential is None:
        db.add(
            AgentCredential(
                server_id=server.id,
                org_id=server.org_id,
                token_hash=token_hash,
                created_by_id=ctx.user_id if ctx is not None else None,
            )
        )
    else:
        # A rotation always starts from the agent's *current* token, even if a
        # previous rotation's grace is still open: the plaintext the agent will
        # present next is the one that becomes the fallback.
        credential.previous_token_hash = credential.token_hash
        credential.previous_expires_at = now + timedelta(seconds=effective_grace)
        credential.token_hash = token_hash
        credential.pending_token_ciphertext = encrypt_str(raw)
        credential.rotation_applied_at = None
        credential.rotated_at = now
        credential.revoked_at = None
    # Real credentials are being issued: the node is enrolled again, and a
    # previous explicit revocation is lifted by issuing a working token.
    server.agent_enrolled_at = None
    server.credential_revoked_at = None
    await db.flush()
    return raw, server


async def revoke_agent_token(
    db: AsyncSession, *, server_id: uuid.UUID, ctx: AuthContext | None = None
) -> Server:
    """Immediate kill switch: the credential stops authenticating at once.

    No grace window and no delivery — the pending rotation ciphertext is dropped
    so a stolen token cannot fetch a replacement, and both the current and
    previous hashes are cleared so any in-flight old token is dead too.
    """
    server = await get_server(db, server_id)
    now = datetime.now(UTC)
    credential = await db.get(AgentCredential, server.id)
    if credential is None:
        raise NotFound("Node has no agent credential to revoke", code="AGENT_CREDENTIAL_MISSING")
    # Both hashes are kept, not blanked: the row must still be *found* so a
    # running agent — whether it is still on the old token or already on the new
    # one — receives an explicit ``AGENT_TOKEN_REVOKED`` instead of an ambiguous
    # ``AGENT_TOKEN_UNKNOWN``, and so the node keeps reading as revoked. What
    # makes revocation immediate is the revoked_at check, which runs *before*
    # the rotation-grace path. The pending rotation ciphertext is dropped so a
    # stolen token cannot fetch a replacement during a revoke.
    credential.pending_token_ciphertext = None
    credential.rotation_applied_at = None
    credential.revoked_at = now
    server.credential_revoked_at = now
    await db.flush()
    return server


async def pending_rotation(
    db: AsyncSession, *, server: Server, authenticated_with_previous: bool
) -> Any:
    """The pending rotation to deliver, or ``None``.

    Served **only** to a request authenticated with the previous hash — never to
    one bearing the new token, and never after the agent acknowledged it. That is
    the whole delivery contract; a crash between receive and persist re-delivers
    on the next beat because the ciphertext is retained until acknowledged.
    """
    from app.core.security import decrypt_str
    from app.schemas.agent import AgentTokenRotation

    if not authenticated_with_previous:
        return None
    credential = await db.get(AgentCredential, server.id)
    if credential is None or credential.pending_token_ciphertext is None:
        return None
    if credential.rotation_applied_at is not None:
        return None
    if credential.previous_expires_at is None or credential.previous_expires_at <= datetime.now(
        UTC
    ):
        return None
    try:
        raw = decrypt_str(credential.pending_token_ciphertext)
    except ValueError:
        # A ciphertext the platform cannot decrypt is a platform problem, not a
        # reason to hand the agent something wrong: withhold and log.
        log.error("agent_rotation_decrypt_failed", server_id=str(server.id))
        return None
    return AgentTokenRotation(token=raw, grace_expires_at=credential.previous_expires_at)


async def acknowledge_rotation(db: AsyncSession, *, server: Server) -> None:
    """End the grace window after the agent confirms it persisted the new token.

    Clearing ``previous_token_hash`` makes the old credential stop working
    immediately, which is the safe direction: the agent already holds the new
    one.
    """
    credential = await db.get(AgentCredential, server.id)
    if credential is None:
        return
    credential.pending_token_ciphertext = None
    credential.previous_token_hash = None
    credential.previous_expires_at = None
    credential.rotation_applied_at = datetime.now(UTC)
    await db.flush()


def _negotiate_protocol(agent_protocol: int) -> int:
    """The wire version this node will use: the lower of the two sides."""
    from app.schemas.agent import AGENT_PROTOCOL_VERSION, MIN_SUPPORTED_AGENT_PROTOCOL

    if agent_protocol < MIN_SUPPORTED_AGENT_PROTOCOL:
        raise BadRequest(
            f"Agent protocol {agent_protocol} is below the supported floor "
            f"({MIN_SUPPORTED_AGENT_PROTOCOL}); upgrade the agent",
            code="AGENT_UPGRADE_REQUIRED",
        )
    return min(agent_protocol, AGENT_PROTOCOL_VERSION)


async def register_agent_hello(
    db: AsyncSession, *, server: Server, payload: AgentHelloIn
) -> AgentHelloOut:
    """Mark the agent enrolled and persist its static host facts.

    Capabilities are refreshed **at hello only**: they describe the host's static
    abilities (a docker socket, an nginx binary), and re-evaluating them on every
    heartbeat would turn a transient daemon hiccup into a dispatch refusal. A
    change in capability requires a hello renegotiation (a restart), which is
    deliberate. The known limitation is documented in the node/agent doc.
    """
    from app.schemas.agent import MIN_AGENT_VERSION, AgentHelloOut

    server.agent_enrolled_at = datetime.now(UTC)
    server.protocol_version = _negotiate_protocol(payload.protocol_version)
    # The agent_version was already sent by v1 and silently dropped; persist it.
    server.agent_version = payload.agent_version
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

    if payload.capabilities:
        # Replace, never merge: a capability the node stopped reporting must stop
        # being trusted, or a removed docker socket would keep receiving ops.
        server.capabilities = {
            name: report.model_dump() for name, report in payload.capabilities.items()
        }
    if payload.facts:
        # Facts land in the flexible JSONB rather than a new column per property.
        server.extra = {**(server.extra or {}), **payload.facts}
    # A node that completes a hello with a real agent token is real telemetry.
    server.simulated = False
    await db.flush()

    return AgentHelloOut(
        server_id=server.id,
        name=server.name,
        heartbeat_interval_seconds=server.heartbeat_interval_seconds,
        offline_after_seconds=server.offline_after_seconds,
        protocol_version=server.protocol_version or 1,
        min_agent_version=MIN_AGENT_VERSION,
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
    # A heartbeat from a real agent is real telemetry. Clearing the flag here
    # (as well as at hello) is what makes a node that was created as a simulation
    # seed stop reading as simulated once a real agent reports for it.
    server.simulated = False
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
        # org_id comes back so the alert below can carry the tenant explicitly:
        # under the sweep's system scope nothing stamps it automatically.
        .returning(Server.id, Server.name, Server.org_id)
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
    for offline_row in went_offline:
        transitions.append({"server_id": str(offline_row.id), "to": "OFFLINE"})
        await publish(
            db,
            type="SERVER_OFFLINE",
            level=EventLevel.WARNING,
            message=f"{offline_row.name} went offline",
            resource_type="server",
            resource_id=str(offline_row.id),
            dedup_key=f"srv-offline:{offline_row.id}:{today}",
        )
        db.add(
            Alert(
                # The sweep runs under the system scope where no ambient org
                # exists; the alert must carry the server's tenant explicitly
                # or the INSERT violates alerts.org_id NOT NULL (and a NULL
                # would hide the alert from the tenant anyway).
                org_id=offline_row.org_id,
                severity=AlertSeverity.CRITICAL,
                title=f"{offline_row.name} went offline",
                body="No heartbeat was received within the configured offline threshold.",
                event_type="SERVER_OFFLINE",
                source="server",
                resource_type="server",
                resource_id=str(offline_row.id),
            )
        )
    for online_row in came_online:
        transitions.append({"server_id": str(online_row.id), "to": "ONLINE"})
        await publish(
            db,
            type="SERVER_ONLINE",
            message=f"{online_row.name} came online",
            resource_type="server",
            resource_id=str(online_row.id),
            dedup_key=f"srv-online:{online_row.id}:{today}",
        )

    if transitions:
        log.info("server_staleness_swept", offline=len(went_offline), online=len(came_online))
    return transitions


# --- Containers ---------------------------------------------------------------


async def ensure_docker_host(db: AsyncSession, *, server: Server) -> DockerHost:
    """Return the agent-backed Docker host for a server, creating it if needed.

    The host is stamped with the **server's** organization rather than whatever
    scope happens to be active: this runs from the agent heartbeat (org scope)
    and from the maintenance sweep (system scope), and in the latter there is no
    ambient answer to copy — a row without an owner would be rejected by the
    RLS ``WITH CHECK`` anyway, but only after a confusing NOT NULL error.
    """
    host = (
        await db.execute(select(DockerHost).where(DockerHost.server_id == server.id))
    ).scalar_one_or_none()
    if host is not None:
        return host
    host = DockerHost(
        server_id=server.id,
        org_id=server.org_id,
        name=f"agent-{server.name}",
        endpoint_url=f"agent://{server.name}",
        status=DockerHostStatus.UNKNOWN,
    )
    try:
        # The savepoint is what makes the new UNIQUE(server_id) safe under a
        # race: two heartbeats (or a heartbeat and the sync sweep) can both miss
        # the row, and whoever loses adopts the winner's instead of failing the
        # whole request. add() goes inside the savepoint so the INSERT rolls back
        # on conflict rather than poisoning the session.
        async with db.begin_nested():
            db.add(host)
            await db.flush()
    except IntegrityError:
        if host in db:
            db.expunge(host)
        existing = (
            await db.execute(select(DockerHost).where(DockerHost.server_id == server.id))
        ).scalar_one_or_none()
        if existing is None:
            raise
        host = existing
    return host


def _apply_agent_entry(
    row: Container, entry: AgentContainerIn, *, server: Server, now: datetime
) -> None:
    """Write one heartbeat entry onto a container row.

    Kept complete at every call site: the fresh-row branch flushes through a
    savepoint, and a savepoint INSERT with any field still unassigned trips
    the NOT NULL constraint before the race handler can ever run.
    """
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
    # Real agent telemetry, never simulation. This used to be hard-coded True,
    # which left every agent-observed container flagged as simulated data.
    row.simulated = server.simulated
    row.server_id = server.id


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
        if row is not None:
            prior_status = row.status
            prior_restarts = row.restart_count or 0
            _apply_agent_entry(row, entry, server=server, now=now)
        else:
            prior_status, prior_restarts = None, 0
            row = Container(
                docker_host_id=host.id,
                server_id=server.id,
                org_id=server.org_id,
                container_id=entry.container_id,
                ports=[],
                env_keys=[],
                labels={},
                mounts=[],
                observed_at=now,
            )
            _apply_agent_entry(row, entry, server=server, now=now)
            try:
                # The sweep and a heartbeat can both see a brand-new container
                # in the same instant; whoever loses the unique insert adopts
                # the winner's row instead of failing the whole heartbeat.
                # add() goes INSIDE the savepoint: begin_nested() autoflushes
                # anything already pending at its start, so an object added
                # before it would INSERT outside the savepoint and poison the
                # session on conflict instead of triggering the handler.
                async with db.begin_nested():
                    db.add(row)
                    await db.flush()
            except IntegrityError:
                # The savepoint rollback expunges an object that was added
                # within it; detach explicitly if it is still attached, so
                # nothing re-runs the failed insert below.
                if row in db:
                    db.expunge(row)
                existing = await db.scalar(
                    select(Container).where(
                        Container.docker_host_id == host.id,
                        Container.container_id == entry.container_id,
                    )
                )
                if existing is None:
                    raise
                # Diff against the adopted row's real pre-race status, not
                # None — the container did not just start because two writers
                # raced.
                prior_status = existing.status
                prior_restarts = existing.restart_count or 0
                row = existing
                _apply_agent_entry(row, entry, server=server, now=now)
            by_cid[entry.container_id] = row

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
