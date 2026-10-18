"""Provider selection: one named provider, no fallback, and a hard production refusal.

The rule the whole key-management seam rests on is that a provider is *chosen* —
never detected, never defaulted, never reached because something else failed. That
rule is enforced in three places (settings validation at startup, the factory, and
the provider's own ``production_safe`` flag), and this module asserts each of them
separately, because a guard that exists in only one place is a guard one refactor
away from not existing.

It also covers the availability posture the design approved: outside production an
*unconfigured* provider is allowed to be unavailable, and says so truthfully,
instead of preventing a process from serving everything that does not need a DEK.
"""

from __future__ import annotations

import pytest
from app.services.kek import (
    KEKConfigurationError,
    ProviderStatus,
)
from app.services.kek import health as kek_health
from app.services.kek.deterministic import DeterministicKEKProvider
from app.services.kek.factory import (
    PROVIDER_NAMES,
    build_kek_provider,
    get_kek_provider,
    reset_kek_provider,
)
from app.services.kek.vault_transit import VaultTransitKEKProvider
from pydantic import ValidationError

VAULT_CONFIG = {
    "kek_vault_addr": "https://vault.internal:8200",
    "kek_vault_transit_key": "nexusops-org-dek",
    "kek_vault_role_id": "role-id-in-a-test",
    "kek_vault_secret_id": "secret-id-in-a-test",
}


@pytest.fixture(autouse=True)
def _clean_provider_cache() -> None:
    """No test may see a provider another test built."""
    reset_kek_provider()
    kek_health.reset_health_cache()
    yield
    reset_kek_provider()
    kek_health.reset_health_cache()


# --- settings validation (the startup path) -----------------------------------


def _settings(**overrides: object):
    from app.core.config import Settings

    # jwt_secret / encryption_key come from the process environment, which the test
    # bootstrap has already pinned; only the key-management fields vary here.
    # ``acme_directory`` is pinned to a valid value for the environment under test:
    # 5.3 made production require an explicit directory, and this module is about
    # the KEK choice, so it must not fail on an unrelated validator first.
    overrides.setdefault(
        "acme_directory",
        "production" if overrides.get("environment") == "production" else "staging",
    )
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_production_requires_a_provider() -> None:
    with pytest.raises(ValidationError, match="KEK_PROVIDER is required in production"):
        _settings(environment="production", kek_provider="")


def test_production_refuses_the_deterministic_provider() -> None:
    """A test fixture must be unreachable by configuration, not by convention."""
    with pytest.raises(ValidationError, match="refused in production"):
        _settings(environment="production", kek_provider="test")


def test_development_may_select_the_deterministic_provider_explicitly() -> None:
    settings = _settings(environment="development", kek_provider="TEST")
    assert settings.kek_provider == "test", "the name is normalized, not pattern-matched"


def test_an_unknown_provider_is_refused_everywhere() -> None:
    with pytest.raises(ValidationError, match="no fallback provider"):
        _settings(kek_provider="vault")
    with pytest.raises(ValidationError, match="no fallback provider"):
        _settings(environment="production", kek_provider="aws-kms")


def test_a_half_configured_vault_is_a_startup_error() -> None:
    """Better to fail at deploy time than at the first unwrap of a real DEK."""
    with pytest.raises(ValidationError) as raised:
        _settings(kek_provider="vault-transit", **{**VAULT_CONFIG, "kek_vault_secret_id": None})
    assert "KEK_VAULT_SECRET_ID" in str(raised.value)


def test_vault_must_be_https() -> None:
    with pytest.raises(ValidationError, match="must use https"):
        _settings(
            kek_provider="vault-transit",
            **{**VAULT_CONFIG, "kek_vault_addr": "http://vault.internal:8200"},
        )


# --- F4: no credentials in the Vault address ----------------------------------

#: Every shape ``user:password@`` can take, including one that also carries a path
#: prefix — the credentials are what disqualify the address, not the path.
_CREDENTIALLED_ADDRS = [
    "https://deploy-bot@vault.internal:8200",  # username only
    "https://:hunter2@vault.internal:8200",  # password only
    "https://deploy-bot:hunter2@vault.internal:8200",  # both
    "https://deploy-bot:hunter2@vault.internal:8200/team",  # both, with a prefix
]


@pytest.mark.parametrize("addr", _CREDENTIALLED_ADDRS)
def test_vault_addr_must_not_embed_credentials(addr: str) -> None:
    """Vault access here is AppRole; an HTTP credential is one nothing consumes.

    Worse than useless: the address is a base URL, so an HTTP client drops the
    userinfo silently — leaving a password in a compose file, a shell history and a
    startup log line, protecting nothing.
    """
    with pytest.raises(ValidationError, match="must not embed a username or password"):
        _settings(kek_provider="vault-transit", **{**VAULT_CONFIG, "kek_vault_addr": addr})


