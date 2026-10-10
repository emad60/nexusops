"""Deferred Celery handoff: enqueue only after the creating transaction commits.

A task dispatched inline races the worker. Its first query filters on a row the
API transaction has not committed yet, so the task finds nothing and no-ops — and
the work sits untouched until a slow sweep rescues it. The deployment engine
learned this the hard way and solved it with an ``after_commit`` listener; this
module is the same pattern, generalised so a new subsystem does not re-derive it
(and does not accidentally re-introduce the race).

Rollback drops the stashed callbacks, because otherwise a *later*, unrelated
commit on the same session would enqueue work for rows that never existed.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import event as sa_event
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

log = get_logger("nexusops.enqueue")

#: Strong references to in-flight enqueue tasks, so the event loop cannot
#: garbage-collect one before it runs.
_background: set[asyncio.Task[None]] = set()

_STASH_KEY = "_nexusops_after_commit"
_HOOK_KEY = "_nexusops_after_commit_installed"


async def _run(label: str, factory: Callable[[], Awaitable[Any]]) -> None:
    try:
        await factory()
    except Exception as exc:  # broker downtime must never fail the request
        log.warning("enqueue_failed", label=label, error=exc.__class__.__name__)


def _on_commit(session: Any) -> None:
    pending: list[tuple[str, Callable[[], Awaitable[Any]]]] = session.info.pop(_STASH_KEY, [])
    if not pending:
        return
    loop = asyncio.get_running_loop()
    for label, factory in pending:
        task = loop.create_task(_run(label, factory))
        _background.add(task)
        task.add_done_callback(_background.discard)


def _on_rollback(session: Any) -> None:
    session.info.pop(_STASH_KEY, None)


def after_commit(db: AsyncSession, label: str, factory: Callable[[], Awaitable[Any]]) -> None:
    """Run ``factory`` once the current transaction commits.

    ``label`` names the work in logs so a dropped enqueue is diagnosable.
    """
    sync = db.sync_session
    sync.info.setdefault(_STASH_KEY, []).append((label, factory))
    if not sync.info.get(_HOOK_KEY):
        sync.info[_HOOK_KEY] = True
        sa_event.listen(sync, "after_commit", _on_commit)
        sa_event.listen(sync, "after_rollback", _on_rollback)
