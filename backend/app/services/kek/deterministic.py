"""The deterministic in-process provider — tests and explicitly configured dev.

This provider exists so the envelope's behaviour can be tested exhaustively and
repeatably: same input, same ciphertext, every run, on any machine. It is **not**
a key-management system and it is not a fallback. Three properties keep it from
becoming one:

* it must be *named* selection — ``KEK_PROVIDER=test``. There is no detection, no
  "use it when Vault is unreachable", no default;
* it declares ``production_safe = False``, and both the settings validator and
  the factory refuse it under a production configuration, so a production
  deployment cannot reach it by configuration at all;
* it never touches the network, so it cannot mask "the provider is down" as
  success in a test that meant to check failure handling.

The root key below is a **test constant, not a secret**: it is derived from a
literal string in this file, so it is public by construction and useless as a
credential. Real dev/test material never appears in source; when a development
environment wants fidelity it configures ``vault-transit`` against a local Vault.
"""

from __future__ import annotations

import hashlib
import hmac

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.kek import (
    EncryptionContext,
    KEKContextMismatchError,
    KEKEnvelopeError,
    ProviderHealth,
    ProviderStatus,
    WrappedKey,
    validate_dek,
)

#: Public test constant. Deterministically derived so the whole fixture tree is
#: reproducible; never a secret and never valid in production (see module docstring).
_TEST_ROOT_KEY = hashlib.sha256(b"nexusops deterministic test KEK (NOT a secret)").digest()

_TEST_KEY_ID = "deterministic-test-key"
_NONCE_BYTES = 12


def _derive(root: bytes, binding: str, version: str) -> bytes:
    """A per-(binding, key version) key: HKDF-style derivation.

    Two properties, both modelling Vault rather than a convenience:

    * deriving per **binding** means a wrong organization/purpose/generation
      produces a *different key*, so unwrapping fails at authentication exactly as
      it does in Transit — the test provider reproduces the failure mode instead of
      comparing a field for equality;
    * deriving per **version** means a rotation genuinely changes the ciphertext
      (as ``transit/rewrap`` does), while an older version stays readable because
      unwrap derives from the version recorded in the envelope, not from the
      provider's current one. Without this, a "rewrapped" value would be
      byte-identical to the old one and a test could not tell the two apart.
    """
    material = f"{version}:{binding}".encode()
    return hmac.new(root, material, hashlib.sha256).digest()


class DeterministicKEKProvider:
    """Deterministic wrap/unwrap/rewrap over an in-process AEAD."""

    name = "test"
    production_safe = False

    def __init__(self, *, root_key: bytes | None = None, key_version: int = 1) -> None:
        self._root = root_key or _TEST_ROOT_KEY
        self._version = max(1, key_version)

    # --- test affordance ---------------------------------------------------

    def rotate(self) -> int:
        """Bump the modelled KEK version, so a test can prove rewrap moves it."""
        self._version += 1
        return self._version

    @property
    def key_version(self) -> int:
        return self._version

    # --- provider protocol -------------------------------------------------

    async def wrap_dek(self, dek: bytes, ctx: EncryptionContext) -> WrappedKey:
        validate_dek(dek)
        key = _derive(self._root, ctx.binding(), str(self._version))
        # Deterministic nonce: identical plaintext under the same binding yields
        # identical ciphertext, which is what makes fixtures stable. Convergent on
        # purpose — a test provider has no need for semantic security, and saying
        # so is better than an accidental nonce reuse in something that does.
        nonce = hmac.new(key, b"nonce:" + dek, hashlib.sha256).digest()[:_NONCE_BYTES]
        ciphertext = AESGCM(key).encrypt(nonce, dek, ctx.binding().encode("utf-8"))
        return WrappedKey(
            provider=self.name,
            key_id=_TEST_KEY_ID,
            key_version=str(self._version),
            ciphertext=nonce + ciphertext,
        )

    async def unwrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> bytes:
        if wrapped.provider != self.name:
            raise KEKEnvelopeError(
                f"envelope was wrapped by {wrapped.provider!r}, not by this provider"
            )
        if not wrapped.key_version.isdigit():
            raise KEKEnvelopeError(
                f"envelope names a non-numeric key version ({wrapped.key_version!r})"
            )
        # Derive from the version the envelope records, not the provider's current
        # one: that is what keeps pre-rotation ciphertext readable after a rewrap.
        key = _derive(self._root, ctx.binding(), wrapped.key_version)
        nonce, ciphertext = wrapped.ciphertext[:_NONCE_BYTES], wrapped.ciphertext[_NONCE_BYTES:]
        try:
            return AESGCM(key).decrypt(nonce, ciphertext, ctx.binding().encode("utf-8"))
        except InvalidTag as exc:
            # Same condition Vault reports as "message authentication failed":
            # wrong binding, or corrupt/tampered ciphertext. Never resolved by
            # trying another key or context.
            raise KEKContextMismatchError(
                "the wrapped DEK did not verify under this organization, purpose and "
                "generation (or the ciphertext is corrupt)"
            ) from exc

    async def rewrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> WrappedKey:
        if wrapped.key_version == str(self._version):
            # Nothing to do: the value is already under the current version. The
            # real adapter returns the provider's rewritten ciphertext here; the
            # test provider keeps the byte-for-byte value so idempotence is visible.
            return wrapped
        # In-process stand-in for Transit's rewrap: it validates the binding, then
        # re-encrypts under the new version. The plaintext stays inside this call
        # and is never returned to the caller.
        dek = await self.unwrap_dek(wrapped, ctx)
        return await self.wrap_dek(dek, ctx)

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider=self.name,
            detail="deterministic test provider (not production safe)",
        )
