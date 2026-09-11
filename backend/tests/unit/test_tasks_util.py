"""Unit tests for the Celery-task async bridge (pure asyncio, no broker)."""

from __future__ import annotations

import asyncio

import pytest
from app.tasks._util import run_async


async def _answer() -> int:
    await asyncio.sleep(0)
    return 42


async def _nested() -> str:
    return f"value-{await _answer()}"


async def _boom() -> None:
    raise RuntimeError("worker exploded")


def test_run_async_returns_coroutine_result() -> None:
    assert run_async(_answer()) == 42


def test_run_async_awaits_nested_coroutines() -> None:
    assert run_async(_nested()) == "value-42"


def test_run_async_propagates_exceptions() -> None:
    with pytest.raises(RuntimeError, match="worker exploded"):
        run_async(_boom())


def test_run_async_is_repeatable_per_invocation() -> None:
    # Each call gets a fresh event loop; sequential calls must not interfere.
    assert run_async(_answer()) == 42
    assert run_async(_answer()) == 42
