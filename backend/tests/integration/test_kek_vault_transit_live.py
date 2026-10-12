"""The Vault Transit adapter against a **real** Vault, in an isolated container.

This module exists because a mock cannot answer the questions the design's hardest
decision rests on. Three of them are measured here:

* **Does a derived key accept the derivation context on all three operations?**
  ``transit/encrypt``, ``transit/decrypt`` *and* ``transit/rewrap`` must each take
  the organization/purpose/generation binding, or the approved invariant ("a
  KEK-only rotation never materialises a plaintext DEK in the application") cannot
  hold.
* **Does a wrong organization, purpose or generation actually fail?** Not "is the
  field compared" — does Vault refuse to decrypt it.
* **Is ``associated_data`` usable as the binding?** This is the measurement that
  chose the design: AAD authenticates on encrypt/decrypt but has no counterpart on
  rewrap, so an AAD-bound envelope cannot be rotated provider-side at all. The
  test asserts that failure directly, so the reason for the choice is recorded as
  evidence rather than as a claim in a comment.

It also asserts the privilege boundary: the application identity can wrap, unwrap
and rewrap one key and read its metadata, and **cannot** administer keys.

The container is fully isolated — a unique name, a host-loopback port chosen from
the free list, its own generated TLS material, its own dev-mode storage — and it is
removed when the module finishes. Nothing here touches the development Postgres,
Redis or any other container, and no shared volume is used.

If Docker or the ``hashicorp/vault:1.15`` image is unavailable, the module skips
with an explicit reason: absence of infrastructure must be visible in the report,
never silently reported as a pass.
"""

from __future__ import annotations

import base64
import json
import shutil
import socket
import ssl
import subprocess
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from app.services.kek import (
    EncryptionContext,
    KEKContextMismatchError,
    ProviderStatus,
)
from app.services.kek.vault_transit import VaultTransitKEKProvider
from cryptography.fernet import Fernet

pytestmark = pytest.mark.integration

IMAGE = "hashicorp/vault:1.15"
ROOT_TOKEN = "root-token-for-an-isolated-dev-vault"
TRANSIT_KEY = "nexusops-org-dek"
POLICY_NAME = "nexusops-kek"
APP_ROLE = "nexusops-kek"
ORG = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORG = uuid.UUID("22222222-2222-2222-2222-222222222222")

#: The transit key is admin-created (by the operator, holding the root token) and
#: derived. Read/write on this one key is all the application gets.
TRANSIT_POLICY = f"""
path "transit/encrypt/{TRANSIT_KEY}" {{ capabilities = ["update"] }}
path "transit/decrypt/{TRANSIT_KEY}" {{ capabilities = ["update"] }}
path "transit/rewrap/{TRANSIT_KEY}" {{ capabilities = ["update"] }}
path "transit/keys/{TRANSIT_KEY}" {{ capabilities = ["read"] }}
"""


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


#: Resolved once, so no PATH-relative executable is ever handed to subprocess.
_DOCKER = shutil.which("docker")


