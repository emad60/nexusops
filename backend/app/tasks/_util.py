"""Shared plumbing for Celery tasks: fresh sessions + an event loop per invocation.

Workers are where tenancy is easiest to get wrong, so the scoping rules live here
rather than being re-derived in every task:

* a task that walks rows across tenants (a sweep, a retry queue) opens
  :func:`sweep_session` — the system scope, which is explicit, logged, and
  fenced by the module allowlist in :mod:`app.core.tenancy`;
* a task that works on one tenant's row resolves the owner first with
  :func:`org_for` and then runs inside :func:`org_session`, so the guard and RLS
  both apply to the actual work.

There is deliberately no ambient, task-level organization: a Celery worker's
process handles many tenants in sequence, and a scope that outlives one row is
how a background job leaks across a tenant boundary.
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from collections.abc import AsyncIterator, Coroutine
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def run_async[T](coroutine: Coroutine[Any, Any, T]) -> T:
    """Run *coroutine* on a dedicated event loop (Celery workers are sync).

    The loop is deliberately kept alive just long enough to flush the event
    frames the coroutine committed: ``event_bus`` announces an event from an
    ``after_commit`` hook by scheduling a publish task, and ``asyncio.run``
    cancels anything still pending the moment the coroutine returns. A task
    whose last act is a commit therefore used to lose its own frame — and with
    it every notification that frame would have dispatched.
    """

    async def _drained() -> T:
        from app.services.event_bus import flush_pending_publishes

        try:
            return await coroutine
        finally:
            await flush_pending_publishes()

    return asyncio.run(_drained())


@contextlib.asynccontextmanager
async def task_session() -> AsyncIterator[Any]:
    """Yield a short-lived session; commit on success, rollback on error."""
    from app.core.db import get_sessionmaker

    maker = get_sessionmaker()
    async with maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@contextlib.asynccontextmanager
async def sweep_session(reason: str) -> AsyncIterator[Any]:
    """A task session inside the **system** scope — for work that spans tenants.

    The reason is required and logged: inside this scope neither the ORM guard
    nor row-level security separates tenants for us, so an auditor has to be able
    to tell why it was opened.
    """
    from app.core.tenancy import apply_scope_to_session, system_scope

    async with task_session() as session:
        with system_scope(reason):
            await apply_scope_to_session(session)
            yield session


@contextlib.asynccontextmanager
async def org_session(org_id: uuid.UUID) -> AsyncIterator[Any]:
    """A task session bound to exactly one organization — for per-tenant work."""
    from app.core.tenancy import apply_scope_to_session, org_scope

    async with task_session() as session:
        with org_scope(org_id):
            await apply_scope_to_session(session)
            yield session


async def org_for(model: Any, row_id: Any) -> uuid.UUID | None:
    """The organization owning one row, resolved before any scope exists.

    This is the worker pattern the architecture prescribes: *claim a specific
    row, resolve its organization, then do the work inside that organization's
    scope*. The lookup itself runs under the system scope — the answer is what
    defines the scope, so there is nothing narrower to run it in — and it reads
    a single column of a single row by primary key.
    """
    from sqlalchemy import select

    async with sweep_session("worker.resolve_org") as session:
        return await session.scalar(select(model.org_id).where(model.id == row_id))
