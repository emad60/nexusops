"""Event bus: the spine connecting domains → events table → Redis → WS hub.

Publishing an event:
  1. persists a :class:`SystemEvent` row (source of truth),
  2. best-effort publishes a compact JSON frame to ``nx:events`` for live fan-out,
  3. deduplicates via ``dedup_key`` where supplied (e.g. state-transition guards).

Frames are published only AFTER their transaction commits: both consumers
(the WS hub and the notification dispatcher) dereference the event id, so a
frame that outruns its row breaks them — and an event whose transaction rolls
back must never be announced at all.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import orjson
from sqlalchemy import event as sa_event
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.channels import CHANNEL_EVENTS
from app.core.logging import get_logger
from app.core.redis_client import get_redis
from app.models import SystemEvent
from app.models.enums import ActorType, EventLevel

log = get_logger("nexusops.events")


#: Strong references to in-flight publish tasks — the loop only keeps weak
#: ones, and a GC'd task would silently drop its frame mid-publish.
_background_publishes: set[asyncio.Task[None]] = set()


def _after_commit_publish(session: Any) -> None:
    """Session hook: schedule pending frames once the transaction commits.

    Runs inside the commit's greenlet on the event-loop thread, so scheduling
    onto the running loop is safe. A rollback never fires this — pending
    frames die with the session's ``info`` dict.
    """
    frames = session.info.pop("_event_bus_pending", [])
    if not frames:
        return
    loop = asyncio.get_running_loop()
    for frame in frames:
        task = loop.create_task(_publish_redis(frame))
        _background_publishes.add(task)
        task.add_done_callback(_background_publishes.discard)


def _after_rollback_drop(session: Any) -> None:
    """Drop stashed frames on rollback.

    Without this, frames from a rolled-back unit of work sat in
    ``session.info`` and were published by a LATER, unrelated commit on the
    same session — announcing events that never happened. (No stash point
    runs inside a savepoint, so the outer ``after_rollback`` is sufficient.)
    """
    session.info.pop("_event_bus_pending", None)


def _publish_after_commit(db: AsyncSession, frame: dict[str, Any]) -> None:
    sync = db.sync_session
    pending: list[dict[str, Any]] = sync.info.setdefault("_event_bus_pending", [])
    pending.append(frame)
    if not sync.info.get("_event_bus_hook_installed"):
        sync.info["_event_bus_hook_installed"] = True
        sa_event.listen(sync, "after_commit", _after_commit_publish)
        sa_event.listen(sync, "after_rollback", _after_rollback_drop)


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
    if commit:
        await db.commit()
        await _publish_redis(frame)
    else:
        # Publish only once the surrounding transaction commits — see module
        # docstring. The dispatcher used to FK-fail on frames consumed before
        # the event row was visible, silently losing the notification.
        _publish_after_commit(db, frame)
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
