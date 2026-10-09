"""Event bus: the spine connecting domains → events table → Redis → WS hub.

Publishing an event:
  1. persists a :class:`SystemEvent` row (source of truth),
  2. best-effort publishes a compact JSON frame to ``nx:events`` for live fan-out,
  3. deduplicates via ``dedup_key`` where supplied (e.g. state-transition guards).

Frames are published only AFTER their transaction commits: both consumers
(the WS hub and the notification dispatcher) dereference the event id, so a
frame that outruns its row breaks them — and an event whose transaction rolls
back must never be announced at all.

Every event carries its organization. Request paths inherit it from the tenancy
scope; sweeps and workers pass it explicitly (there is no ambient answer once a
worker acts across tenants); and the genuinely org-less events that remain are
written under the system scope, which is also why no tenant can read them.

A named actor (a user, a machine) is required to belong somewhere: publishing
one without an organization raises, so tenant work can never be filed under no
tenant. The narrow exception is :attr:`publish`'s ``instance_level`` opt-in, used
only for the pre-organization authentication facts (a sign-in, a failed attempt,
a sign-out or a password change for an account whose membership is none or
ambiguous). Those are honest instance-level records: ``org_id IS NULL``, written
under the system scope, dropped by the WS hub for every org subscriber, and
invisible to every tenant-scoped read. It is deliberately explicit at each call
site rather than a blanket allowance — nothing else may pass it.
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
from app.core.tenancy import TenancyScopeError, current_org, system_write_scope
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


#: How long a short-lived loop waits for the frames its own commit scheduled
#: before closing. A Redis publish is sub-millisecond; the bound exists only so
#: a wedged Redis cannot hang a Celery task.
PUBLISH_DRAIN_TIMEOUT_SECONDS = 5.0


async def flush_pending_publishes(drain_seconds: float = PUBLISH_DRAIN_TIMEOUT_SECONDS) -> int:
    """Wait for frames scheduled by ``after_commit`` hooks to reach Redis.

    The commit hook cannot await — it runs inside the commit — so it schedules
    the publish as a task on the running loop. That is correct for a long-lived
    loop (the API serves it, and the task runs a moment later) and wrong for a
    short-lived one: ``asyncio.run`` closes the loop as soon as its coroutine
    returns and cancels whatever is still pending, so a worker task whose last
    act is a commit announced its event to nobody — which is exactly how every
    monitor/incident notification went missing.

    Callers that own a short-lived loop await this before closing it. Returns
    how many frames were still in flight when the wait expired; those are
    cancelled and logged, because an unsent frame is a notification nobody
    received.
    """
    pending = [task for task in _background_publishes if not task.done()]
    if not pending:
        return 0
    _, unfinished = await asyncio.wait(pending, timeout=drain_seconds)
    for task in unfinished:
        task.cancel()
    if unfinished:
        # Reap the cancellations so they do not surface as loop-shutdown noise.
        await asyncio.gather(*unfinished, return_exceptions=True)
        log.warning(
            "event_publish_drain_incomplete",
            frames=len(unfinished),
            drain_seconds=drain_seconds,
        )
    return len(unfinished)


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
    org_id: uuid.UUID | None = None,
    instance_level: bool = False,
) -> SystemEvent | None:
    """Persist an event and fan it out to Redis. Returns None when deduplicated.

    The organization defaults to the active tenancy scope, which is correct for
    every request-scoped publish and most worker publishes. Sweeps that run
    under ``system_scope()`` and act on rows belonging to different tenants must
    pass ``org_id`` explicitly: there is no ambient answer, and the dispatcher
    matches notification channels by the frame's organization, so an event
    published to the wrong org is a cross-tenant notification.

    ``instance_level=True`` is the *only* way a named actor may be published with
    no organization, and it exists solely for pre-organization authentication
    facts. It is opt-in per call so the invariant stays loud everywhere else; the
    resulting row is ``org_id IS NULL`` and invisible to every tenant.
    """
    resolved_org = org_id if org_id is not None else current_org()
    if dedup_key is not None:
        existing = (
            await db.execute(select(SystemEvent.id).where(SystemEvent.dedup_key == dedup_key))
        ).scalar_one_or_none()
        if existing is not None:
            return None

    if resolved_org is None and actor_type is not ActorType.SYSTEM and not instance_level:
        # A named actor (user or machine) always belongs somewhere; publishing
        # without an organization would file the event under no tenant at all.
        # The one deliberate exception is a pre-org auth fact, which an operator
        # cannot attribute to a single tenant and which therefore declares
        # ``instance_level=True`` explicitly at its call site.
        raise TenancyScopeError(
            f"event {type!r} has an actor but no organization: pass org_id= or "
            f"run inside org_scope(...)"
        )

    event = SystemEvent(
        org_id=resolved_org,
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
    if resolved_org is None:
        # An event with no organization (a system-actor, instance-level record:
        # bootstrap, a failed login for an address with no account) can only be
        # written under the system scope. The tenant policy requires
        # ``org_id = current org`` and a NULL never matches it; the system policy
        # is the one that admits org-less rows — and, symmetrically, keeps them
        # invisible to every tenant afterwards.
        async with system_write_scope(db, "event_bus.orgless_event"):
            db.add(event)
            await db.flush()
    else:
        db.add(event)
        await db.flush()

    frame = {
        "id": str(event.id),
        "org_id": str(resolved_org) if resolved_org else None,
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
        "org_id": str(event.org_id) if event.org_id else None,
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