@pytest.mark.parametrize("addr", _CREDENTIALLED_ADDRS)
def test_the_vault_addr_error_never_echoes_the_address_or_its_credentials(addr: str) -> None:
    """A validation error is startup output — the least private place there is.

    The field validator controls its own message, and ``hide_input_in_errors`` keeps
    pydantic from appending the rejected input, so neither the URL nor either
    credential appears in the text.
    """
    with pytest.raises(ValidationError) as raised:
        _settings(kek_provider="vault-transit", **{**VAULT_CONFIG, "kek_vault_addr": addr})
    message = str(raised.value)
    assert "hunter2" not in message
    assert "deploy-bot" not in message
    assert "vault.internal" not in message, "the host is part of the input, not of the report"
    # The message still says which variable is wrong and how to fix it.
    assert "KEK_VAULT_ADDR" in message
    assert "KEK_VAULT_ROLE_ID" in message and "KEK_VAULT_SECRET_ID" in message


def test_a_vault_path_prefix_is_still_a_valid_address() -> None:
    """Only the authority is inspected — a prefix (and its port) survives untouched."""
    settings = _settings(
        kek_provider="vault-transit",
        **{**VAULT_CONFIG, "kek_vault_addr": "https://vault.internal:8200/team"},
    )
    assert settings.kek_vault_addr == "https://vault.internal:8200/team"


def test_a_complete_vault_configuration_validates_in_production() -> None:
    settings = _settings(environment="production", kek_provider="vault-transit", **VAULT_CONFIG)
    assert settings.is_production
    assert settings.kek_vault_transit_key == "nexusops-org-dek"


# --- the factory --------------------------------------------------------------


def test_the_factory_builds_the_named_provider() -> None:
    provider = build_kek_provider(_settings(kek_provider="test", environment="development"))
    assert isinstance(provider, DeterministicKEKProvider)
    assert provider.name == "test"


def test_the_factory_builds_the_vault_adapter() -> None:
    provider = build_kek_provider(_settings(kek_provider="vault-transit", **VAULT_CONFIG))
    assert isinstance(provider, VaultTransitKEKProvider)
    assert provider.name == "vault-transit"
    assert provider.production_safe is True


def test_the_factory_refuses_an_unset_provider() -> None:
    with pytest.raises(KEKConfigurationError, match="KEK_PROVIDER is not set"):
        build_kek_provider(_settings(kek_provider=""))


def test_the_factory_refuses_an_unknown_name_past_the_validator() -> None:
    """The second guard, reached directly.

    Settings validation rejects an unknown name first (asserted above), but
    ``model_copy`` bypasses validation — the path a caller with its own settings
    construction takes. The factory must refuse on its own.
    """
    from app.core.config import get_settings

    sneaky = get_settings().model_copy(update={"kek_provider": "gcp-kms"})
    with pytest.raises(KEKConfigurationError, match="not a known provider"):
        build_kek_provider(sneaky)


def test_the_factory_refuses_the_deterministic_provider_in_production_even_if_named() -> None:
    """Production election is refused by the factory, not only by the validator."""
    from app.core.config import get_settings

    sneaky = get_settings().model_copy(update={"environment": "production", "kek_provider": "test"})
    with pytest.raises(KEKConfigurationError, match="refused in production"):
        build_kek_provider(sneaky)


def test_provider_names_are_the_two_the_design_approves() -> None:
    assert PROVIDER_NAMES == ("vault-transit", "test")


# --- selection as health sees it ----------------------------------------------


def test_an_unconfigured_provider_is_unavailable_not_a_fallback() -> None:
    """An unconfigured key path fails closed and says so — it never picks one."""
    with pytest.raises(KEKConfigurationError, match="KEK_PROVIDER is not set"):
        build_kek_provider(_settings(kek_provider=""))


def _unbuildable() -> object:
    """Settings that name Vault without its credentials.

    Built with ``model_copy`` on purpose: this is the *runtime* shape of a broken
    configuration (validation would have stopped a real deployment at startup), and
    selection must still answer truthfully instead of raising into readiness.
    """
    from app.core.config import get_settings

    return get_settings().model_copy(
        update={
            "kek_provider": "vault-transit",
            "kek_vault_addr": None,
            "kek_vault_transit_key": None,
            "kek_vault_role_id": None,
            "kek_vault_secret_id": None,
        }
    )


