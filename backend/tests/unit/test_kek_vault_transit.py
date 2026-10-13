"""The Vault Transit adapter's HTTP contract, without a Vault.

This module pins the *mapping* — which Vault answer becomes which named error, and
what must never appear in a log line. It is deliberately not the evidence that the
adapter works against Vault: a mock cannot tell you whether Transit accepts the
derivation context on ``rewrap``, whether the ciphertext prefix really is
``vault:v<N>:`` or whether a wrong context really fails authentication. That
evidence is in ``tests/integration/test_kek_vault_transit_live.py``, which runs
against a real Vault Transit key. What a mock *can* prove, and does here, is that
every response Vault is capable of returning is handled deliberately: a 403 is
never mistaken for a ciphertext mismatch, a timeout is never mistaken for success,
and a 500 never produces a plausible-looking envelope.

The transport is ``httpx.MockTransport``, so the exact request is inspected as well
as the response: the assertions include what the adapter *sends* (the derivation
context on every operation, one attempt per call, no body echoing).
"""

from __future__ import annotations

import base64
import json
import uuid

import httpx
import pytest
import structlog
from app.services.kek import (
    KEKConfigurationError,
    KEKContextMismatchError,
    KEKEnvelopeError,
    KEKUnauthorizedError,
    KEKUnavailableError,
    ProviderStatus,
    WrappedKey,
)
from app.services.kek.deterministic import _TEST_ROOT_KEY  # a public test constant, not a secret
from app.services.kek.vault_transit import VaultTransitKEKProvider
from cryptography.fernet import Fernet

ORG = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADDR = "https://vault.internal:8200"
TRANSIT_KEY = "nexusops-org-dek"
ROLE_ID = "role-id-not-a-secret-in-tests"
SECRET_ID = "secret-id-not-a-secret-in-tests"
TOKEN = "hvs.NOT-A-REAL-TOKEN"


