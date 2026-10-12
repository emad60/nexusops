"""Provider health on the readiness surface, seen through the API.

The approved posture has two halves and both are asserted here: readiness keeps an
instance in rotation on database and Redis alone, and key-management status is
*reported* — with named, sanitized detail — so an operator can act on it without a
working key provider taking the whole API down.

The test also checks the negative that matters most on a public endpoint: a provider
that is misconfigured or unreachable must not turn the probe body into a
configuration dump. No address, no transit key name, no role or secret id, no
token — a status word and nothing else.
"""

from __future__ import annotations

import pytest
from app.services.kek import ProviderHealth, ProviderStatus

pytestmark = pytest.mark.integration

VAULT_ADDR = "https://vault.internal:8200"
TRANSIT_KEY = "nexusops-org-dek"
SECRET_ID = "secret-id-that-must-never-be-rendered"
TOKEN = "hvs.TOKEN-THAT-MUST-NEVER-BE-RENDERED"


class _UnhealthyProvider:
    """A provider that answers truthfully and is never asked to do more."""

    name = "vault-transit"
    production_safe = True

    def __init__(self, status: ProviderStatus, detail: str) -> None:
        self._health = ProviderHealth(status, self.name, detail)

    async def health(self) -> ProviderHealth:
        return self._health


@pytest.fixture(autouse=True)
def _clear_health_cache() -> None:
    """Every test observes its own provider, not a verdict left by the last one."""
    from app.services.kek import health as kek_health

    kek_health.reset_health_cache()
    yield
    kek_health.reset_health_cache()


async def _ready(client) -> dict:
    response = await client.get("/ready")
    assert response.status_code == 200, response.text
    return response.json()


async def test_readiness_reports_the_configured_provider_as_ok(client) -> None:
    """The suite selects the deterministic provider explicitly, so it is healthy."""
    body = await _ready(client)
    assert body["status"] == "ready"
    assert body["components"]["key_management"] == "ok"


async def test_an_unreachable_provider_does_not_unready_the_instance(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole point of reporting instead of gating: the API keeps serving."""
    from app.services.kek import health as kek_health

    monkeypatch.setattr(
        kek_health,
        "get_kek_provider",
        lambda: _UnhealthyProvider(
            ProviderStatus.UNREACHABLE, f"Vault is unreachable at {VAULT_ADDR}"
        ),
    )
    body = await _ready(client)
    assert body["status"] == "ready", "a key provider outage must not pull the API out"
    assert body["components"]["database"] == "ok"
    assert body["components"]["key_management"] == "unreachable"


@pytest.mark.parametrize(
    "status",
    [
        ProviderStatus.UNAUTHORIZED,
        ProviderStatus.INVALID_CONFIGURATION,
        ProviderStatus.DISABLED,
    ],
)
async def test_every_provider_state_is_distinguishable(
    client, monkeypatch: pytest.MonkeyPatch, status: ProviderStatus
) -> None:
    """Four states, four operator actions — never collapsed into one boolean."""
    from app.services.kek import health as kek_health

    monkeypatch.setattr(
        kek_health,
        "get_kek_provider",
        lambda: _UnhealthyProvider(status, "sanitized detail"),
    )
    body = await _ready(client)
    assert body["components"]["key_management"] == str(status)
    assert body["status"] == "ready"


async def test_the_readiness_body_never_carries_configuration_or_credentials(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A probe is unauthenticated in most deployments; it must leak nothing."""
    from app.services.kek import health as kek_health

    monkeypatch.setattr(
        kek_health,
        "get_kek_provider",
        lambda: _UnhealthyProvider(
            ProviderStatus.UNAUTHORIZED,
            f"AppRole login refused for {TRANSIT_KEY} at {VAULT_ADDR}",
        ),
    )
    response = await client.get("/ready")
    text = response.text
    assert VAULT_ADDR not in text
    assert TRANSIT_KEY not in text
    assert SECRET_ID not in text
    assert TOKEN not in text
    # Only the status word is published, not the provider's explanation.
    assert response.json()["components"]["key_management"] == "unauthorized"


async def test_liveness_stays_a_single_cheap_field(client) -> None:
    """Liveness must not acquire a provider dependency by accident."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
