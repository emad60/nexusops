"""Uptime monitor engine: CRUD, due-claim scheduling, check execution.

The engine is designed for multiple concurrent runners: :func:`claim_due_monitors`
atomically reserves a batch with ``FOR UPDATE SKIP LOCKED``, and :func:`run_check`
takes a ``NOWAIT`` row lock so a monitor is never probed twice in parallel. A
single commit closes each check.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import Request
from sqlalchemy import case, func, select, tuple_, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.config import get_settings
from app.core.errors import AppError, BadRequest, NotFound
from app.core.logging import get_logger
from app.core.pagination import CursorParams, decode_cursor, encode_cursor
from app.core.ssrf import assert_safe_url_async, is_simulation_url
from app.models import Incident, Monitor, MonitorCheck, Project
from app.models.enums import (
    AlertSeverity,
    CheckResult,
    EventLevel,
    IncidentEventKind,
    IncidentStatus,
    MonitorStatus,
)
from app.providers.monitor_transport import CheckOutcome, coerce_headers, get_transport, strip_query
from app.schemas.monitor import MonitorCreate, MonitorUpdate
from app.services import alert_service, audit_service, event_bus, incident_service

log = get_logger("nexusops.monitors")

ACTIVE_INCIDENT_STATUSES = (IncidentStatus.OPEN, IncidentStatus.ACKNOWLEDGED)
MAX_UPTIME_HOURS = 720

_SORT_COLUMNS = {
    "created_at": Monitor.created_at,
    "name": Monitor.name,
    "status": Monitor.status,
    "next_check_at": Monitor.next_check_at,
}


def _now() -> datetime:
    return datetime.now(UTC)


async def _audit(
    db: AsyncSession,
    ctx: AuthContext | None,
    action: str,
    monitor_id: uuid.UUID | str,
    *,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    await audit_service.record(
        db,
        ctx,
        action=action,
        resource_type="monitor",
        resource_id=monitor_id,
        request=request,
        metadata=metadata,
    )


async def _emit(
    db: AsyncSession,
    event_type: str,
    message: str,
    ctx: AuthContext | None,
    monitor: Monitor,
    *,
    level: EventLevel = EventLevel.INFO,
    data: dict[str, Any] | None = None,
) -> None:
    await event_bus.publish(
        db,
        type=event_type,
        message=message,
        level=level,
        actor_id=ctx.user_id if ctx else None,
        resource_type="monitor",
        resource_id=str(monitor.id),
        data=data or {},
    )


async def require_monitor(db: AsyncSession, monitor_id: uuid.UUID) -> Monitor:
    monitor = (
        await db.execute(select(Monitor).where(Monitor.id == monitor_id))
    ).scalar_one_or_none()
    if monitor is None:
        raise NotFound("Monitor not found")
    return monitor


async def validate_monitor_url(url: str) -> str:
    """SSRF-check *url*; ``sim://`` targets are allowed only in simulation mode."""
    if is_simulation_url(url):
        if not get_settings().simulation_mode:
            raise BadRequest("sim:// monitors require simulation mode")
        return url
    await assert_safe_url_async(url)
    return url


def _validate_headers(headers: dict[str, str]) -> dict[str, str]:
    clean = coerce_headers(headers)
    if len(clean) > 20:
        raise BadRequest("At most 20 headers are allowed")
    return clean


async def _require_project(db: AsyncSession, project_id: uuid.UUID | None) -> None:
    exists = (
        await db.execute(select(Project.id).where(Project.id == project_id))
    ).scalar_one_or_none()
    if exists is None:
        raise NotFound("Project not found")


# --- CRUD ---------------------------------------------------------------------


async def create_monitor(
    db: AsyncSession,
    ctx: AuthContext | None,
    data: MonitorCreate,
    *,
    request: Request | None = None,
) -> Monitor:
    """Create a monitor scheduled for its first immediate check."""
    await validate_monitor_url(data.url)
    if data.project_id is not None:
        await _require_project(db, data.project_id)
    monitor = Monitor(
        name=data.name.strip(),
        project_id=data.project_id,
        url=data.url.strip(),
        method=data.method,
        interval_seconds=data.interval_seconds,
        timeout_seconds=data.timeout_seconds,
        expected_status=data.expected_status,
        expected_body=data.expected_body or None,
        headers=_validate_headers(data.headers),
        skip_tls_verify=data.skip_tls_verify,
        follow_redirects=data.follow_redirects,
        enabled=data.enabled,
        failure_threshold=data.failure_threshold,
        success_threshold=data.success_threshold,
        status=MonitorStatus.PENDING,
        next_check_at=_now(),
        created_by_id=ctx.user_id if ctx else None,
    )
    db.add(monitor)
    await db.flush()

    await _audit(
        db,
        ctx,
        "monitor.create",
        monitor.id,
        request=request,
        # Audit is append-only: persist the query-stripped URL so tokens
        # embedded in the query cannot leak into the trail.
        metadata={"url": strip_query(monitor.url), "interval": monitor.interval_seconds},
    )
    await _emit(
        db,
        "MONITOR_CREATED",
        f"Monitor {monitor.name} created",
        ctx,
        monitor,
        data={"name": monitor.name},
    )
    return monitor


