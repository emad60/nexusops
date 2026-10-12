"""Provider construction — the only place a ``KEKProvider`` is ever created.

One configured name, one provider, **no chain**. The rules that make that more
than a convention:

* an unknown name, a missing name in production, or the deterministic test
  provider under a production configuration is a :class:`KEKConfigurationError`.
  In production that error is raised while configuration is validated, so the
  process exits instead of serving traffic with a key source the operator did not
  choose;
* a provider that is not ``production_safe`` cannot be selected in production even
  if it were somehow named — the refusal is a property of the provider, not a
  string comparison in one branch;
* an unconfigured provider outside production yields a :class:`ProviderSelection`
  with ``provider=None`` and a truthful status. The key-management paths then fail
  closed with ``KEK_CONFIG_INVALID``, while the rest of the platform keeps
  serving — which is the approved availability posture (§6.9);
* construction performs **no I/O**. Nothing here contacts Vault, so importing a
  module, running a migration or executing a management script never depends on a
  provider being up. Authentication happens lazily on the first real call.
"""

from __future__ import annotations

import threading

from app.core.config import Settings, get_settings
from app.services.kek import KEKConfigurationError, KEKError, KEKProvider
from app.services.kek.deterministic import DeterministicKEKProvider
from app.services.kek.vault_transit import VaultTransitKEKProvider

PROVIDER_NAMES: tuple[str, ...] = ("vault-transit", "test")


def build_kek_provider(settings: Settings | None = None) -> KEKProvider:
    """Return the configured provider, or raise naming exactly what is wrong."""
    settings = settings or get_settings()
    raw_name = (settings.kek_provider or "").strip().lower()
    if not raw_name:
        raise KEKConfigurationError(
            "KEK_PROVIDER is not set. Set it to 'vault-transit' (production) or "
            f"'test' (tests/development only). Known providers: {', '.join(PROVIDER_NAMES)}"
        )
    if raw_name not in PROVIDER_NAMES:
        raise KEKConfigurationError(
            f"KEK_PROVIDER={raw_name!r} is not a known provider "
            f"({', '.join(PROVIDER_NAMES)}). There is no fallback provider."
        )
    provider = _construct(settings, raw_name)
    if settings.is_production and not provider.production_safe:
        # Belt and braces: the settings validator refuses this combination too. A
        # second guard here means a future caller that builds settings differently
        # still cannot reach a non-production key source in production.
        raise KEKConfigurationError(
            f"provider {provider.name!r} is not production safe and cannot be used in "
            "production; configure 'vault-transit'"
        )
    return provider


def _construct(settings: Settings, name: str) -> KEKProvider:
    if name == "vault-transit":
        return VaultTransitKEKProvider(
            addr=settings.kek_vault_addr or "",
            transit_key=settings.kek_vault_transit_key or "",
            role_id=settings.kek_vault_role_id or "",
            secret_id=settings.kek_vault_secret_id or "",
            ca_bundle=settings.kek_vault_ca_bundle or None,
            timeout_seconds=settings.kek_vault_timeout_seconds,
            namespace=settings.kek_vault_namespace or None,
        )
    if name == "test":
        if settings.is_production:
            raise KEKConfigurationError(
                "the deterministic 'test' provider is refused in production; "
                "configure 'vault-transit'"
            )
        return DeterministicKEKProvider()
    raise KEKConfigurationError(
        f"unhandled provider {name!r}"
    )  # pragma: no cover - guarded above# --- process-wide accessor ----------------------------------------------------


_provider_lock = threading.Lock()
_provider: KEKProvider | None = None
_provider_error: KEKError | None = None


def get_kek_provider() -> KEKProvider:
    """The process-wide provider, built once.

    Cached so the adapter's HTTP client and its short-lived Vault token are reused
    across operations instead of re-authenticating per DEK. A configuration error
    is cached too: repeating a broken configuration on every request would turn a
    deployment mistake into a hot loop.
    """
    global _provider, _provider_error
    with _provider_lock:
        if _provider is not None:
            return _provider
        if _provider_error is not None:
            raise _provider_error
        try:
            _provider = build_kek_provider()
        except KEKError as exc:
            _provider_error = exc
            raise
        return _provider


def reset_kek_provider() -> None:
    """Drop the cached provider (tests, and any future configuration reload)."""
    global _provider, _provider_error
    with _provider_lock:
        _provider = None
        _provider_error = None


__all__ = [
    "PROVIDER_NAMES",
    "build_kek_provider",
    "get_kek_provider",
    "reset_kek_provider",
]