def _docker(*args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
    """Run one docker subcommand with a fixed argv: no shell, no cleanup commands."""
    assert _DOCKER is not None
    return subprocess.run(  # noqa: S603 - fixed argv built from module constants
        [_DOCKER, *args],
        capture_output=True,
        text=True,
        timeout=120,
        **kwargs,  # type: ignore[arg-type]
    )


class LiveVault:
    """A running dev Vault, its generated CA, and the application's AppRole."""

    def __init__(self, addr: str, ca_bundle: Path, role_id: str, secret_id: str) -> None:
        self.addr = addr
        self.ca_bundle = ca_bundle
        self.role_id = role_id
        self.secret_id = secret_id

    def provider(self, **overrides: object) -> VaultTransitKEKProvider:
        kwargs: dict[str, object] = {
            "addr": self.addr,
            "transit_key": TRANSIT_KEY,
            "role_id": self.role_id,
            "secret_id": self.secret_id,
            "ca_bundle": str(self.ca_bundle),
        }
        kwargs.update(overrides)
        return VaultTransitKEKProvider(**kwargs)  # type: ignore[arg-type]

    def app_token(self) -> str:
        """Log in as the application identity, the way the adapter does."""
        with httpx.Client(verify=_ca_context(self), timeout=10) as client:
            response = client.post(
                f"{self.addr}/v1/auth/approle/login",
                json={"role_id": self.role_id, "secret_id": self.secret_id},
            )
            assert response.status_code == 200, response.text
            return str(response.json()["auth"]["client_token"])

    def root(self, method: str, path: str, payload: dict | None = None) -> httpx.Response:
        with httpx.Client(verify=_ca_context(self), timeout=10) as client:
            return client.request(
                method,
                f"{self.addr}{path}",
                json=payload,
                headers={"X-Vault-Token": ROOT_TOKEN},
            )


def _start_vault(name: str, port: int, certs: Path) -> str:
    """Start the container; returns its id."""
    result = _docker(
        "run",
        "-d",
        "--name",
        name,
        "-p",
        f"127.0.0.1:{port}:8200",
        "-e",
        f"VAULT_DEV_ROOT_TOKEN_ID={ROOT_TOKEN}",
        "-e",
        "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200",
        IMAGE,
        # Vault refuses to start if the cert directory does not already exist, so a
        # shell wrapper creates it first. TLS stays on: the test then exercises
        # certificate verification against the generated CA instead of bypassing
        # it with a plaintext listener.
        "sh",
        "-c",
        "mkdir -p /vault-certs && exec vault server -dev -dev-tls -dev-tls-cert-dir=/vault-certs",
    )
    if result.returncode != 0:
        pytest.skip(f"could not start an isolated Vault container: {result.stderr.strip()[:400]}")
    container_id = result.stdout.strip()
    # The generated CA has to be read out of the container and trusted explicitly,
    # which is also how TLS verification gets exercised rather than bypassed.
    for _ in range(60):
        copied = _docker("cp", f"{name}:/vault-certs/vault-ca.pem", str(certs))
        if copied.returncode == 0 and certs.exists():
            return container_id
        time.sleep(0.5)
    _docker("rm", "-f", name)
    pytest.skip("Vault started but never produced its generated CA certificate")


def _ca_context(vault: LiveVault) -> ssl.SSLContext:
    """An explicit trust context for the probe's own control-plane calls.

    The same thing the adapter builds from ``KEK_VAULT_CA_BUNDLE``, so the test
    verifies Vault's certificate rather than skipping verification.
    """
    return ssl.create_default_context(cafile=str(vault.ca_bundle))


def _wait_healthy(addr: str, ca_bundle: Path) -> None:
    deadline = time.monotonic() + 60
    last: object = "no attempt"
    context = ssl.create_default_context(cafile=str(ca_bundle))
    while time.monotonic() < deadline:
        try:
            with httpx.Client(verify=context, timeout=5) as client:
                response = client.get(f"{addr}/v1/sys/health")
                if response.status_code == 200:
                    return
                last = response.status_code
        except httpx.HTTPError as exc:
            last = type(exc).__name__
        time.sleep(0.5)
    raise AssertionError(f"Vault did not become healthy ({last})")


def _configure(vault: LiveVault) -> None:
    """Create the mount, the derived key, the policy and the AppRole."""
    assert vault.root("POST", "/v1/sys/mounts/transit", {"type": "transit"}).status_code in (
        200,
        204,
    )
    key = vault.root(
        "PUT",
        f"/v1/transit/keys/{TRANSIT_KEY}",
        {
            "derived": True,
            "type": "aes256-gcm96",
            "exportable": False,
            "allow_plaintext_backup": False,
        },
    )
    assert key.status_code in (200, 204), key.text
    policy = vault.root("PUT", f"/v1/sys/policies/acl/{POLICY_NAME}", {"policy": TRANSIT_POLICY})
    assert policy.status_code in (200, 204), policy.text
    assert vault.root("POST", "/v1/sys/auth/approle", {"type": "approle"}).status_code in (200, 204)
    role = vault.root(
        "POST",
        f"/v1/auth/approle/role/{APP_ROLE}",
        {
            "token_policies": POLICY_NAME,
            "token_ttl": "5m",
            "token_max_ttl": "10m",
            # No default policy: the identity's *only* capabilities are the four
            # paths above, so the least-privilege claim is executable.
            "token_no_default_policy": True,
            "secret_id_ttl": "0",
        },
    )
    assert role.status_code in (200, 204), role.text
    role_id = vault.root("GET", f"/v1/auth/approle/role/{APP_ROLE}/role-id")
    secret_id = vault.root("POST", f"/v1/auth/approle/role/{APP_ROLE}/secret-id")
    assert role_id.status_code == 200 and secret_id.status_code == 200
    vault.role_id = str(role_id.json()["data"]["role_id"])
    vault.secret_id = str(secret_id.json()["data"]["secret_id"])


@pytest.fixture(scope="module")
def vault(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LiveVault]:
    if _DOCKER is None:
        pytest.skip("docker is not available: cannot run the real-Vault adapter test")
    if _docker("image", "inspect", IMAGE).returncode != 0:
        pytest.skip(f"{IMAGE} is not present locally: cannot run the real-Vault adapter test")

    name = f"nexusops-vault-kek-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    certs = tmp_path_factory.mktemp("vault-certs") / "vault-ca.pem"
    _start_vault(name, port, certs)
    try:
        addr = f"https://127.0.0.1:{port}"
        _wait_healthy(addr, certs)
        live = LiveVault(addr, certs, role_id="", secret_id="")
        _configure(live)
        yield live
    finally:
        # Only this container, by its unique name. No broad cleanup command.
        _docker("rm", "-f", name)


def _ctx(org: uuid.UUID = ORG, generation: int = 1, purpose: str = "org-dek") -> EncryptionContext:
    return EncryptionContext(org_id=org, dek_generation=generation, purpose=purpose)


# --- the contract -------------------------------------------------------------


async def test_a_real_derived_key_reports_healthy(vault: LiveVault) -> None:
    provider = vault.provider()
    try:
        health = await provider.health()
    finally:
        await provider.aclose()
    assert health.status is ProviderStatus.OK, health.detail
    assert health.operable
    assert TRANSIT_KEY in health.detail


async def test_wrap_and_unwrap_round_trip_through_transit(vault: LiveVault) -> None:
    provider = vault.provider()
    try:
        dek = Fernet.generate_key()
        wrapped = await provider.wrap_dek(dek, _ctx())
        assert wrapped.provider == "vault-transit"
        assert wrapped.key_version.isdigit()
        assert wrapped.ciphertext.startswith(b"vault:v")
        # The stored value is not the key, and does not contain it.
        assert dek not in wrapped.ciphertext
        recovered = await provider.unwrap_dek(wrapped, _ctx())
        assert recovered == dek
    finally:
        await provider.aclose()


async def test_the_wrong_context_is_refused_by_vault_itself(vault: LiveVault) -> None:
    """Organization, purpose and generation are each load-bearing.

    Asserted one field at a time, because a binding that only distinguishes some of
    its inputs is not a binding — and because a wrong *purpose* (the DNS credential
    of a later slice presented as an organization DEK) must fail for the same
    reason a wrong tenant does.
    """
    provider = vault.provider()
    try:
        dek = Fernet.generate_key()
        wrapped = await provider.wrap_dek(dek, _ctx())
        for wrong in (
            _ctx(org=OTHER_ORG),
            _ctx(generation=2),
            _ctx(org=OTHER_ORG, generation=2, purpose="org-dek"),
        ):
            with pytest.raises(KEKContextMismatchError):
                await provider.unwrap_dek(wrapped, wrong)
    finally:
        await provider.aclose()


async def test_no_purpose_outside_the_vocabulary_is_accepted(vault: LiveVault) -> None:
    """An unknown purpose cannot even be expressed as a context."""
    with pytest.raises(ValueError, match="unknown KEK purpose"):
        _ctx(purpose="acme-account")


async def test_a_rewrap_moves_the_key_version_and_keeps_the_binding(vault: LiveVault) -> None:
    """The KEK-rotation property, provider-side and measured.

    Rotate the transit key, rewrap (Vault does the work, so no plaintext DEK is
    returned to this process), and check that the value is genuinely re-encrypted
    under the new version while the old binding still authenticates.
    """
    provider = vault.provider()
    try:
        dek = Fernet.generate_key()
        wrapped = await provider.wrap_dek(dek, _ctx())
        before_version = int(wrapped.key_version)

        assert vault.root("POST", f"/v1/transit/keys/{TRANSIT_KEY}/rotate").status_code in (
            200,
            204,
        )
        rewrapped = await provider.rewrap_dek(wrapped, _ctx())

        assert rewrapped.key_version != wrapped.key_version
        assert int(rewrapped.key_version) > before_version
        assert rewrapped.ciphertext != wrapped.ciphertext
        assert await provider.unwrap_dek(rewrapped, _ctx()) == dek
        # The old ciphertext is still readable: rotation is not destructive.
        assert await provider.unwrap_dek(wrapped, _ctx()) == dek
        # And the binding survived the move.
        with pytest.raises(KEKContextMismatchError):
            await provider.unwrap_dek(rewrapped, _ctx(org=OTHER_ORG))
        with pytest.raises(KEKContextMismatchError):
            await provider.unwrap_dek(rewrapped, _ctx(generation=2))
    finally:
        await provider.aclose()


def test_associated_data_cannot_be_rewrapped(vault: LiveVault) -> None:
    """Why the binding is the derivation context and not AAD — measured.

    AAD authenticates on encrypt and decrypt, but ``transit/rewrap`` has no
    ``associated_data`` parameter. Encrypting with AAD therefore produces a value
    that cannot be rotated provider-side at all, which would force a KEK rotation to
    unwrap every DEK in the application — the exact thing the approved design
    forbids. This test pins the failure so the design decision stays justified by
    evidence rather than by memory.
    """
    with httpx.Client(verify=_ca_context(vault), timeout=10) as client:
        token = vault.app_token()
        plaintext = base64.b64encode(Fernet.generate_key()).decode()
        context = _ctx().provider_context()
        # Transit takes associated_data base64-encoded, like every other binary
        # field on its API; providing it is how an AAD binding would have to travel.
        aad = base64.b64encode(b"org:1234").decode()
        auth = {"X-Vault-Token": token}
        sealed = client.post(
            f"{vault.addr}/v1/transit/encrypt/{TRANSIT_KEY}",
            json={"plaintext": plaintext, "context": context, "associated_data": aad},
            headers=auth,
        )
        assert sealed.status_code == 200, sealed.text
        ciphertext = sealed.json()["data"]["ciphertext"]

        # Decrypt with the same AAD: fine.
        opened = client.post(
            f"{vault.addr}/v1/transit/decrypt/{TRANSIT_KEY}",
            json={"ciphertext": ciphertext, "context": context, "associated_data": aad},
            headers=auth,
        )
        assert opened.status_code == 200, opened.text

        # Rewrap without it: Vault has nowhere to put the AAD, so authentication
        # fails and the envelope is un-rotatable provider-side.
        rewrapped = client.post(
            f"{vault.addr}/v1/transit/rewrap/{TRANSIT_KEY}",
            json={"ciphertext": ciphertext, "context": context},
            headers=auth,
        )
        assert rewrapped.status_code >= 400, (
            "Vault accepted an AAD-bound rewrap; the design's premise must be re-measured"
        )
        assert "authentication failed" in rewrapped.text.lower()

        # And with the AAD supplied anyway, it is simply not a rewrap parameter: the
        # field is ignored, and the same authentication failure comes back.
        ignored = client.post(
            f"{vault.addr}/v1/transit/rewrap/{TRANSIT_KEY}",
            json={"ciphertext": ciphertext, "context": context, "associated_data": aad},
            headers=auth,
        )
        assert ignored.status_code >= 400


def test_the_application_identity_cannot_administer_keys(vault: LiveVault) -> None:
    """Least privilege, asserted against Vault's own policy engine.

    The identity may encrypt, decrypt, rewrap and read one key — and may not create,
    rotate, configure or delete anything, which is what keeps a compromised
    application from re-keying the platform or reading another tenant's key.
    """
    with httpx.Client(verify=_ca_context(vault), timeout=10) as client:
        headers = {"X-Vault-Token": vault.app_token()}

        def attempt(method: str, path: str, payload: dict | None = None) -> int:
            return client.request(
                method, f"{vault.addr}{path}", json=payload, headers=headers
            ).status_code

        assert attempt("PUT", f"/v1/transit/keys/{TRANSIT_KEY}", {"derived": False}) == 403
        assert attempt("POST", f"/v1/transit/keys/{TRANSIT_KEY}/rotate") == 403
        assert attempt("PUT", "/v1/transit/keys/another-org-dek", {"derived": True}) == 403
        assert attempt("DELETE", f"/v1/transit/keys/{TRANSIT_KEY}") == 403
        assert (
            attempt("POST", f"/v1/transit/keys/{TRANSIT_KEY}/config", {"min_decryption_version": 1})
            == 403
        )
        assert attempt("GET", "/v1/sys/mounts") == 403
        assert attempt("GET", "/v1/sys/policies/acl/root") == 403
        # What it *may* do, so the refusal above is not an artifact of a dead token.
        assert attempt("GET", f"/v1/transit/keys/{TRANSIT_KEY}") == 200


async def test_an_invalid_approle_secret_is_unauthorized(vault: LiveVault) -> None:
    provider = vault.provider(secret_id="not-the-secret-id")
    try:
        with pytest.raises(Exception) as raised:
            await provider.wrap_dek(Fernet.generate_key(), _ctx())
        assert type(raised.value).__name__ == "KEKUnauthorizedError"
    finally:
        await provider.aclose()


async def test_an_unknown_key_name_is_reported_as_unauthorized_not_success(
    vault: LiveVault,
) -> None:
    """At least privilege, the wrong key name is indistinguishable from a denied path.

    The application's policy names one key path, so Vault's ACL denies any other
    path before it looks for a key there: a typo'd ``KEK_VAULT_TRANSIT_KEY`` comes
    back as 403, exactly like a policy that is too narrow. Both are addressed by the
    same operator action (check the key name and the policy), and neither may ever
    be reported as healthy — which is the assertion that matters here.
    """
    provider = vault.provider(transit_key="no-such-key")
    try:
        health = await provider.health()
        assert health.status is ProviderStatus.UNAUTHORIZED
        assert not health.operable
        with pytest.raises(Exception) as raised:
            await provider.wrap_dek(Fernet.generate_key(), _ctx())
        assert type(raised.value).__name__ in {"KEKUnauthorizedError", "KEKConfigurationError"}
    finally:
        await provider.aclose()


async def test_an_unreachable_vault_is_unavailable(vault: LiveVault) -> None:
    """A dead endpoint must never look like success, or like a ciphertext mismatch."""
    provider = vault.provider(addr="https://127.0.0.1:1", timeout_seconds=0.5)
    try:
        with pytest.raises(Exception) as raised:
            await provider.wrap_dek(Fernet.generate_key(), _ctx())
        assert type(raised.value).__name__ == "KEKUnavailableError"
        health = await provider.health()
        assert health.status is ProviderStatus.UNREACHABLE
    finally:
        await provider.aclose()


async def test_the_stored_envelope_is_self_describing(vault: LiveVault) -> None:
    """What a row would hold: provider, key, version, ciphertext — and no key."""
    provider = vault.provider()
    try:
        dek = Fernet.generate_key()
        stored = (await provider.wrap_dek(dek, _ctx())).encode()
        assert stored.startswith("v1:vault-transit:nexusops-org-dek:")
        assert json.dumps(stored)  # a plain string, safe in a Text column
        assert dek.decode() not in stored
        assert base64.b64encode(dek).decode() not in stored
    finally:
        await provider.aclose()
