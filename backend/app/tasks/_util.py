"""Shared plumbing for Celery tasks: fresh sessions + an event loop per invocation."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Coroutine
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def run_async[T](coroutine: Coroutine[Any, Any, T]) -> T:
    """Run *coroutine* on a dedicated event loop (Celery workers are sync)."""
    return asyncio.run(coroutine)


@contextlib.asynccontextmanager
async def task_session():
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
