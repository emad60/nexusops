"""Alert inbox: insert-only creation plus read/unread bookkeeping."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound
from app.models import Alert
from app.models.enums import AlertSeverity

#: Event types that page an operator immediately.
CRITICAL_EVENT_TYPES = frozenset({"MONITOR_DOWN", "SERVER_OFFLINE", "DEPLOYMENT_FAILED"})

WARNING_EVENT_TYPES = frozenset({"NOTIFICATION_FAILED"})


def severity_for_event(event_type: str) -> AlertSeverity:
    """Map a system event type to the alert severity it deserves."""
    if event_type in CRITICAL_EVENT_TYPES:
        return AlertSeverity.CRITICAL
    if event_type in WARNING_EVENT_TYPES:
        return AlertSeverity.WARNING
    return AlertSeverity.INFO


async def create_alert(
    db: AsyncSession,
    *,
    event_type: str,
    severity: AlertSeverity,
    title: str,
    body: str = "",
    source: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> Alert:
    """Insert an alert row (flush only — the caller owns the transaction)."""
    alert = Alert(
        event_type=event_type[:64],
        severity=severity,
        title=title[:240],
        body=body[:4000],
        source=source[:32],
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
    )
    db.add(alert)
    await db.flush()
    return alert


async def get_alert(db: AsyncSession, alert_id: uuid.UUID) -> Alert | None:
    return (await db.execute(select(Alert).where(Alert.id == alert_id))).scalar_one_or_none()


async def mark_read(db: AsyncSession, alert_id: uuid.UUID) -> Alert:
    """Mark one alert read; raises :class:`NotFound` for unknown ids."""
    alert = await get_alert(db, alert_id)
    if alert is None:
        raise NotFound("Alert not found")
    if alert.read_at is None:
        alert.read_at = datetime.now(UTC)
        await db.flush()
    return alert


async def mark_all_read(db: AsyncSession) -> int:
    """Mark every unread alert read. Returns how many rows changed."""
    result = await db.execute(
        update(Alert).where(Alert.read_at.is_(None)).values(read_at=datetime.now(UTC))
    )
    await db.flush()
    return int(cast(CursorResult[Any], result).rowcount or 0)


async def unread_count(db: AsyncSession) -> int:
    return int(
        (
            await db.execute(select(func.count()).select_from(Alert).where(Alert.read_at.is_(None)))
        ).scalar_one()
    )
