"""The KEK provider seam — the one place key material crosses the platform boundary.

Phase 5 wraps each organization's Fernet DEK with a **root key that never enters
this process**: the provider holds the root, NexusOps holds only the wrapped
value. This module is the seam that makes that true — it defines the protocol the
envelope calls, the two value objects they exchange, the named errors a failure
produces, and the wire format the wrapped value is stored in. Nothing else in the
codebase may talk to a provider, and no provider may return the root key.

**Binding is cryptographic, not structural.** The organization id, the purpose
and the DEK generation are not merely *stored beside* the ciphertext — they are
bound into the encryption, so a wrapped DEK lifted from one organization's row
into another's cannot be unwrapped at all (``KEK_CONTEXT_MISMATCH``), and neither
can one replayed under a different purpose or generation. Beside-ciphertext
metadata would be an assertion the database cannot keep; this is a property the
ciphertext itself enforces.

**Why the binding travels as an AES-GCM nonce-free derivation *context*.** The
Vault Transit adapter binds it as the derived-key ``context`` parameter, because
that is the only binding Transit accepts on **every** operation: ``transit/encrypt``,
``transit/decrypt`` *and* ``transit/rewrap``. Transit's ``associated_data`` (AAD)
parameter authenticates on encrypt/decrypt but does **not** exist on rewrap, so an
AAD-bound envelope cannot be rotated provider-side at all — measured against Vault
1.15, rewrap of an AAD-bound ciphertext fails with ``message authentication
failed``. Since the approved design requires KEK-only rotation to happen at the
provider with no plaintext DEK returned to the application, the derivation context
is the binding, and ``associated_data`` is deliberately unused. The invariant is
therefore kept rather than weakened: wrong context fails, and rewrap preserves the
binding.

The wire format is versioned and self-describing, so the stored value states which
provider, key and key version can unwrap it — adding a provider is not a migration.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

#: Envelope wire-format version. It participates in the binding, so a future format
#: change cannot silently reinterpret an existing ciphertext.
FORMAT_VERSION = "v1"

#: The only purpose in Phase 5. A new purpose gets a new literal and therefore a
#: different binding — a DNS credential wrapped for ``org-dek`` cannot be presented
#: as an ACME account key even though both are wrapped DEKs.
PURPOSE_ORG_DEK = "org-dek"
PURPOSES: frozenset[str] = frozenset({PURPOSE_ORG_DEK})

#: Provider names that may appear in a stored envelope. An unknown name is refused
#: rather than attempted: an envelope naming something this build cannot unwind is
#: a misconfiguration, not a candidate for a fallback.
KNOWN_PROVIDERS: frozenset[str] = frozenset({"vault-transit", "test"})

#: Bounds. The DEK is a 44-byte Fernet key and a Vault ciphertext of it is a short
#: base64 string, so these are generous by orders of magnitude and exist to refuse
#: absurd input early instead of passing it to a provider.
MAX_DEK_BYTES = 128
MAX_ENVELOPE_CHARS = 8_192
MAX_FIELD_CHARS = 512
#: Field separator of the envelope; a provider or key name may not contain it.
_SEP = ":"


class KEKError(Exception):
    """Base class for provider failures. Messages never carry key material.

    Every message in this hierarchy is written to be safe in a log, an event, an
    audit row or an API error: it names the *condition*, never the DEK, the root
    key, a Vault token or the ciphertext.
    """

    code = "KEK_ERROR"


class KEKConfigurationError(KEKError):
    """The provider is unset, unknown, or configured in a way this build refuses.

    Raised at construction time — in production that is process start, so a
    deployment cannot serve traffic with an unusable or unsafe key source.
    """

    code = "KEK_CONFIG_INVALID"


class KEKUnavailableError(KEKError):
    """The provider could not be reached, or answered nothing usable in time."""

    code = "KEK_UNAVAILABLE"


class KEKUnauthorizedError(KEKError):
    """The provider authenticated the caller and refused: identity or policy."""

    code = "KEK_UNAUTHORIZED"


class KEKEnvelopeError(KEKError):
    """A stored envelope, or a provider response, is malformed."""

    code = "KEK_ENVELOPE_INVALID"


class KEKContextMismatchError(KEKError):
    """The ciphertext did not verify under this organization/purpose/generation.

    The provider cannot tell "wrong binding" from "corrupt or tampered
    ciphertext" — both are an authentication failure of the same AEAD — so this
    error names both possibilities and is *never* retried into a fallback.
    """

    code = "KEK_CONTEXT_MISMATCH"


class ProviderStatus(StrEnum):
    """The four states health must distinguish (never merged into a boolean)."""

    OK = "ok"
    DISABLED = "disabled"
    UNREACHABLE = "unreachable"
    UNAUTHORIZED = "unauthorized"
    INVALID_CONFIGURATION = "invalid_configuration"


@dataclass(frozen=True)
class ProviderHealth:
    """A provider's self-report. ``detail`` is sanitized: no tokens, no DSNs."""

    status: ProviderStatus
    provider: str
    detail: str = ""

    @property
    def operable(self) -> bool:
        return self.status is ProviderStatus.OK


