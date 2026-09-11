"""Unit tests for the Redis-backed rate limiter's failure modes.

Regression coverage: auth-facing limiters used to *fail open* — a Redis
outage silently removed the login/register/refresh throttles and opened the
door to full-rate credential brute-forcing. Auth limiters now degrade to an
in-process fixed-window counter (fail closed); general endpoints keep the
availability-friendly fail-open behaviour.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.core.errors import RateLimited
from app.core.rate_limit import (
    _memory_count_and_ttl,
    _memory_windows,
    auth_limiter,
    rate_limit,
)


class _FakeRequest:
    def __init__(self, ip: str = "203.0.113.7") -> None:
        self.headers: dict[str, str] = {}
        self.client = SimpleNamespace(host=ip)


@pytest.fixture(autouse=True)
def _clean_memory_windows():
    _memory_windows.clear()
    yield
    _memory_windows.clear()


@pytest.fixture
def redis_down(monkeypatch: pytest.MonkeyPatch):
    def _boom():
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr("app.core.rate_limit.get_redis", _boom)
    return True


async def test_fail_closed_limiter_still_limits_when_redis_down(redis_down) -> None:
    dependency = rate_limit("unit-auth", 2, 60, fail_closed=True)

    await dependency(_FakeRequest())  # 1
    await dependency(_FakeRequest())  # 2
    with pytest.raises(RateLimited):
        await dependency(_FakeRequest())  # 3 → throttled despite the outage


async def test_auth_limiter_is_fail_closed(redis_down) -> None:
    dependency = auth_limiter()
    for _ in range(10):
        await dependency(_FakeRequest())
    with pytest.raises(RateLimited):
        await dependency(_FakeRequest())


async def test_fail_open_limiter_stays_available_when_redis_down(redis_down) -> None:
    dependency = rate_limit("unit-general", 1, 60, fail_closed=False)
    for _ in range(5):
        # Never raises: general endpoints prefer availability.
        await dependency(_FakeRequest())


async def test_fail_closed_fallback_is_per_ip(redis_down) -> None:
    dependency = rate_limit("unit-scoped", 1, 60, fail_closed=True)
    await dependency(_FakeRequest(ip="198.51.100.1"))
    await dependency(_FakeRequest(ip="198.51.100.2"))  # different bucket → fine
    with pytest.raises(RateLimited):
        await dependency(_FakeRequest(ip="198.51.100.1"))


async def test_memory_counter_resets_per_window(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.core.rate_limit as rl

    now = 3_000_000  # % 60 == 0 → full window ahead
    monkeypatch.setattr(rl.time, "time", lambda: now)
    key = "nx:rl:unit-window:1.2.3.4"
    assert _memory_count_and_ttl(key, 60) == (1, 60)
    assert _memory_count_and_ttl(key, 60) == (2, 60)
    # Roll into the next window: the counter restarts.
    monkeypatch.setattr(rl.time, "time", lambda: now + 61)
    assert _memory_count_and_ttl(key, 60) == (1, 59)
