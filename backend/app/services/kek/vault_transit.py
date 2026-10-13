"""Vault Transit — the first production ``KEKProvider`` (approved 2026-10-12).

The root key lives in Vault and never leaves it: NexusOps authenticates as a
least-privilege application identity, asks Transit to wrap or unwrap one DEK, and
stores only the returned ciphertext. Rewrap — the KEK-rotation operation — is
performed by Transit itself (``transit/rewrap``), which is why a KEK-only rotation
never materialises a plaintext DEK in this process.

**The context binding is Transit's derivation context, not AAD.** The wrapped DEK
is bound to ``(organization, purpose, generation)`` through the ``context``
parameter of ``transit/encrypt|decrypt|rewrap``, with the transit key created
``derived=true``. That choice is measured, not aesthetic: Transit's
``associated_data`` authenticates on encrypt/decrypt but **does not exist on
rewrap** (Vault 1.15 rejects an AAD-bound ciphertext with ``message authentication
failed``), so an AAD binding cannot be rotated provider-side at all. The derivation
context is accepted by every operation, a wrong value fails authentication, and
rewrap preserves it — so the approved invariant ("no plaintext DEK during KEK-only
rotation") holds rather than being traded away.

**What this adapter deliberately does not do:** no root token, no key creation or
rotation (``transit/keys/*`` is an operator action — the application only *reads*
key metadata to report health), no retries (a provider failure fails closed with a
named error instead of becoming a retry storm), no plaintext logging, and no
``verify=False`` escape hatch. Request bodies and tokens never reach a log line: a
failure is logged as a status code plus a matched reason, never with the body.
"""

from __future__ import annotations

import asyncio
import base64
import ssl
import time
from urllib.parse import urlsplit

import httpx

from app.core.logging import get_logger
from app.services.kek import (
    EncryptionContext,
    KEKConfigurationError,
    KEKContextMismatchError,
    KEKEnvelopeError,
    KEKUnauthorizedError,
    KEKUnavailableError,
    ProviderHealth,
    ProviderStatus,
    WrappedKey,
    validate_dek,
)

log = get_logger("nexusops.kek.vault")

#: Ciphertexts Transit returns look like ``vault:v3:<base64>``; the version is the
#: key version that wrapped it, and it is what a rewrap moves forward.
_CIPHERTEXT_PREFIX = "vault:v"
#: Vault's own words for the two conditions worth distinguishing by text rather
#: than by status code. Matched as substrings of the *server's* error list, which
#: is never echoed into a log or an exception message.
_AUTH_FAILED = "authentication failed"
_DERIVATION_REQUIRED = "key derivation"


def _embeds_userinfo(addr: str) -> bool:
    """Whether a Vault address carries ``user:password@`` (Phase 5.2.1.2, F4).

    Only the authority component is inspected, so a path prefix
    (``https://vault.example:8200/team``) is unaffected. An address that does not
    parse as a URL at all is left to the ``https://`` check, which refuses it
    first anyway.
    """
    try:
        parts = urlsplit(addr)
    except ValueError:
        return False
    return parts.username is not None or parts.password is not None or "@" in parts.netloc