@dataclass(frozen=True)
class EncryptionContext:
    """What a wrapped DEK is bound to. Frozen: a context is not edited in place."""

    org_id: uuid.UUID
    purpose: str = PURPOSE_ORG_DEK
    dek_generation: int = 1
    format_version: str = FORMAT_VERSION

    def __post_init__(self) -> None:
        if self.purpose not in PURPOSES:
            raise ValueError(f"unknown KEK purpose {self.purpose!r}")
        if self.dek_generation < 1:
            # Generation 0 is the database's "no DEK yet" marker, so it can never
            # be a wrapped generation; letting it through would make an unwrapped
            # organization indistinguishable from a wrapped one.
            raise ValueError("dek_generation must be >= 1")
        if self.format_version != FORMAT_VERSION or _SEP in self.format_version:
            raise ValueError(f"unknown envelope format version {self.format_version!r}")

    def binding(self) -> str:
        """The canonical, unambiguous binding string.

        Field order and separator are fixed and every component is constrained
        (a uuid, a vocabulary word, a positive int, a version literal), so the
        encoding is injective: two different contexts cannot produce the same
        binding, and no context can be smuggled into another by string surgery.
        """
        return _SEP.join(
            (
                "nexusops",
                self.format_version,
                self.purpose,
                str(self.org_id),
                str(self.dek_generation),
            )
        )

    def provider_context(self) -> str:
        """The binding as a provider expects it: base64, never line-wrapped.

        Wrap-free matters: a newline inside the encoded context is invisible in a
        diff and produces a provider-side JSON parse error, which reads like a
        provider fault instead of the client bug it is.
        """
        return base64.b64encode(self.binding().encode("utf-8")).decode("ascii")


@dataclass(frozen=True)
class WrappedKey:
    """A DEK as stored: who wrapped it, which key and version, and the ciphertext."""

    provider: str
    key_id: str
    key_version: str
    ciphertext: bytes
    format_version: str = FORMAT_VERSION

    def __post_init__(self) -> None:
        if self.provider not in KNOWN_PROVIDERS:
            raise KEKEnvelopeError(f"unknown KEK provider {self.provider!r} in envelope")
        for name, value in (("key_id", self.key_id), ("key_version", self.key_version)):
            if not value or len(value) > MAX_FIELD_CHARS or _SEP in value:
                raise KEKEnvelopeError(f"invalid {name} in KEK envelope")
        if not self.ciphertext or len(self.ciphertext) > MAX_DEK_BYTES * 8:
            raise KEKEnvelopeError("invalid ciphertext length in KEK envelope")

    def encode(self) -> str:
        """``v1:<provider>:<key_id>:<key_version>:<base64 ciphertext>``."""
        payload = base64.b64encode(self.ciphertext).decode("ascii")
        return _SEP.join(
            (self.format_version, self.provider, self.key_id, self.key_version, payload)
        )

    @classmethod
    def decode(cls, value: str) -> WrappedKey:
        """Parse a stored envelope, strictly.

        Every rejection is a named :class:`KEKEnvelopeError`: an unknown format
        version, an unknown provider, a missing field, non-canonical base64 or an
        oversized value. Nothing is guessed, defaulted or partially parsed — a
        half-understood envelope must not reach a provider.
        """
        if not isinstance(value, str) or not value:
            raise KEKEnvelopeError("empty KEK envelope")
        if len(value) > MAX_ENVELOPE_CHARS:
            raise KEKEnvelopeError("KEK envelope is implausibly long")
        parts = value.split(_SEP, 4)
        if len(parts) != 5:
            raise KEKEnvelopeError("malformed KEK envelope")
        version, provider, key_id, key_version, payload = parts
        if version != FORMAT_VERSION:
            raise KEKEnvelopeError(f"unsupported KEK envelope version {version!r}")
        try:
            # validate=True: a lenient decoder accepts junk (whitespace, missing
            # padding, trailing bytes) and would turn a corrupt row into a
            # mysterious provider error instead of a precise local one.
            ciphertext = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise KEKEnvelopeError("KEK envelope ciphertext is not canonical base64") from exc
        return cls(
            provider=provider,
            key_id=key_id,
            key_version=key_version,
            ciphertext=ciphertext,
            format_version=version,
        )


@runtime_checkable
class KEKProvider(Protocol):
    """What the envelope is allowed to assume about a key provider.

    Four operations, no root-key accessor, and no way to ask a provider to
    encrypt with a caller-supplied key: ``wrap_dek`` and ``unwrap_dek`` are the
    only paths that move key material, and ``rewrap_dek`` exists so a KEK-only
    rotation never has to unwrap in the application at all.
    """

    name: str
    #: False for providers that must never serve production (the deterministic
    #: test provider). The factory refuses them under a production configuration;
    #: it is declared here so that refusal is a property of the provider rather
    #: than a name compared in one call site.
    production_safe: bool

    async def wrap_dek(self, dek: bytes, ctx: EncryptionContext) -> WrappedKey:
        """Wrap *dek* under the provider's root key, bound to *ctx*."""
        ...

    async def unwrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> bytes:
        """Unwrap *wrapped*, verifying the *ctx* binding. Raises on mismatch."""
        ...

    async def rewrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> WrappedKey:
        """Re-wrap under the provider's current key version, never returning the DEK."""
        ...

    async def health(self) -> ProviderHealth:
        """Report operability without touching key material."""
        ...


def validate_dek(dek: bytes) -> bytes:
    """Refuse a DEK that is not a plausible Fernet key, before any provider call."""
    if not isinstance(dek, bytes) or not 32 <= len(dek) <= MAX_DEK_BYTES:
        raise KEKEnvelopeError("DEK has an implausible length")
    return dek


__all__ = [
    "FORMAT_VERSION",
    "KNOWN_PROVIDERS",
    "MAX_DEK_BYTES",
    "PURPOSES",
    "PURPOSE_ORG_DEK",
    "EncryptionContext",
    "KEKConfigurationError",
    "KEKContextMismatchError",
    "KEKEnvelopeError",
    "KEKError",
    "KEKProvider",
    "KEKUnauthorizedError",
    "KEKUnavailableError",
    "ProviderHealth",
    "ProviderStatus",
    "WrappedKey",
    "validate_dek",
]