async def update_monitor(
    db: AsyncSession,
    ctx: AuthContext | None,
    monitor: Monitor,
    data: MonitorUpdate,
    *,
    request: Request | None = None,
) -> Monitor:
    """Apply a partial update. URL changes are re-run through the SSRF guard."""
    changes: dict[str, Any] = {}
    provided = data.model_dump(exclude_unset=True)

    if "project_id" in provided and data.project_id != monitor.project_id:
        await _require_project(db, data.project_id)
    if isinstance(data.url, str):
        await validate_monitor_url(data.url)

    for field, value in provided.items():
        if field == "headers":
            value = _validate_headers(value or {})
        elif field in ("name", "url") and isinstance(value, str):
            value = value.strip()
            if field == "url" and value == monitor.url:
                continue
        setattr(monitor, field, value)
        changes[field] = value

    await db.flush()
    await _audit(
        db, ctx, "monitor.update", monitor.id, request=request, metadata={"changes": list(changes)}
    )
    if changes:
        await _emit(
            db,
            "MONITOR_UPDATED",
            f"Monitor {monitor.name} updated",
            ctx,
            monitor,
            data={"fields": sorted(changes)},
        )
    return monitor


async def delete_monitor(
    db: AsyncSession,
    ctx: AuthContext | None,
    monitor: Monitor,
    *,
    request: Request | None = None,
) -> None:
    name, monitor_id = monitor.name, str(monitor.id)
    await db.delete(monitor)
    await db.flush()
    await _audit(db, ctx, "monitor.delete", monitor_id, request=request, metadata={"name": name})
    await event_bus.publish(
        db,
        type="MONITOR_DELETED",
        message=f"Monitor {name} deleted",
        level=EventLevel.INFO,
        actor_id=ctx.user_id if ctx else None,
        resource_type="monitor",
        resource_id=monitor_id,
    )


async def pause_monitor(
    db: AsyncSession,
    ctx: AuthContext | None,
    monitor: Monitor,
    *,
    request: Request | None = None,
) -> Monitor:
    if not monitor.enabled:
        raise BadRequest("Monitor is already paused")
    monitor.enabled = False
    monitor.status = MonitorStatus.PAUSED
    await db.flush()
    await _audit(db, ctx, "monitor.pause", monitor.id, request=request)
    await _emit(db, "MONITOR_PAUSED", f"Monitor {monitor.name} paused", ctx, monitor)
    return monitor


async def resume_monitor(
    db: AsyncSession,
    ctx: AuthContext | None,
    monitor: Monitor,
    *,
    request: Request | None = None,
) -> Monitor:
    if monitor.enabled:
        raise BadRequest("Monitor is already active")
    monitor.enabled = True
    monitor.status = MonitorStatus.PENDING
    monitor.next_check_at = _now()  # resume checks immediately
    await db.flush()
    await _audit(db, ctx, "monitor.resume", monitor.id, request=request)
    await _emit(db, "MONITOR_RESUMED", f"Monitor {monitor.name} resumed", ctx, monitor)
    return monitor


# --- Scheduling & execution ---------------------------------------------------


