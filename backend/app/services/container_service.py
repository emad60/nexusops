"""Container lifecycle and docker-host reconciliation.

Services here are the only callers of providers: routers stay thin, workers
reuse the same entry points (``sync_host_state``, ``collect_recent_logs``).
All provider calls are offloaded to threads; provider failures never bubble
out of sweep loops.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.logging import get_logger
from app.models import Container, DockerHost
from app.models.enums import (
    AuditResult,
    ContainerHealth,
    ContainerStatus,
    DockerHostStatus,
    EventLevel,
)
from app.providers.base import (
    DockerProviderError,
    clip,
)
from app.providers.docker_factory import (
    SimulatedDockerProvider,
    describe_provider_error,
    is_simulated,
    provider_for,
)
from app.services import audit_service, event_bus, log_service

log = get_logger("nexusops.containers")

_MAX_STATS_PER_HOST = 25

#: Expected row status after each action completes successfully.
_STATUS_BY_ACTION: dict[str, str] = {
    "start": "RUNNING",
    "stop": "EXITED",
    "restart": "RUNNING",
    "pause": "PAUSED",
    "unpause": "RUNNING",
}

_EVENT_BY_ACTION: dict[str, str] = {
    "start": "CONTAINER_STARTED",
    "stop": "CONTAINER_STOPPED",
    "restart": "CONTAINER_RESTARTED",
    "pause": "CONTAINER_PAUSED",
    "unpause": "CONTAINER_UNPAUSED",
}

_ACTIONS: tuple[str, ...] = ("start", "stop", "restart", "pause", "unpause")


def _as_status(value: Any) -> ContainerStatus:
    text = str(getattr(value, "value", value) or "").upper()
    try:
        return ContainerStatus(text)
    except ValueError:
        return ContainerStatus.CREATED


def _as_health(value: Any) -> ContainerHealth:
    text = str(getattr(value, "value", value) or "").upper()
    try:
        return ContainerHealth(text)
    except ValueError:
        return ContainerHealth.NONE


def _daily_dedup(event_type: str, cid: str, now: datetime) -> str:
    return f"{event_type.lower()}:{cid}:{now:%Y%m%d}"


def _transition_event(old: ContainerStatus, new: ContainerStatus) -> str | None:
    """Map a status change onto an event type (None = not notable)."""
    if old == new:
        return None
    if new is ContainerStatus.RUNNING:
        if old is ContainerStatus.PAUSED:
            return "CONTAINER_UNPAUSED"
        return "CONTAINER_STARTED"
    if new in (ContainerStatus.EXITED, ContainerStatus.DEAD):
        return "CONTAINER_STOPPED"
    if new is ContainerStatus.PAUSED:
        return "CONTAINER_PAUSED"
    if new is ContainerStatus.RESTARTING:
        return "CONTAINER_RESTARTED"
    return None


async def _emit(
    db: AsyncSession,
    *,
    event_type: str,
    container: Container,
    now: datetime,
    level: EventLevel = EventLevel.INFO,
    message: str = "",
    dedup: bool = True,
) -> None:
    await event_bus.publish(
        db,
        type=event_type,
        level=level,
        message=message or f"{event_type.lower().replace('_', ' ')}: {container.name}",
        resource_type="container",
        resource_id=str(container.id),
        data={
            "container_name": container.name,
            "image_ref": container.image_ref,
            "docker_host_id": str(container.docker_host_id),
            "container_status": str(getattr(container.status, "value", container.status)),
        },
        dedup_key=_daily_dedup(event_type, container.container_id, now) if dedup else None,
    )


def _dispatch(provider: Any, action: str, cid: str) -> None:
    """Blocking provider call for one lifecycle action."""
    method = getattr(provider, action)
    if action in {"stop", "restart"}:
        method(cid, timeout=10)
    else:
        method(cid)


async def trigger_action(
    db: AsyncSession,
    *,
    container: Container,
    host: DockerHost,
    action: str,
    ctx: AuthContext | None = None,
    request: Request | None = None,
) -> Container:
    """Run a start/stop/restart/pause/unpause and reflect it on the row.

    Raises Conflict(DOCKER_UNAVAILABLE) with a sanitized message when the
    provider fails; the host row is marked UNAVAILABLE before raising.
    """
    if action not in _ACTIONS:
        raise BadRequest(f"Unsupported container action: {action}", code="INVALID_ACTION")

    provider = provider_for(host)
    if is_simulated(provider):
        cast(SimulatedDockerProvider, provider).register_container(container)

    try:
        await asyncio.to_thread(_dispatch, provider, action, container.container_id)
    except DockerProviderError as exc:
        error_text = describe_provider_error(exc)
        host.status = DockerHostStatus.UNAVAILABLE
        host.last_error = error_text
        host.last_checked_at = datetime.now(UTC)
        await audit_service.record(
            db,
            ctx,
            action=f"container.{action}",
            resource_type="container",
            resource_id=container.id,
            result=AuditResult.ERROR,
            metadata={"error": error_text},
            request=request,
        )
        await db.commit()
        raise Conflict(
            f"Docker host '{clip(host.name, 60)}' is unavailable; action not applied.",
            code="DOCKER_UNAVAILABLE",
        ) from exc

    now = datetime.now(UTC)
    new_status = ContainerStatus(_STATUS_BY_ACTION[action])
    container.status = new_status
    container.observed_at = now
    if action == "restart":
        container.restart_count = (container.restart_count or 0) + 1
    if new_status is ContainerStatus.RUNNING:
        container.started_at = now
        container.finished_at = None
    elif action == "stop":
        container.finished_at = now

    await audit_service.record(
        db,
        ctx,
        action=f"container.{action}",
        resource_type="container",
        resource_id=container.id,
        metadata={"name": container.name, "host": host.name},
        request=request,
    )
    await _emit(db, event_type=_EVENT_BY_ACTION[action], container=container, now=now)
    return container


async def remove_container(
    db: AsyncSession,
    *,
    container: Container,
    host: DockerHost,
    confirm_name: str,
    ctx: AuthContext | None = None,
    request: Request | None = None,
) -> None:
    """Destructive removal requiring exact-name confirmation.

    Deletes via the provider first, then hard-deletes the DB row.
    """
    if confirm_name != container.name:
        raise BadRequest(
            "confirm must exactly match the container name",
            code="CONFIRMATION_REQUIRED",
            details={"expected": container.name},
        )

    provider = provider_for(host)
    if is_simulated(provider):
        cast(SimulatedDockerProvider, provider).register_container(container)

    try:
        await asyncio.to_thread(provider.remove, container.container_id, False)
    except DockerProviderError as exc:
        error_text = describe_provider_error(exc)
        host.status = DockerHostStatus.UNAVAILABLE
        host.last_error = error_text
        host.last_checked_at = datetime.now(UTC)
        await audit_service.record(
            db,
            ctx,
            action="container.remove",
            resource_type="container",
            resource_id=container.id,
            result=AuditResult.ERROR,
            metadata={"error": error_text},
            request=request,
        )
        await db.commit()
        raise Conflict(
            "Docker host unavailable; container not removed.",
            code="DOCKER_UNAVAILABLE",
        ) from exc

    container_id = container.id
    container_cid = container.container_id
    container_name = container.name
    await audit_service.record(
        db,
        ctx,
        action="container.remove",
        resource_type="container",
        resource_id=container_id,
        metadata={"name": container_name, "host": host.name},
        request=request,
    )
    await event_bus.publish(
        db,
        type="CONTAINER_REMOVED",
        level=EventLevel.WARNING,
        message=f"container removed: {container_name}",
        resource_type="container",
        resource_id=str(container_id),
        actor_id=ctx.user_id if ctx else None,
        data={"container_name": container_name, "docker_host_id": str(host.id)},
        dedup_key=f"container_removed:{container_cid}:{datetime.now(UTC):%Y%m%d}",
    )
    await db.delete(container)


async def sync_host_state(db: AsyncSession, host_id: uuid.UUID) -> dict[str, Any]:
    """Reconcile provider state into DB rows for one host.

    Returns ``{"seen", "added", "updated", "removed", "error"?}``. Provider
    failures mark the host UNAVAILABLE and are swallowed so one dead host
    never breaks sweep loops.
    """
    host = await db.get(DockerHost, host_id)
    if host is None:
        raise NotFound("Docker host not found")

    summary: dict[str, Any] = {"seen": 0, "added": 0, "updated": 0, "removed": 0}
    now = datetime.now(UTC)

    try:
        provider = provider_for(host)
        infos = await asyncio.to_thread(provider.list_containers, True)
    except DockerProviderError as exc:
        return await _mark_host_unavailable(db, host, summary, exc)

    simulated = is_simulated(provider)
    existing = list(
        (await db.execute(select(Container).where(Container.docker_host_id == host.id)))
        .scalars()
        .all()
    )
    if simulated:
        cast(SimulatedDockerProvider, provider).register_containers(existing)
    by_cid = {row.container_id: row for row in existing}

    seen_cids: set[str] = set()
    stats_targets: list[Container] = []

    for info in infos:
        seen_cids.add(info.id)
        status = _as_status(info.status)
        health = _as_health(info.health)
        row = by_cid.get(info.id)
        if row is None:
            row = Container(
                docker_host_id=host.id,
                server_id=host.server_id,
                container_id=info.id[:72],
                name=(info.name or info.id[:12])[:200],
                image_ref=info.image_ref[:300],
                command=info.command[:500],
                status=status,
                health=health,
                ports=list(info.ports or []),
                env_keys=list(info.env_keys or [])[:100],
                labels=dict(info.labels or {}),
                mounts=list(info.mounts or []),
                restart_count=int(info.restart_count or 0),
                started_at=info.started_at,
                observed_at=now,
                simulated=simulated,
            )
            db.add(row)
            summary["added"] += 1
            by_cid[info.id] = row
            await event_bus.publish(
                db,
                type="CONTAINER_STARTED",
                message=f"container discovered: {row.name}",
                resource_type="container",
                resource_id=str(row.id),
                data={"image_ref": row.image_ref, "docker_host_id": str(host.id)},
                dedup_key=f"container_started:{info.id}:{now:%Y%m%d}",
            )
            if status is ContainerStatus.RUNNING:
                stats_targets.append(row)
            continue

        old_status = _as_status(row.status)
        changed = (
            old_status != status
            or _as_health(row.health) != health
            or row.image_ref != info.image_ref
            or row.name != info.name
        )
        row.name = (info.name or row.name)[:200]
        row.image_ref = info.image_ref[:300]
        row.command = info.command[:500]
        row.status = status
        row.health = health
        row.ports = list(info.ports or [])
        row.env_keys = list(info.env_keys or [])[:100]
        row.labels = dict(info.labels or {})
        row.mounts = list(info.mounts or [])
        row.restart_count = int(info.restart_count or row.restart_count or 0)
        row.started_at = info.started_at or row.started_at
        row.observed_at = now
        row.simulated = simulated
        if changed:
            summary["updated"] += 1
            event_type = _transition_event(old_status, status)
            if event_type is not None:
                await event_bus.publish(
                    db,
                    type=event_type,
                    message=f"{row.name}: {old_status.value} -> {status.value}",
                    resource_type="container",
                    resource_id=str(row.id),
                    data={"from": old_status.value, "to": status.value},
                    dedup_key=_daily_dedup(event_type, info.id, now),
                )
        if status is ContainerStatus.RUNNING:
            stats_targets.append(row)

    for cid, row in list(by_cid.items()):
        if cid in seen_cids:
            continue
        await event_bus.publish(
            db,
            type="CONTAINER_REMOVED",
            level=EventLevel.WARNING,
            message=f"container disappeared: {row.name}",
            resource_type="container",
            resource_id=str(row.id),
            data={"container_name": row.name, "docker_host_id": str(host.id)},
            dedup_key=f"container_removed:{cid}:{now:%Y%m%d}",
        )
        await db.delete(row)
        by_cid.pop(cid, None)
        summary["removed"] += 1

    summary["seen"] = len(infos)

    for row in stats_targets[:_MAX_STATS_PER_HOST]:
        try:
            stats = await asyncio.to_thread(provider.stats, row.container_id)
        except DockerProviderError as exc:
            log.warning("container_stats_failed", host=str(host.id), error=str(exc))
            break
        row.cpu_percent = stats.cpu_percent
        row.mem_used_mb = stats.mem_used_mb
        row.mem_limit_mb = stats.mem_limit_mb
        row.net_rx_kb_s = stats.net_rx_kb_s
        row.net_tx_kb_s = stats.net_tx_kb_s

    host.status = DockerHostStatus.AVAILABLE
    host.last_error = ""
    host.last_checked_at = datetime.now(UTC)
    await db.commit()
    return summary


async def _mark_host_unavailable(
    db: AsyncSession,
    host: DockerHost,
    summary: dict[str, Any],
    exc: DockerProviderError,
) -> dict[str, Any]:
    error_text = describe_provider_error(exc)
    host.status = DockerHostStatus.UNAVAILABLE
    host.last_error = error_text
    host.last_checked_at = datetime.now(UTC)
    await db.commit()
    summary["error"] = "DOCKER_UNAVAILABLE"
    log.warning("host_sync_failed", host=str(host.id), error=error_text)
    return summary


async def collect_recent_logs(
    db: AsyncSession,
    host: DockerHost,
    max_containers: int = 5,
    per_container: int = 100,
) -> int:
    """Pull recent logs from running containers of a real host.

    Simulated hosts are skipped — their logs are produced directly by the
    simulator's generator, so replaying rows here would duplicate them.
    Per-container errors are swallowed with a warning. Returns lines stored.
    """
    provider = provider_for(host)
    if is_simulated(provider):
        return 0

    running_rows = list(
        (
            await db.execute(
                select(Container)
                .where(
                    Container.docker_host_id == host.id,
                    Container.status == ContainerStatus.RUNNING,
                )
                .order_by(Container.name.asc())
                .limit(max_containers)
            )
        )
        .scalars()
        .all()
    )

    total = 0
    for row in running_rows:
        try:

            def _read(target: Container = row) -> list[Any]:
                return list(provider.logs(target.container_id, tail=per_container))

            lines = await asyncio.to_thread(_read)
        except DockerProviderError as exc:
            log.warning(
                "log_collection_failed",
                host=str(host.id),
                container=row.container_id[:12],
                error=str(exc),
            )
            continue
        total += await log_service.ingest_provider_lines(db, container_row=row, lines=lines)
    return total
