"""Provider health, cached, for the readiness surface.

Health is the one place a provider is touched on a schedule rather than by a user
action, so it has two jobs and one restraint:

* **report the truth** — reachable, unreachable, unauthorized, and invalid
  configuration are four different operator actions and must never be collapsed
  into a boolean;
* **not become load** — the verdict is cached for ``KEK_HEALTH_CACHE_SECONDS``, and
  the probe uses the **process-wide provider** (``get_kek_provider``) rather than
  constructing one. Building an adapter per readiness probe would leak a client and
  its connection pool on every probe, and it would also mean the probe exercised a
  different identity from the one that unwraps real DEKs. The cache is keyed by
  provider name, because the platform has exactly one provider of a given name by
  construction (one named selection, no fallback chain). What is cached is only the
  verdict: no key material, no DEK, no ciphertext, not even a wrapped one. A health
  probe asks the provider to describe its key; it never asks it to wrap or unwrap
  anything;
* **not fail the process's readiness** — the platform keeps serving everything that
  does not need a DEK while key management is down (approved posture,
  phase5-design.md §6.9). The caller decides how to present it; this module only
  reports.
"""

from __future__ import annotations

import time

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.kek import KEKError, KEKProvider, ProviderHealth, ProviderStatus
from app.services.kek.factory import get_kek_provider

log = get_logger("nexusops.kek.health")

_cached: dict[str, tuple[float, ProviderHealth]] = {}


def reset_health_cache() -> None:
    """Drop every cached verdict (tests, and any future configuration reload)."""
    _cached.clear()


async def provider_health(
    *, settings: Settings | None = None, provider: KEKProvider | None = None
) -> ProviderHealth:
    """The configured provider's health, at most one probe per cache window."""
    settings = settings or get_settings()
    ttl = settings.kek_health_cache_seconds
    now = time.monotonic()

    if provider is None:
        if not (settings.kek_provider or "").strip():
            # Unconfigured, and that is a configuration answer, not a probe — and
            # never a reason to substitute a different provider.
            return ProviderHealth(
                status=ProviderStatus.DISABLED,
                provider="none",
                detail=(
                    "KEK_PROVIDER is not configured; key-management operations are unavailable"
                ),
            )
        try:
            provider = get_kek_provider()
        except KEKError as exc:
            # Misconfiguration is cached by the factory (so a broken deployment
            # cannot become a hot loop) and reported as its own state: the operator
            # fixes configuration, they do not retry.
            return ProviderHealth(
                status=ProviderStatus.INVALID_CONFIGURATION,
                provider=str(settings.kek_provider),
                detail=str(exc),
            )

    name = str(getattr(provider, "name", "unknown"))
    if ttl > 0:
        cached = _cached.get(name)
        if cached is not None and now - cached[0] < ttl:
            return cached[1]

    try:
        health = await provider.health()
    except Exception as exc:
        # An adapter that raises has told us it cannot operate; the class name is
        # enough for an operator, and nothing from the exception is echoed (it could
        # carry a URL with credentials).
        health = ProviderHealth(
            ProviderStatus.UNREACHABLE,
            name,
            f"provider probe raised {type(exc).__name__}",
        )
    if not health.operable:
        log.warning(
            "kek_provider_unhealthy",
            provider=health.provider,
            status=str(health.status),
            detail=health.detail,
        )
    if ttl > 0:
        _cached[name] = (now, health)
    return health


__all__ = ["provider_health", "reset_health_cache"]
