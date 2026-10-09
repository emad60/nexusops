"""Redis-backed fixed-window rate limiting as a FastAPI dependency factory.

Auth-sensitive limiters (login / register / refresh) are *fail closed*: when
Redis is unavailable they fall back to an in-process fixed-window counter so
brute-force throttling never silently disappears. General endpoints keep the
availability-friendly fail-open behaviour.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request

from app.core.client_ip import resolve_client_ip
from app.core.errors import RateLimited
from app.core.logging import get_logger
from app.core.redis_client import get_redis

log = get_logger("nexusops.rate_limit")

# In-process fallback state for fail-closed limiters: key -> [bucket, count].
# Approximate across workers (each process counts its own share), which is
# still far safer than having no throttle at all during a Redis outage.
_memory_windows: dict[str, list[int]] = {}
_MEMORY_MAX_KEYS = 10_000


def client_ip(request: Request) -> str:
    """Best-effort client IP; honours X-Forwarded-For from trusted proxies.

    Delegates to the chain-aware resolver — the naive "rightmost entry" read
    is wrong behind more than one proxy hop (e.g. Cloudflare → host nginx →
    edge): the rightmost entry is then the edge's docker-network peer, which
    would collapse every client into one rate-limit bucket.
    """
    return resolve_client_ip(request)


def _memory_count_and_ttl(key: str, window_seconds: int) -> tuple[int, int]:
    """Fixed-window counter backed by process memory. Returns (count, ttl)."""
    now = int(time.time())
    bucket = now // window_seconds
    entry = _memory_windows.get(key)
    if entry is None or entry[0] != bucket:
        if len(_memory_windows) >= _MEMORY_MAX_KEYS:
            # Drop stale buckets so the fallback state cannot grow unbounded.
            stale = [k for k, v in _memory_windows.items() if v[0] != bucket]
            for k in stale:
                _memory_windows.pop(k, None)
        entry = [bucket, 0]
        _memory_windows[key] = entry
    entry[1] += 1
    ttl = window_seconds - (now % window_seconds)
    return entry[1], max(ttl, 1)


async def _enforce(
    *, key: str, name: str, limit: int, window_seconds: int, fail_closed: bool
) -> None:
    """Shared fixed-window accounting for every limiter in this module."""
    try:
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        ttl = await redis.ttl(key)
    except Exception:
        if not fail_closed:
            log.warning("rate_limiter_unavailable", limiter=name)
            return
        # Auth/enrollment endpoints: degrade to the in-process limiter, never open.
        count, ttl = _memory_count_and_ttl(key, window_seconds)
    if count > limit:
        retry_after = max(ttl, 1)
        raise RateLimited(
            f"Rate limit exceeded. Try again in {retry_after}s.",
            retry_after=retry_after,
        )


def rate_limit(
    name: str, limit: int, window_seconds: int, *, fail_closed: bool = False
) -> Callable[[Request], Awaitable[None]]:
    """Return a dependency enforcing *limit* requests per window per IP.

    With ``fail_closed=True`` a Redis outage no longer disables the throttle:
    an in-process fixed-window limiter takes over (per-worker approximation).
    """

    async def _dependency(request: Request) -> None:
        await _enforce(
            key=f"nx:rl:{name}:{client_ip(request)}",
            name=name,
            limit=limit,
            window_seconds=window_seconds,
            fail_closed=fail_closed,
        )

    return _dependency


def node_rate_limit(
    name: str, limit: int, window_seconds: int, *, fail_closed: bool = True
) -> Callable[[Request], Awaitable[None]]:
    """Return a dependency keyed on the **authenticated node**, not the IP.

    A fleet behind one NAT should not share a single 600/min bucket: after
    ``require_server`` has resolved the token, the bucket key is the node id, so
    each machine gets its own allowance. The identity comes exclusively from
    ``request.state.agent_server_id``, which only ``require_server`` sets after a
    token lookup — an unauthenticated caller can never choose or consume another
    node's bucket. When that state is absent (the dependency is used on a route
    with no resolved node, or runs before authentication), the key falls back to
    the client IP so the route is never unthrottled.

    Fail-closed by default: losing Redis must not remove agent throttling.
    """

    async def _dependency(request: Request) -> None:
        node_id = getattr(request.state, "agent_server_id", None)
        identity = f"node:{node_id}" if node_id else f"ip:{client_ip(request)}"
        await _enforce(
            key=f"nx:rl:{name}:{identity}",
            name=name,
            limit=limit,
            window_seconds=window_seconds,
            fail_closed=fail_closed,
        )

    return _dependency


# Pre-built limiters for the sensitive endpoints. Auth-facing limiters fail
# closed: a Redis outage must not silently remove brute-force throttling.
auth_limiter = lambda: rate_limit("auth", 10, 60, fail_closed=True)  # noqa: E731 - 10/min per IP
register_limiter = lambda: rate_limit("register", 5, 300, fail_closed=True)  # noqa: E731 - 5/5min per IP
token_refresh_limiter = lambda: rate_limit("refresh", 30, 60, fail_closed=True)  # noqa: E731
expensive_op_limiter = lambda: rate_limit("expensive", 20, 60)  # noqa: E731