class _Recorder:
    """A MockTransport that records every request and replays a scripted answer."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses
        self.requests: list[httpx.Request] = []
        self.bodies: list[dict[str, object]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.content:
            try:
                self.bodies.append(json.loads(request.content))
            except ValueError:  # pragma: no cover - the adapter always sends JSON
                self.bodies.append({})
        response = self._responses.pop(0) if len(self._responses) > 1 else self._responses[0]
        return response

    @property
    def paths(self) -> list[str]:
        return [request.url.path for request in self.requests]

    def tokens(self) -> list[str | None]:
        return [request.headers.get("X-Vault-Token") for request in self.requests]


def _login_ok(lease: int = 3600) -> httpx.Response:
    return httpx.Response(200, json={"auth": {"client_token": TOKEN, "lease_duration": lease}})


def _provider(recorder: _Recorder, **overrides: object) -> VaultTransitKEKProvider:
    kwargs: dict[str, object] = {
        "addr": ADDR,
        "transit_key": TRANSIT_KEY,
        "role_id": ROLE_ID,
        "secret_id": SECRET_ID,
        "transport": httpx.MockTransport(recorder.handler),
    }
    kwargs.update(overrides)
    return VaultTransitKEKProvider(**kwargs)  # type: ignore[arg-type]


async def test_wrap_sends_plaintext_once_and_returns_a_versioned_envelope() -> None:
    recorder = _Recorder(
        [_login_ok(), httpx.Response(200, json={"data": {"ciphertext": "vault:v3:AAAA"}})]
    )
    provider = _provider(recorder)
    dek = Fernet.generate_key()
    wrapped = await provider.wrap_dek(dek, _ctx())

    assert recorder.paths == ["/v1/auth/approle/login", f"/v1/transit/encrypt/{TRANSIT_KEY}"]
    assert wrapped.provider == "vault-transit"
    assert wrapped.key_id == TRANSIT_KEY
    assert wrapped.key_version == "3"
    assert wrapped.ciphertext == b"vault:v3:AAAA"
    assert recorder.bodies[1]["plaintext"] == base64.b64encode(dek).decode()


async def test_every_operation_carries_the_derivation_context() -> None:
    """encrypt, decrypt *and* rewrap: the binding must survive a rotation."""
    recorder = _Recorder(
        [
            _login_ok(),
            httpx.Response(200, json={"data": {"ciphertext": "vault:v3:AAAA"}}),
            httpx.Response(200, json={"data": {"plaintext": base64.b64encode(b"x" * 32).decode()}}),
            httpx.Response(200, json={"data": {"ciphertext": "vault:v4:BBBB"}}),
        ]
    )
    provider = _provider(recorder)
    context = _ctx()

    await provider.wrap_dek(Fernet.generate_key(), context)
    await provider.unwrap_dek(_wrapped(), context)
    await provider.rewrap_dek(_wrapped(), context)

    # Three data calls, every one of them with the same context, and no
    # associated_data anywhere: AAD does not exist on rewrap, which is why the
    # binding is the derivation context.
    assert recorder.paths[1:] == [
        f"/v1/transit/encrypt/{TRANSIT_KEY}",
        f"/v1/transit/decrypt/{TRANSIT_KEY}",
        f"/v1/transit/rewrap/{TRANSIT_KEY}",
    ]
    for body in recorder.bodies[1:]:
        assert body["context"] == context.provider_context()
        assert "associated_data" not in body


async def test_rewrap_returns_the_new_version_without_touching_the_dek() -> None:
    recorder = _Recorder(
        [_login_ok(), httpx.Response(200, json={"data": {"ciphertext": "vault:v4:BBBB"}})]
    )
    provider = _provider(recorder)
    rewrapped = await provider.rewrap_dek(_wrapped(), _ctx())

    assert rewrapped.key_version == "4"
    assert recorder.paths[-1] == f"/v1/transit/rewrap/{TRANSIT_KEY}"
    # The rewrap request carries ciphertext, never a plaintext DEK.
    assert set(recorder.bodies[-1]) == {"ciphertext", "context"}


async def test_the_client_token_is_attached_but_never_sent_to_the_wrong_place() -> None:
    recorder = _Recorder(
        [_login_ok(), httpx.Response(200, json={"data": {"ciphertext": "vault:v1:A"}})]
    )
    provider = _provider(recorder)
    await provider.wrap_dek(Fernet.generate_key(), _ctx())
    assert recorder.tokens() == [None, TOKEN], "login carries no token; the call carries it"
    # The AppRole credentials go to the login endpoint only.
    assert recorder.bodies[0] == {"role_id": ROLE_ID, "secret_id": SECRET_ID}
    assert set(recorder.bodies[1]) == {"plaintext", "context"}


async def test_the_token_is_reused_until_its_lease_is_nearly_over() -> None:
    recorder = _Recorder(
        [
            _login_ok(),
            httpx.Response(200, json={"data": {"ciphertext": "vault:v1:A"}}),
            httpx.Response(200, json={"data": {"ciphertext": "vault:v1:B"}}),
        ]
    )
    provider = _provider(recorder)
    await provider.wrap_dek(Fernet.generate_key(), _ctx())
    await provider.wrap_dek(Fernet.generate_key(), _ctx())
    assert recorder.paths.count("/v1/auth/approle/login") == 1, "a lease-valid token is reused"


async def test_a_failed_login_is_an_authorization_error_not_a_retry() -> None:
    recorder = _Recorder([httpx.Response(403, json={"errors": ["permission denied"]})])
    provider = _provider(recorder)
    with pytest.raises(KEKUnauthorizedError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())
    assert len(recorder.requests) == 1, "a refused identity is not retried"


async def test_a_login_response_without_a_token_is_malformed() -> None:
    recorder = _Recorder([httpx.Response(200, json={"auth": {}})])
    provider = _provider(recorder)
    with pytest.raises(KEKEnvelopeError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_a_denied_transit_permission_is_authorization() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(403, json={"errors": ["permission denied"]})])
    provider = _provider(recorder)
    with pytest.raises(KEKUnauthorizedError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_a_wrong_context_is_distinguished_from_a_denied_permission() -> None:
    """Transit reports both as 400; only the message tells them apart.

    Collapsing them would be the expensive mistake: "wrong organization" and "your
    policy is wrong" need opposite responses, and a retry cannot fix either.
    """
    recorder = _Recorder(
        [
            _login_ok(),
            httpx.Response(
                400, json={"errors": ["unable to decrypt: message authentication failed"]}
            ),
        ]
    )
    provider = _provider(recorder)
    with pytest.raises(KEKContextMismatchError):
        await provider.unwrap_dek(_wrapped(), _ctx())


async def test_a_derivation_misconfiguration_is_named() -> None:
    recorder = _Recorder(
        [
            _login_ok(),
            httpx.Response(400, json={"errors": ["encryption key derivation is required"]}),
        ]
    )
    provider = _provider(recorder)
    with pytest.raises(KEKConfigurationError) as raised:
        await provider.wrap_dek(Fernet.generate_key(), _ctx())
    assert "derived=true" in str(raised.value)


async def test_a_missing_transit_key_is_a_configuration_error() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(404, json={"errors": []})])
    provider = _provider(recorder)
    with pytest.raises(KEKConfigurationError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_a_server_error_is_unavailable_never_success() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(503, json={"errors": ["standby"]})])
    provider = _provider(recorder)
    with pytest.raises(KEKUnavailableError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_a_timeout_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/login"):
            return _login_ok()
        raise httpx.ConnectTimeout("timed out", request=request)

    provider = VaultTransitKEKProvider(
        addr=ADDR,
        transit_key=TRANSIT_KEY,
        role_id=ROLE_ID,
        secret_id=SECRET_ID,
        transport=httpx.MockTransport(handler),
        timeout_seconds=0.5,
    )
    with pytest.raises(KEKUnavailableError, match="timeout"):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_an_unreachable_vault_is_unavailable_on_login() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    provider = VaultTransitKEKProvider(
        addr=ADDR,
        transit_key=TRANSIT_KEY,
        role_id=ROLE_ID,
        secret_id=SECRET_ID,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KEKUnavailableError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_a_malformed_response_never_becomes_an_envelope() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(200, text="<html>not json</html>")])
    provider = _provider(recorder)
    with pytest.raises(KEKEnvelopeError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_an_empty_ciphertext_is_malformed() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(200, json={"data": {}})])
    provider = _provider(recorder)
    with pytest.raises(KEKEnvelopeError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_an_unknown_ciphertext_format_is_malformed() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(200, json={"data": {"ciphertext": "x"}})])
    provider = _provider(recorder)
    with pytest.raises(KEKEnvelopeError):
        await provider.wrap_dek(Fernet.generate_key(), _ctx())


async def test_a_decrypt_response_that_is_not_a_dek_is_refused() -> None:
    recorder = _Recorder(
        [_login_ok(), httpx.Response(200, json={"data": {"plaintext": "!!!not base64!!!"}})]
    )
    provider = _provider(recorder)
    with pytest.raises(KEKEnvelopeError):
        await provider.unwrap_dek(_wrapped(), _ctx())


async def test_an_envelope_from_another_key_is_refused_locally() -> None:
    recorder = _Recorder([_login_ok()])
    provider = _provider(recorder)
    foreign = WrappedKey(
        provider="vault-transit", key_id="some-other-key", key_version="1", ciphertext=b"vault:v1:A"
    )
    with pytest.raises(KEKEnvelopeError):
        await provider.unwrap_dek(foreign, _ctx())
    # Refused before the first request is sent: another key's ciphertext is never
    # handed to Transit as though it were ours.
    assert recorder.paths == []


async def test_tls_verification_is_not_disableable() -> None:
    with pytest.raises(KEKConfigurationError, match="https"):
        VaultTransitKEKProvider(
            addr="http://vault.internal:8200",
            transit_key=TRANSIT_KEY,
            role_id=ROLE_ID,
            secret_id=SECRET_ID,
        )


#: The shapes ``user:password@`` can take, one of them with a path prefix.
_CREDENTIALLED_ADDRS = [
    "https://deploy-bot@vault.internal:8200",
    "https://:hunter2@vault.internal:8200",
    "https://deploy-bot:hunter2@vault.internal:8200",
    "https://deploy-bot:hunter2@vault.internal:8200/team",
]


@pytest.mark.parametrize("addr", _CREDENTIALLED_ADDRS)
async def test_a_vault_address_with_embedded_credentials_is_refused(addr: str) -> None:
    """Refused at construction, so no base URL ever carries a credential (F4).

    Checked here as well as in settings validation because the adapter is
    constructible directly — tests, tooling, a future caller — and the address is
    the one input that reaches both an httpx base URL and the unreachable-error
    text.
    """
    with pytest.raises(KEKConfigurationError, match="must not embed a username or password"):
        VaultTransitKEKProvider(
            addr=addr, transit_key=TRANSIT_KEY, role_id=ROLE_ID, secret_id=SECRET_ID
        )


@pytest.mark.parametrize("addr", _CREDENTIALLED_ADDRS)
async def test_the_credentialled_address_is_not_echoed_in_the_error(addr: str) -> None:
    with pytest.raises(KEKConfigurationError) as raised:
        VaultTransitKEKProvider(
            addr=addr, transit_key=TRANSIT_KEY, role_id=ROLE_ID, secret_id=SECRET_ID
        )
    message = str(raised.value)
    assert "hunter2" not in message
    assert "deploy-bot" not in message
    assert "vault.internal" not in message


async def test_a_vault_path_prefix_reaches_the_request_unchanged() -> None:
    """A prefixed address is supported, and it is the base URL that carries it.

    httpx merges its base path with each request path, so a Vault behind
    ``https://vault.internal:8200/team`` is addressed without the adapter having to
    rewrite anything — and without TLS verification being relaxed for it.
    """
    recorder = _Recorder(
        [_login_ok(), httpx.Response(200, json={"data": {"ciphertext": "vault:v1:AAAA"}})]
    )
    provider = _provider(recorder, addr="https://vault.internal:8200/team")
    await provider.wrap_dek(b"0" * 32, _ctx())
    assert recorder.paths[0] == "/team/v1/auth/approle/login"
    assert provider._verify is True, "a path prefix must not touch TLS verification"


async def test_incomplete_configuration_is_refused_at_construction() -> None:
    with pytest.raises(KEKConfigurationError):
        VaultTransitKEKProvider(addr=ADDR, transit_key="", role_id=ROLE_ID, secret_id=SECRET_ID)


# --- health ------------------------------------------------------------------


async def test_health_reports_a_derived_key_as_ok() -> None:
    recorder = _Recorder(
        [
            _login_ok(),
            httpx.Response(200, json={"data": {"derived": True, "keys": {"1": 1, "2": 2}}}),
        ]
    )
    health = await _provider(recorder).health()
    assert health.status is ProviderStatus.OK
    assert health.operable
    assert "version 2" in health.detail


async def test_health_reports_a_key_without_derivation_as_invalid_configuration() -> None:
    """The provider is fine; the key cannot satisfy the binding. Not a retry."""
    recorder = _Recorder([_login_ok(), httpx.Response(200, json={"data": {"derived": False}})])
    health = await _provider(recorder).health()
    assert health.status is ProviderStatus.INVALID_CONFIGURATION
    assert not health.operable
    assert "derived=true" in health.detail


async def test_health_reports_denied_permissions_as_unauthorized() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(403, json={"errors": ["permission denied"]})])
    health = await _provider(recorder).health()
    assert health.status is ProviderStatus.UNAUTHORIZED


async def test_health_reports_an_unreachable_vault() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    provider = VaultTransitKEKProvider(
        addr=ADDR,
        transit_key=TRANSIT_KEY,
        role_id=ROLE_ID,
        secret_id=SECRET_ID,
        transport=httpx.MockTransport(handler),
    )
    health = await provider.health()
    assert health.status is ProviderStatus.UNREACHABLE
    assert not health.operable


async def test_health_reports_a_missing_key_as_invalid_configuration() -> None:
    recorder = _Recorder([_login_ok(), httpx.Response(404, json={"errors": ["no such key"]})])
    health = await _provider(recorder).health()
    assert health.status is ProviderStatus.INVALID_CONFIGURATION


# --- what must never be logged ------------------------------------------------


async def test_neither_the_token_nor_the_dek_nor_the_secret_id_is_logged() -> None:
    """Every failing call, with the log stream captured.

    The token travels in a header on every call, the DEK travels in one body and the
    AppRole secret in another, so all three are plausible accidental log fields.
    """
    dek = Fernet.generate_key()
    recorder = _Recorder(
        [
            _login_ok(),
            httpx.Response(
                400, json={"errors": ["unable to decrypt: message authentication failed"]}
            ),
        ]
    )
    provider = _provider(recorder)
    with structlog.testing.capture_logs() as logs:
        with pytest.raises(KEKContextMismatchError):
            await provider.wrap_dek(dek, _ctx())
    rendered = str(logs)
    assert TOKEN not in rendered
    assert SECRET_ID not in rendered
    assert ROLE_ID not in rendered
    assert dek.decode() not in rendered
    assert base64.b64encode(dek).decode() not in rendered
    # A health failure too: the same rule applies to the reporting path.
    unhealthy = _Recorder(
        [_login_ok(), httpx.Response(403, json={"errors": ["permission denied"]})]
    )
    with structlog.testing.capture_logs() as logs:
        await _provider(unhealthy).health()
    assert TOKEN not in str(logs)
    # And the probe itself only *reads* key metadata: a health check must never
    # wrap, unwrap or rewrap anything.
    assert unhealthy.paths == [
        "/v1/auth/approle/login",
        f"/v1/transit/keys/{TRANSIT_KEY}",
    ]


async def test_the_test_root_constant_is_not_reachable_from_the_adapter() -> None:
    """The deterministic provider's fixture key must not be a Vault credential.

    A two-line guard, but it makes the boundary explicit: the adapter's module has
    no reference to the test root, so an adapter that "worked" offline by falling
    back to it is not a thing that can be written by accident.
    """
    from app.services.kek import vault_transit

    assert _TEST_ROOT_KEY not in vars(vault_transit).values()


def _ctx():
    from app.services.kek import EncryptionContext

    return EncryptionContext(org_id=ORG, dek_generation=1)


def _wrapped() -> WrappedKey:
    return WrappedKey(
        provider="vault-transit", key_id=TRANSIT_KEY, key_version="3", ciphertext=b"vault:v3:AAAA"
    )
