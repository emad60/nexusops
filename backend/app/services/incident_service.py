"""Incident lifecycle: open, acknowledge, resolve, annotate.

Incidents are opened automatically by the monitor engine (see
``monitor_service.run_check``) and moved through their lifecycle either by that
engine (auto-resolution) or by operators via the API. All writes here use the
caller's transaction; the engine performs the single commit per check.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from app.api.deps import AuthContext
from app.core.errors import Conflict
from app.core.logging import get_logger
from app.models import Incident, IncidentEvent, Monitor
from app.models.enums import (
    ActorType,
    EventLevel,
    IncidentEventKind,
    IncidentSeverity,
    IncidentStatus,
)
from app.services import audit_service, event_bus

# --- Compatibility shim -------------------------------------------------------
# ``Incident.timeline`` declares back_populates="incident", but the contract
# model file omits the reverse relationship, which fails global mapper
# configuration for the entire app. Complete it here (guarded so this becomes a
# no-op once the proper relationship lands in app/models/observability.py).
if "incident" not in vars(IncidentEvent):
    IncidentEvent.incident = relationship("Incident", back_populates="timeline")

log = get_logger("nexusops.incidents")


def _now() -> datetime:
    return datetime.now(UTC)


def _add_event(
    incident: Incident,
    *,
    kind: IncidentEventKind,
    message: str,
    actor_id: uuid.UUID | None = None,
) -> IncidentEvent:
    return IncidentEvent(
        incident_id=incident.id,
        kind=kind,
        message=message[:4000],
        actor_id=actor_id,
        data={},
        occurred_at=_now(),
    )


async def get_incident(db: AsyncSession, incident_id: uuid.UUID) -> Incident | None:
    """Fetch an incident by id (timeline loads eagerly via selectin)."""
    return (
        await db.execute(select(Incident).where(Incident.id == incident_id))
    ).scalar_one_or_none()


async def list_incidents(
    db: AsyncSession,
    *,
    status_filter: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    monitor_id: uuid.UUID | None = None,
    limit: int,
    offset: int,
) -> tuple[list[Incident], int]:
    """Paged incidents, newest first."""
    stmt = select(Incident)
    if status_filter is not None:
        stmt = stmt.where(Incident.status == status_filter)
    if severity is not None:
        stmt = stmt.where(Incident.severity == severity)
    if monitor_id is not None:
        stmt = stmt.where(Incident.monitor_id == monitor_id)
    stmt = stmt.order_by(Incident.opened_at.desc())
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    return list(rows), int(total)


async def monitor_names(db: AsyncSession, incidents: list[Incident]) -> dict[uuid.UUID, str]:
    """Monitor id → name map for a page of incidents (avoids N+1 in routers)."""
    ids = {i.monitor_id for i in incidents}
    if not ids:
        return {}
    rows = (await db.execute(select(Monitor.id, Monitor.name).where(Monitor.id.in_(ids)))).all()
    return {mid: name for mid, name in rows}


async def open_incident(
    db: AsyncSession,
    monitor: Monitor,
    *,
    failure_count: int = 1,
    error: str = "",
) -> Incident:
    """Open a new incident for *monitor* (flush only; caller owns commit)."""
    now = _now()
    incident = Incident(
        monitor_id=monitor.id,
        title=f"{monitor.name} is down",
        severity=IncidentSeverity.MAJOR,
        status=IncidentStatus.OPEN,
        failure_count=max(failure_count, 1),
        opened_at=now,
        detected_at=now,
        resolution="",
    )
    db.add(incident)
    await db.flush()

    db.add(
        _add_event(
            incident,
            kind=IncidentEventKind.OPENED,
            message=f"Opened after {max(failure_count, 1)} consecutive failing checks",
        )
    )
    db.add(
        _add_event(
            incident,
            kind=IncidentEventKind.DETECTED,
            message=f"Detection error: {error[:300]}" if error else "Failure threshold reached",
        )
    )

    await event_bus.publish(
        db,
        type="INCIDENT_OPENED",
        message=f"Incident opened for {monitor.name}",
        level=EventLevel.ERROR,
        resource_type="incident",
        resource_id=str(incident.id),
        data={"monitor_id": str(monitor.id), "monitor_name": monitor.name},
        dedup_key=f"incident-opened:{incident.id}",
    )
    return incident


async def acknowledge(
    db: AsyncSession,
    incident: Incident,
    ctx: AuthContext | None,
    *,
    note: str = "",
    request: Request | None = None,
) -> Incident:
    """Acknowledge an OPEN incident on behalf of an operator."""
    if incident.status != IncidentStatus.OPEN:
        raise Conflict(f"Cannot acknowledge incident in status {incident.status.value}")
    actor = ctx.email if ctx else "operator"
    incident.status = IncidentStatus.ACKNOWLEDGED
    incident.acknowledged_at = _now()
    incident.acknowledged_by_id = ctx.user_id if ctx else None
    db.add(
        _add_event(
            incident,
            kind=IncidentEventKind.ACKNOWLEDGED,
            message=note.strip() or f"Acknowledged by {actor}",
            actor_id=ctx.user_id if ctx else None,
        )
    )
    await db.flush()
    await audit_service.record(
        db,
        ctx,
        action="incident.acknowledge",
        resource_type="incident",
        resource_id=incident.id,
        request=request,
    )
    await event_bus.publish(
        db,
        type="INCIDENT_ACKNOWLEDGED",
        message=f"Incident acknowledged by {actor}",
        level=EventLevel.INFO,
        actor_id=ctx.user_id if ctx else None,
        actor_type=ActorType.USER if ctx else ActorType.SYSTEM,
        resource_type="incident",
        resource_id=str(incident.id),
        data={"monitor_id": str(incident.monitor_id)},
    )
    return incident


async def resolve(
    db: AsyncSession,
    incident: Incident,
    resolution_text: str,
    ctx: AuthContext | None = None,
    *,
    request: Request | None = None,
    auto: bool = False,
) -> Incident:
    """Resolve an incident. ``auto=True`` marks the transition as machine-made."""
    if incident.status == IncidentStatus.RESOLVED:
        raise Conflict("Incident is already resolved")
    actor_label = "automatic recovery" if auto else (ctx.email if ctx else "operator")
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = _now()
    incident.resolution = (resolution_text or "")[:4000]
    db.add(
        _add_event(
            incident,
            kind=IncidentEventKind.RESOLVED,
            message=f"Resolved by {actor_label}: {resolution_text[:300]}",
            actor_id=None if auto else (ctx.user_id if ctx else None),
        )
    )
    await db.flush()

    if not auto:
        await audit_service.record(
            db,
            ctx,
            action="incident.resolve",
            resource_type="incident",
            resource_id=incident.id,
            request=request,
        )
    await event_bus.publish(
        db,
        type="INCIDENT_RESOLVED",
        message=f"Incident resolved by {actor_label}",
        level=EventLevel.INFO,
        actor_id=None if auto else (ctx.user_id if ctx else None),
        actor_type=ActorType.SYSTEM if auto else (ActorType.USER if ctx else ActorType.SYSTEM),
        resource_type="incident",
        resource_id=str(incident.id),
        data={"monitor_id": str(incident.monitor_id), "auto": auto},
    )
    return incident


async def add_note(
    db: AsyncSession,
    incident: Incident,
    ctx: AuthContext | None,
    message: str,
    *,
    request: Request | None = None,
    kind: IncidentEventKind = IncidentEventKind.NOTE,
) -> IncidentEvent:
    """Append a timeline entry. Only user-authored notes are audited."""
    text = (message or "").strip()
    if not text:
        raise Conflict("Note must not be empty")
    event = _add_event(incident, kind=kind, message=text, actor_id=ctx.user_id if ctx else None)
    db.add(event)
    await db.flush()
    if ctx is not None and request is not None:
        await audit_service.record(
            db,
            ctx,
            action="incident.note",
            resource_type="incident",
            resource_id=incident.id,
            request=request,
        )
    return event
