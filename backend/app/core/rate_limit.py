"""Redis-backed fixed-window rate limiting as a FastAPI dependency factory."""

from __future__ import annotations

from fastapi import Request

from app.core.errors import RateLimited
from app.core.logging import get_logger
from app.core.redis_client import get_redis

log = get_logger("nexusops.rate_limit")


def client_ip(request: Request) -> str:
    """Best-effort client IP; honours X-Forwarded-For from trusted proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Rightmost entry is added by our own nginx; leftmost is spoofable,
        # so use the last hop value.
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, limit: int, window_seconds: int):  # type: ignore[no-untyped-def]
    """Return a dependency enforcing *limit* requests per window per IP."""

    async def _dependency(request: Request) -> None:
        key = f"nx:rl:{name}:{client_ip(request)}"
        try:
            redis = get_redis()
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window_seconds)
            ttl = await redis.ttl(key)
        except Exception:  # Redis unavailable → fail open, log loudly
            log.warning("rate_limiter_unavailable", limiter=name)
            return
        if count > limit:
            retry_after = max(ttl, 1)
            raise RateLimited(
                f"Rate limit exceeded. Try again in {retry_after}s.",
                retry_after=retry_after,
            )

    return _dependency


# Pre-built limiters for the sensitive endpoints.
auth_limiter = lambda: rate_limit("auth", 10, 60)  # noqa: E731 - 10/min per IP
register_limiter = lambda: rate_limit("register", 5, 300)  # noqa: E731 - 5/5min per IP
token_refresh_limiter = lambda: rate_limit("refresh", 30, 60)  # noqa: E731
expensive_op_limiter = lambda: rate_limit("expensive", 20, 60)  # noqa: E731
