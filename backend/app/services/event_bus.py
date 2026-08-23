"""Event bus: the spine connecting domains → events table → Redis → WS hub.

Publishing an event:
  1. persists a :class:`SystemEvent` row (source of truth),
  2. best-effort publishes a compact JSON frame to ``nx:events`` for live fan-out,
  3. deduplicates via ``dedup_key`` where supplied (e.g. state-transition guards).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import orjson
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.channels import CHANNEL_EVENTS
from app.core.logging import get_logger
from app.core.redis_client import get_redis
from app.models import SystemEvent
from app.models.enums import ActorType, EventLevel

log = get_logger("nexusops.events")


async def publish(
    db: AsyncSession,
    *,
    type: str,
    message: str = "",
    level: EventLevel = EventLevel.INFO,
    actor_id: uuid.UUID | None = None,
    actor_type: ActorType = ActorType.SYSTEM,
    resource_type: str | None = None,
    resource_id: str | None = None,
    data: dict[str, Any] | None = None,
    dedup_key: str | None = None,
    commit: bool = False,
) -> SystemEvent | None:
    """Persist an event and fan it out to Redis. Returns None when deduplicated."""
    if dedup_key is not None:
        existing = (
            await db.execute(select(SystemEvent.id).where(SystemEvent.dedup_key == dedup_key))
        ).scalar_one_or_none()
        if existing is not None:
            return None

    event = SystemEvent(
        type=type,
        level=level,
        message=message[:500],
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        data=data or {},
        dedup_key=dedup_key,
    )
    db.add(event)
    await db.flush()
    if commit:
        await db.commit()

    frame = {
        "id": str(event.id),
        "type": type,
        "level": level.value,
        "message": message[:500],
        "actor_id": str(actor_id) if actor_id else None,
        "actor_type": actor_type.value,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "data": data or {},
        "created_at": (event.created_at or datetime.now(UTC)).isoformat(),
    }
    await _publish_redis(frame)
    log.debug("event_published", event_type=type, resource=resource_type)
    return event


async def _publish_redis(frame: dict[str, Any]) -> None:
    try:
        await get_redis().publish(CHANNEL_EVENTS, orjson.dumps(frame).decode())
    except Exception as exc:  # Redis down must never break business flow
        log.warning("event_redis_publish_failed", error=str(exc))


def event_frame_from_row(event: SystemEvent) -> dict[str, Any]:
    """Serialize a persisted event for WS delivery (used on replay/backfill)."""
    return {
        "id": str(event.id),
        "type": event.type,
        "level": event.level.value,
        "message": event.message,
        "actor_id": str(event.actor_id) if event.actor_id else None,
        "actor_type": event.actor_type.value
        if isinstance(event.actor_type, ActorType)
        else str(event.actor_type),
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "data": event.data or {},
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }
