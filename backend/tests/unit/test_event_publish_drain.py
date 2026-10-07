"""Frames committed inside a task must reach Redis before that task's loop closes.

``event_bus`` cannot publish inside the commit — the row is not visible yet, and
a rolled-back transaction must announce nothing — so the ``after_commit`` hook
schedules the publish as a task on the running loop. A Celery task runs its
coroutine under ``asyncio.run`` (`app/tasks/_util.py`), which closes the loop the
instant the coroutine returns and cancels whatever is still pending.

That combination silently lost notifications: a monitor going DOWN set its
status, opened an incident and committed — and the frame announcing it was
cancelled before a byte reached Redis, so no channel saw the event and no email
was ever sent. In the e2e journey the symptom was
``notification delivery reached the mailpit sink`` finding zero deliveries and an
empty mailpit while the incidents existed.

This pins the mechanism at the seam that was broken, without Redis or a
database: the real hook schedules the publish, and ``run_async`` has to keep the
loop alive long enough for that publish to run.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.services import event_bus
from app.tasks._util import run_async
from sqlalchemy.orm import Session


class _FakeDb:
    """Stands in for an ``AsyncSession`` whose only job here is ``sync_session``.

    A real (unbound) ``Session`` is used because the hook is installed as a
    SQLAlchemy event listener, which only accepts a real mapper/session target.
    """

    def __init__(self) -> None:
        self.sync_session = Session()


def test_run_async_publishes_frames_scheduled_by_the_commit_hook(monkeypatch) -> None:
    """The shape of a worker task whose last statement is a commit."""
    published: list[str] = []

    async def fake_publish(frame: dict[str, Any]) -> None:
        # A real publish is Redis I/O; the sleep is what used to be interrupted.
        await asyncio.sleep(0.05)
        published.append(str(frame["type"]))

    monkeypatch.setattr(event_bus, "_publish_redis", fake_publish)

    async def commit_then_return() -> None:
        db = _FakeDb()
        # What ``event_bus.publish(..., commit=False)`` stashes, and what the
        # session's ``after_commit`` then hands to the loop.
        event_bus._publish_after_commit(db, {"type": "MONITOR_DOWN", "id": "event-1"})
        event_bus._after_commit_publish(db.sync_session)
        # No further await: without the drain, asyncio.run cancels the publish here.

    run_async(commit_then_return())

    assert published == ["MONITOR_DOWN"], (
        "the frame the commit scheduled never reached Redis: the task's loop "
        "closed before its own outbound publish ran"
    )


def test_flush_is_a_noop_when_nothing_is_pending() -> None:
    """The drain must not become a delay on the hot path for quiet tasks."""

    async def quiet() -> int:
        return 7

    assert run_async(quiet()) == 7
    assert run_async(event_bus.flush_pending_publishes()) == 0