async def claim_due_monitors(db: AsyncSession, limit: int = 50) -> list[uuid.UUID]:
    """Atomically reschedule and return the ids of due monitors (single statement)."""
    due_ids = (
        select(Monitor.id)
        .where(Monitor.enabled.is_(True), Monitor.next_check_at <= func.now())
        .order_by(Monitor.next_check_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    stmt = (
        update(Monitor)
        .where(Monitor.id.in_(due_ids))
        .values(
            next_check_at=func.now()
            + func.make_interval(0, 0, 0, 0, 0, 0, Monitor.interval_seconds)
        )
        .returning(Monitor.id)
    )
    rows = (await db.execute(stmt)).scalars().all()
    await db.commit()
    return list(rows)


async def _active_incident(db: AsyncSession, monitor_id: uuid.UUID) -> Incident | None:
    stmt = (
        select(Incident)
        .where(Incident.monitor_id == monitor_id, Incident.status.in_(ACTIVE_INCIDENT_STATUSES))
        .order_by(Incident.opened_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def run_check(db: AsyncSession, monitor_id: uuid.UUID) -> MonitorCheck | None:
    """Execute one check cycle for *monitor_id* and commit the result.

    Returns ``None`` when the monitor is missing, paused, or locked by another
    runner. Outcome-level problems (timeouts, bad statuses) never raise;
    unexpected transport exceptions propagate.
    """
    try:
        monitor = (
            await db.execute(
                select(Monitor).where(Monitor.id == monitor_id).with_for_update(nowait=True)
            )
        ).scalar_one_or_none()
    except OperationalError:
        log.debug("check_lock_busy", monitor_id=str(monitor_id))
        return None
    if monitor is None or not monitor.enabled:
        return None

    # Defense in depth: re-apply the SSRF guard at execution time. The guard
    # may have tightened (or the row been edited outside the API) since the
    # monitor was created; a now-forbidden target must not be probed.
    outcome: CheckOutcome | None = None
    if not is_simulation_url(monitor.url):
        try:
            await validate_monitor_url(monitor.url)
        except AppError:
            outcome = CheckOutcome(
                result=CheckResult.ERROR,
                error="url failed SSRF re-validation",
            )
    if outcome is None:
        outcome = await get_transport(monitor).check(monitor)
    now = _now()
    check = MonitorCheck(
        monitor_id=monitor.id,
        checked_at=now,
        result=outcome.result,
        response_time_ms=outcome.response_time_ms,
        status_code=outcome.status_code,
        error=(outcome.error or "")[:500],
    )
    db.add(check)
    open_incident = await _active_incident(db, monitor.id)

    if outcome.result == CheckResult.SUCCESS:
        monitor.consecutive_successes += 1
        monitor.consecutive_failures = 0
        monitor.last_success_at = now
        monitor.status = MonitorStatus.UP
        if open_incident is not None and monitor.consecutive_successes >= monitor.success_threshold:
            await incident_service.resolve(
                db,
                open_incident,
                f"{monitor.success_threshold} consecutive successful checks",
                None,
                auto=True,
            )
            await _emit(
                db,
                "MONITOR_RECOVERED",
                f"{monitor.name} recovered",
                None,
                monitor,
                data={"consecutive_successes": monitor.consecutive_successes},
            )
            await alert_service.create_alert(
                db,
                event_type="MONITOR_RECOVERED",
                severity=AlertSeverity.INFO,
                title=f"{monitor.name} recovered",
                body=f"Incident resolved after {monitor.success_threshold} successful checks.",
                source="monitor",
                resource_type="monitor",
                resource_id=str(monitor.id),
            )
    else:
        monitor.consecutive_failures += 1
        monitor.consecutive_successes = 0
        monitor.last_failure_at = now
        monitor.status = MonitorStatus.DOWN
        failures = monitor.consecutive_failures

        if failures == monitor.failure_threshold and open_incident is None:
            incident = await incident_service.open_incident(
                db, monitor, failure_count=failures, error=outcome.error or outcome.result.value
            )
            await _emit(
                db,
                "MONITOR_DOWN",
                f"{monitor.name} is DOWN ({outcome.error or outcome.result.value})",
                None,
                monitor,
                level=EventLevel.ERROR,
                data={"incident_id": str(incident.id), "consecutive_failures": failures},
            )
            await alert_service.create_alert(
                db,
                event_type="MONITOR_DOWN",
                severity=AlertSeverity.CRITICAL,
                title=f"{monitor.name} is DOWN",
                body=outcome.error or f"{failures} consecutive failing checks.",
                source="monitor",
                resource_type="monitor",
                resource_id=str(monitor.id),
            )
        elif failures > monitor.failure_threshold and open_incident is not None:
            open_incident.failure_count += 1
            if open_incident.failure_count % 5 == 0:
                await incident_service.add_note(
                    db,
                    open_incident,
                    None,
                    f"Still failing after {open_incident.failure_count} checks "
                    f"({outcome.error or outcome.result.value})",
                    kind=IncidentEventKind.NOTE,
                )

    monitor.last_check_at = now
    monitor.next_check_at = now + timedelta(seconds=monitor.interval_seconds)
    await db.commit()
    return check


# --- Reads & aggregation ------------------------------------------------------


async def list_monitors(
    db: AsyncSession,
    *,
    status_filter: MonitorStatus | None = None,
    project_id: uuid.UUID | None = None,
    q: str | None = None,
    sort: str = "created_at",
    limit: int,
    offset: int,
) -> tuple[list[Monitor], int]:
    """Paged monitor list. *sort* may carry a leading ``-`` for descending."""
    column = _SORT_COLUMNS.get(sort.lstrip("-"))
    if column is None:
        raise BadRequest("Invalid sort field")
    stmt = select(Monitor)
    if status_filter is not None:
        stmt = stmt.where(Monitor.status == status_filter)
    if project_id is not None:
        stmt = stmt.where(Monitor.project_id == project_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Monitor.name.ilike(like) | Monitor.url.ilike(like))
    stmt = stmt.order_by(column.desc() if sort.startswith("-") else column.asc())
    total = (
        await db.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))
    ).scalar_one()
    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    return list(rows), int(total)


async def page_decorations(db: AsyncSession, monitors: list[Monitor]) -> dict[str, dict[Any, Any]]:
    """Cheap per-page aggregates: 24h uptime pct, active incident id, project name."""
    stats: dict[uuid.UUID, float] = {}
    incidents_by_monitor: dict[uuid.UUID, uuid.UUID] = {}
    projects: dict[uuid.UUID, str] = {}
    ids = [m.id for m in monitors]
    if not ids:
        return {"uptime": stats, "incidents": incidents_by_monitor, "projects": projects}

    since = _now() - timedelta(hours=24)
    rows = (
        await db.execute(
            select(
                MonitorCheck.monitor_id,
                func.count(),
                func.sum(case((MonitorCheck.result == CheckResult.SUCCESS, 1), else_=0)),
            )
            .where(MonitorCheck.monitor_id.in_(ids), MonitorCheck.checked_at >= since)
            .group_by(MonitorCheck.monitor_id)
        )
    ).all()
    for monitor_id, total, successes in rows:
        stats[monitor_id] = round((successes or 0) * 100 / total, 3) if total else 100.0

    inc_rows = (
        await db.execute(
            select(Incident.monitor_id, Incident.id)
            .where(Incident.monitor_id.in_(ids), Incident.status.in_(ACTIVE_INCIDENT_STATUSES))
            .order_by(Incident.opened_at.desc())
        )
    ).all()
    for monitor_id, incident_id in inc_rows:
        incidents_by_monitor.setdefault(monitor_id, incident_id)

    project_ids = {m.project_id for m in monitors if m.project_id is not None}
    if project_ids:
        name_rows = (
            await db.execute(select(Project.id, Project.name).where(Project.id.in_(project_ids)))
        ).all()
        projects = dict(cast(Iterable[tuple[uuid.UUID, str]], name_rows))

    return {"uptime": stats, "incidents": incidents_by_monitor, "projects": projects}


async def uptime_summary(
    db: AsyncSession, monitor_id: uuid.UUID, hours: int = 24
) -> dict[str, Any]:
    """Aggregate availability for one monitor over the trailing window."""
    window = max(1, min(hours, MAX_UPTIME_HOURS))
    since = _now() - timedelta(hours=window)
    row = (
        await db.execute(
            select(
                func.count(),
                func.sum(case((MonitorCheck.result != CheckResult.SUCCESS, 1), else_=0)),
                func.avg(MonitorCheck.response_time_ms),
                func.percentile_cont(0.95).within_group(MonitorCheck.response_time_ms.asc()),
            ).where(MonitorCheck.monitor_id == monitor_id, MonitorCheck.checked_at >= since)
        )
    ).one()
    total, failed = int(row[0] or 0), int(row[1] or 0)
    return {
        "uptime_pct": round((total - failed) * 100 / total, 3) if total else 100.0,
        "total_checks": total,
        "failed_checks": failed,
        "avg_response_ms": round(float(row[2]), 2) if row[2] is not None else None,
        "p95_response_ms": round(float(row[3]), 2) if row[3] is not None else None,
    }


async def list_checks(
    db: AsyncSession, monitor_id: uuid.UUID, params: CursorParams
) -> tuple[list[MonitorCheck], str | None, bool]:
    """Keyset-paged check history, newest first."""
    stmt = select(MonitorCheck).where(MonitorCheck.monitor_id == monitor_id)
    cursor = decode_cursor(params.cursor)
    if cursor is not None:
        stmt = stmt.where(tuple_(MonitorCheck.checked_at, MonitorCheck.id) < (cursor.ts, cursor.id))
    stmt = stmt.order_by(MonitorCheck.checked_at.desc(), MonitorCheck.id.desc())
    rows = (await db.execute(stmt.limit(params.limit + 1))).scalars().all()
    has_more = len(rows) > params.limit
    rows = rows[: params.limit]
    next_cursor = encode_cursor(rows[-1].checked_at, rows[-1].id) if has_more and rows else None
    return list(rows), next_cursor, has_more