class VaultTransitKEKProvider:
    """``KEKProvider`` backed by a single Transit key in HashiCorp Vault."""

    name = "vault-transit"
    production_safe = True

    def __init__(
        self,
        *,
        addr: str,
        transit_key: str,
        role_id: str,
        secret_id: str,
        ca_bundle: str | None = None,
        timeout_seconds: float = 5.0,
        namespace: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        mount: str = "transit",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not addr or not transit_key or not role_id or not secret_id:
            raise KEKConfigurationError(
                "Vault Transit requires KEK_VAULT_ADDR, KEK_VAULT_TRANSIT_KEY, "
                "KEK_VAULT_ROLE_ID and KEK_VAULT_SECRET_ID"
            )
        if not addr.startswith("https://"):
            # Checked here as well as in settings validation: the adapter is
            # constructible directly (tests, tooling), and a plaintext transport to
            # the service that holds the root key must be impossible to build, not
            # merely unreachable by one configuration path.
            raise KEKConfigurationError(
                "KEK_VAULT_ADDR must use https:// — Vault carries the root key and "
                "certificate verification is mandatory"
            )
        if _embeds_userinfo(addr):
            # Same reasoning: authentication is AppRole, so a user:password in the
            # address is a credential nothing here consumes — it must not be
            # carried into an httpx base URL or a request log. Neither this message
            # nor the settings one quotes the address (Phase 5.2.1.2, F4).
            raise KEKConfigurationError(
                "KEK_VAULT_ADDR must not embed a username or password: Vault access is "
                "authenticated with KEK_VAULT_ROLE_ID and KEK_VAULT_SECRET_ID. Remove "
                "the credentials from the address."
            )
        if ca_bundle == "":
            # An empty bundle string would silently fall back to the system store;
            # treat it as "unset" rather than as a half-configured value.
            ca_bundle = None
        # TLS verification is mandatory. The value is either a context built from
        # the configured CA bundle or the system trust store — there is
        # intentionally no way to spell "off". A missing bundle is refused here
        # rather than per request: it is a deployment mistake, and it fails the
        # same way at health-probe time as at unwrap time if left to httpx.
        if ca_bundle:
            try:
                self._verify: bool | ssl.SSLContext = ssl.create_default_context(cafile=ca_bundle)
            except OSError as exc:
                raise KEKConfigurationError(
                    "KEK_VAULT_CA_BUNDLE could not be loaded; TLS verification is mandatory"
                ) from exc
        else:
            self._verify = True
        self._addr = addr.rstrip("/")
        self._mount = mount
        self._transit_key = transit_key
        self._role_id = role_id
        self._secret_id = secret_id
        self._namespace = namespace
        headers = {"X-Vault-Request": "true"}
        if namespace:
            headers["X-Vault-Namespace"] = namespace
        # No retries are configured anywhere: httpx's own transport defaults to
        # ``retries=0``, and nothing here overrides it. A provider failure must
        # surface as a named error on the first answer, not become a retry storm
        # against a Vault that is already struggling — and a retried wrap must not
        # be able to produce a second envelope behind the caller's back.
        self._client = client or httpx.AsyncClient(
            base_url=self._addr,
            # Ignored when an explicit transport is supplied (a MockTransport in
            # tests); with the default transport it is what enforces TLS against
            # the CA bundle or the system store, and it is never ``False``.
            verify=self._verify,
            timeout=httpx.Timeout(timeout_seconds),
            headers=headers,
            transport=transport,
        )
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._token_lock = asyncio.Lock()

    # --- lifecycle ---------------------------------------------------------

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- authentication ----------------------------------------------------

    async def _login(self) -> None:
        """Exchange the AppRole credentials for a short-lived client token.

        The token is held in memory only, refreshed before its lease expires, and
        never logged, serialized or returned. The role-id/secret-id pair is the
        application's whole identity: it can encrypt, decrypt and rewrap one key.
        """
        try:
            response = await self._client.post(
                "/v1/auth/approle/login",
                json={"role_id": self._role_id, "secret_id": self._secret_id},
            )
        except httpx.HTTPError as exc:
            raise KEKUnavailableError(
                f"Vault is unreachable at {self._addr} ({type(exc).__name__})"
            ) from exc
        if response.status_code in (400, 401, 403):
            raise KEKUnauthorizedError(
                "Vault refused the AppRole login (invalid role or secret id)"
            )
        auth = self._json_object(response).get("auth")
        if not isinstance(auth, dict) or not auth.get("client_token"):
            raise KEKEnvelopeError("Vault login response carried no client token")
        self._token = str(auth["client_token"])
        lease = auth.get("lease_duration")
        lease_seconds = float(lease) if isinstance(lease, int | float) and lease else 300.0
        # Refresh at 2/3 of the lease: early enough that a slow request cannot
        # outlive the token, late enough not to re-login on every call.
        self._token_expires_at = time.monotonic() + max(30.0, lease_seconds * 2 / 3)
        log.info("kek_vault_login_ok", lease_seconds=int(lease_seconds))

    async def _ensure_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token
        async with self._token_lock:
            # Re-check inside the lock: a concurrent caller may have just logged in.
            if self._token and time.monotonic() < self._token_expires_at:
                return self._token
            await self._login()
        assert self._token is not None
        return self._token

    # --- provider protocol -------------------------------------------------

    async def wrap_dek(self, dek: bytes, ctx: EncryptionContext) -> WrappedKey:
        validate_dek(dek)
        payload = {
            "plaintext": _b64(dek),
            "context": ctx.provider_context(),
        }
        data = await self._call("POST", f"/v1/{self._mount}/encrypt/{self._transit_key}", payload)
        ciphertext = data.get("ciphertext")
        if not isinstance(ciphertext, str) or not ciphertext:
            raise KEKEnvelopeError("Vault encrypt response carried no ciphertext")
        return self._wrapped(ciphertext)

    async def unwrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> bytes:
        self._require_own_envelope(wrapped)
        data = await self._call(
            "POST",
            f"/v1/{self._mount}/decrypt/{self._transit_key}",
            {
                "ciphertext": wrapped.ciphertext.decode("utf-8"),
                "context": ctx.provider_context(),
            },
        )
        plaintext = data.get("plaintext")
        if not isinstance(plaintext, str) or not plaintext:
            raise KEKEnvelopeError("Vault decrypt response carried no plaintext")
        try:
            dek = base64.b64decode(plaintext, validate=True)
        except (ValueError, TypeError) as exc:
            raise KEKEnvelopeError("Vault decrypt response was not canonical base64") from exc
        return validate_dek(dek)

    async def rewrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> WrappedKey:
        """Move the ciphertext to the current key version — provider-side.

        Transit decrypts and re-encrypts internally and returns only ciphertext, so
        this process never sees the DEK. The context is required by Transit for a
        derived key, which is also what keeps the binding intact across the move.
        """
        self._require_own_envelope(wrapped)
        data = await self._call(
            "POST",
            f"/v1/{self._mount}/rewrap/{self._transit_key}",
            {
                "ciphertext": wrapped.ciphertext.decode("utf-8"),
                "context": ctx.provider_context(),
            },
        )
        ciphertext = data.get("ciphertext")
        if not isinstance(ciphertext, str) or not ciphertext:
            raise KEKEnvelopeError("Vault rewrap response carried no ciphertext")
        return self._wrapped(ciphertext)

    async def health(self) -> ProviderHealth:
        """Read the transit key's metadata. Requires only ``read`` on the key.

        A key that is not configured for derivation is reported as an *invalid
        configuration* rather than as unhealthy: the provider is fine, the
        deployment's key cannot satisfy the platform's binding requirement, and
        that is an operator action, not a retry.
        """
        try:
            data = await self._call("GET", f"/v1/{self._mount}/keys/{self._transit_key}")
        except KEKConfigurationError as exc:
            return ProviderHealth(ProviderStatus.INVALID_CONFIGURATION, self.name, str(exc))
        except KEKUnauthorizedError as exc:
            return ProviderHealth(ProviderStatus.UNAUTHORIZED, self.name, str(exc))
        except (KEKUnavailableError, KEKEnvelopeError) as exc:
            return ProviderHealth(ProviderStatus.UNREACHABLE, self.name, str(exc))
        if not data.get("derived"):
            return ProviderHealth(
                ProviderStatus.INVALID_CONFIGURATION,
                self.name,
                f"transit key {self._transit_key!r} is not configured for key derivation "
                "(create it with derived=true)",
            )
        keys = data.get("keys")
        version = len(keys) if isinstance(keys, dict) else None
        detail = f"key {self._transit_key!r} reachable"
        if version:
            detail += f" (version {version})"
        return ProviderHealth(ProviderStatus.OK, self.name, detail)

    # --- internals ---------------------------------------------------------

    def _require_own_envelope(self, wrapped: WrappedKey) -> None:
        if wrapped.provider != self.name or wrapped.key_id != self._transit_key:
            # Refuse locally instead of sending another key's ciphertext to Vault:
            # a 400 from Transit would look like tampering, and this is a
            # configuration or data error that deserves its own answer.
            raise KEKEnvelopeError("the wrapped DEK was not produced by this Vault transit key")

    def _wrapped(self, ciphertext: str) -> WrappedKey:
        version = ciphertext[len(_CIPHERTEXT_PREFIX) :].split(":", 1)[0]
        if not ciphertext.startswith(_CIPHERTEXT_PREFIX) or not version.isdigit():
            raise KEKEnvelopeError("Vault returned a ciphertext in an unknown format")
        return WrappedKey(
            provider=self.name,
            key_id=self._transit_key,
            key_version=version,
            ciphertext=ciphertext.encode("utf-8"),
        )

    async def _call(self, method: str, path: str, payload: dict[str, str] | None = None) -> dict:
        """One authenticated Transit call, mapped onto the seam's named errors."""
        token = await self._ensure_token()
        try:
            response = await self._client.request(
                method, path, json=payload, headers={"X-Vault-Token": token}
            )
        except httpx.TimeoutException as exc:
            raise KEKUnavailableError(
                f"Vault did not answer within the configured timeout ({type(exc).__name__})"
            ) from exc
        except httpx.HTTPError as exc:
            raise KEKUnavailableError(f"Vault is unreachable ({type(exc).__name__})") from exc
        if response.status_code >= 400:
            reason = _classify(response)
            # Log the status and the classification only — never the body, which
            # can echo the request, and never the token.
            log.warning(
                "kek_vault_call_failed",
                path=path,
                status=response.status_code,
                reason=reason,
            )
            if response.status_code in (401, 403):
                raise KEKUnauthorizedError(
                    "Vault denied the request: the application identity or its policy "
                    "does not permit this operation"
                )
            if response.status_code == 404:
                raise KEKConfigurationError(
                    "Vault has no such transit key or mount (check KEK_VAULT_TRANSIT_KEY)"
                )
            if reason == _AUTH_FAILED:
                raise KEKContextMismatchError(
                    "the wrapped DEK did not verify under this organization, purpose and "
                    "generation (or the ciphertext is corrupt)"
                )
            if reason == _DERIVATION_REQUIRED:
                raise KEKConfigurationError(
                    "the transit key cannot satisfy the context binding (it must be "
                    "created with derived=true)"
                )
            raise KEKUnavailableError(f"Vault rejected the request (HTTP {response.status_code})")
        return self._json_object(response).get("data") or {}

    @staticmethod
    def _json_object(response: httpx.Response) -> dict:
        try:
            body = response.json()
        except ValueError as exc:
            raise KEKEnvelopeError("Vault returned a non-JSON response") from exc
        if not isinstance(body, dict):
            raise KEKEnvelopeError("Vault returned an unexpected response shape")
        return body


def _b64(value: bytes) -> str:
    """Wrap-free base64, matching what Vault expects and returns."""
    return base64.b64encode(value).decode("ascii")


def _classify(response: httpx.Response) -> str:
    """Map a Vault error body onto one of the two reasons worth naming.

    Only a *matched* keyword is ever surfaced; the server's message is not logged
    or re-raised, so nothing the provider echoes about the request (or about a
    credential) can reach a log line.
    """
    try:
        body = response.json()
    except ValueError:
        return ""
    errors = body.get("errors") if isinstance(body, dict) else None
    text = " ".join(str(item) for item in errors) if isinstance(errors, list) else ""
    lowered = text.lower()
    if _AUTH_FAILED in lowered:
        return _AUTH_FAILED
    if _DERIVATION_REQUIRED in lowered:
        return _DERIVATION_REQUIRED
    return ""


__all__ = ["VaultTransitKEKProvider"]
