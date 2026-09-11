"""Event bus fan-out ordering: a frame follows its transaction, never leads it.

Both consumers of ``nx:events`` (WS hub, notification dispatcher) dereference
the event id. Frames published before the surrounding transaction commits
raced the commit — the dispatcher FK-failed and silently lost the
notification — and a rolled-back transaction was announced as if it happened.
publish() therefore defers to the session's after-commit hook.
"""

from __future__ import annotations

import orjson
import pytest
from app.core.channels import CHANNEL_EVENTS
from app.core.redis_client import get_redis
from app.services import event_bus

pytestmark = pytest.mark.integration


async def _next_data_message(pubsub, wait: float):
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=wait)
        if message is None:
            return None
        if message.get("type") in ("message", "pmessage"):
            return message


async def test_frame_published_only_after_commit(db):
    pubsub = get_redis().pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(CHANNEL_EVENTS)
    try:
        await event_bus.publish(db, type="TEST.ORDERING", message="pending")
        # Flushed but NOT committed: the frame must not be fanable-out yet.
        assert await _next_data_message(pubsub, wait=0.5) is None

        await db.commit()
        message = await _next_data_message(pubsub, wait=3.0)
        assert message is not None, "frame must follow the commit"
        assert orjson.loads(message["data"])["type"] == "TEST.ORDERING"
    finally:
        await pubsub.aclose()


async def test_rolled_back_event_never_publishes(db):
    pubsub = get_redis().pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(CHANNEL_EVENTS)
    try:
        await event_bus.publish(db, type="TEST.ROLLBACK", message="never happened")
        await db.rollback()
        assert await _next_data_message(pubsub, wait=1.0) is None
    finally:
        await pubsub.aclose()


async def test_rolled_back_event_not_resurrected_by_later_commit(db):
    """Regression: a rollback must drop stashed frames, not defer them.

    The stash lives in ``session.info``; without an ``after_rollback`` hook a
    rolled-back frame survived there and was published by the session's NEXT
    commit — an unrelated commit resurrecting an event that never happened.
    """
    pubsub = get_redis().pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(CHANNEL_EVENTS)
    try:
        await event_bus.publish(db, type="TEST.ROLLBACK", message="never happened")
        await db.rollback()
        await db.commit()  # unrelated commit on the same session
        assert await _next_data_message(pubsub, wait=1.0) is None
    finally:
        await pubsub.aclose()