async def test_an_unbuildable_vault_is_not_quietly_replaced_by_the_test_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The failure mode the no-fallback rule exists for.

    Naming Vault and failing to configure it must never yield the deterministic
    provider: that would silently wrap real DEKs with a public test constant. Health
    reports the misconfiguration; the key path refuses.
    """
    settings = _unbuildable()
    # Both namespaces: health resolves the settings, and the factory builds from
    # whatever settings it is handed.
    monkeypatch.setattr("app.services.kek.health.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.kek.factory.get_settings", lambda: settings)
    health = await kek_health.provider_health()
    assert health.status is ProviderStatus.INVALID_CONFIGURATION
    assert health.provider == "vault-transit"
    assert "KEK_VAULT_ADDR" in health.detail
    with pytest.raises(KEKConfigurationError):
        get_kek_provider()


async def test_an_unconfigured_provider_reports_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core.config import get_settings

    settings = get_settings().model_copy(update={"kek_provider": ""})
    monkeypatch.setattr("app.services.kek.health.get_settings", lambda: settings)
    health = await kek_health.provider_health()
    assert health.status is ProviderStatus.DISABLED
    assert not health.operable
    assert health.provider == "none"


async def test_health_probes_the_cached_provider_and_dials_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One process-wide provider, built once and reused by every probe.

    Building an adapter per probe would leak an HTTP client and its pool, and would
    probe a different identity from the one that unwraps real DEKs.
    """
    from app.core.config import get_settings
    from app.services.kek import factory

    # A Vault endpoint that refuses immediately, so the probe is a real attempt
    # rather than a DNS wait.
    settings = get_settings().model_copy(
        update={
            "kek_provider": "vault-transit",
            **VAULT_CONFIG,
            "kek_vault_addr": "https://127.0.0.1:1",
        }
    )
    monkeypatch.setattr("app.services.kek.health.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.kek.factory.get_settings", lambda: settings)

    built: list[str] = []
    real = factory.build_kek_provider

    def counting(inner=None):
        built.append("build")
        return real(inner)

    monkeypatch.setattr(factory, "build_kek_provider", counting)
    first = await kek_health.provider_health()
    second = await kek_health.provider_health()
    assert isinstance(get_kek_provider(), VaultTransitKEKProvider)
    assert built == ["build"], "the probe reused the cached provider instead of building one"
    assert first.status is ProviderStatus.UNREACHABLE, "a Vault that is not there is not ok"
    assert second.status is ProviderStatus.UNREACHABLE


# --- the process-wide accessor -------------------------------------------------


def test_the_cached_provider_is_built_once(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.kek import factory

    built: list[str] = []
    real = factory.build_kek_provider

    def counting(settings=None):
        built.append("build")
        return real(settings)

    monkeypatch.setattr(factory, "build_kek_provider", counting)
    first = get_kek_provider()
    second = get_kek_provider()
    assert first is second
    assert built == ["build"], "a provider is built once per process"

    reset_kek_provider()
    third = get_kek_provider()
    assert third is not first
    assert len(built) == 2


def test_a_broken_configuration_is_not_re_evaluated_on_every_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deployment mistake must not become a per-request hot loop."""
    from app.services.kek import factory

    attempts: list[str] = []
    real = factory.build_kek_provider

    def always_broken(settings=None):
        attempts.append("attempt")
        raise KEKConfigurationError("KEK_PROVIDER is not set")

    monkeypatch.setattr(factory, "build_kek_provider", always_broken)
    assert real is not always_broken
    for _ in range(3):
        with pytest.raises(KEKConfigurationError):
            get_kek_provider()
    assert len(attempts) == 1, "the error is cached alongside the provider"


# --- health reporting ----------------------------------------------------------


async def test_health_reports_the_deterministic_provider_as_ok_but_not_production_safe() -> None:
    health = await kek_health.provider_health(provider=DeterministicKEKProvider())
    assert health.status is ProviderStatus.OK
    assert "not production safe" in health.detail


class _RaisingProvider:
    """A provider whose probe itself explodes — the worst case for readiness."""

    name = "vault-transit"
    production_safe = True

    async def health(self):
        raise RuntimeError("connection pool is closed")


async def test_a_probe_that_raises_never_breaks_the_readiness_response() -> None:
    health = await kek_health.provider_health(provider=_RaisingProvider())
    assert health.status is ProviderStatus.UNREACHABLE
    assert health.provider == "vault-transit"
    # The message names the failure class and nothing else: an exception body can
    # carry a URL with credentials in it.
    assert health.detail == "provider probe raised RuntimeError"


async def test_health_is_cached_between_probes() -> None:
    """Readiness probes are frequent; the provider must not be dialled per probe."""
    from app.core.config import get_settings

    class _Counting(DeterministicKEKProvider):
        probes = 0

        async def health(self):
            _Counting.probes += 1
            return await super().health()

    settings = get_settings().model_copy(update={"kek_health_cache_seconds": 60})
    for _ in range(4):
        await kek_health.provider_health(settings=settings, provider=_Counting())
    assert _Counting.probes == 1
