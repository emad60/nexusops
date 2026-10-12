"""The KEK envelope codec and the binding it encodes.

Two properties are worth more than the other assertions here, and both are about
what the stored value *cannot* say:

* an envelope is parsed strictly — unknown version, unknown provider, missing
  field, non-canonical base64 and oversized input are all refused, because a
  half-understood envelope reaching a provider turns a data error into a
  mysterious provider failure;
* the binding is injective and versioned — organization, purpose, generation and
  format version all participate, so a wrapped DEK cannot be replayed under a
  different context by editing rows (the ciphertext simply will not verify).
"""

from __future__ import annotations

import base64
import uuid

import pytest
from app.services.kek import (
    FORMAT_VERSION,
    MAX_ENVELOPE_CHARS,
    PURPOSE_ORG_DEK,
    EncryptionContext,
    KEKEnvelopeError,
    WrappedKey,
    validate_dek,
)

ORG = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORG = uuid.UUID("22222222-2222-2222-2222-222222222222")


def test_binding_is_the_documented_canonical_string() -> None:
    ctx = EncryptionContext(org_id=ORG, purpose=PURPOSE_ORG_DEK, dek_generation=1)
    assert ctx.binding() == f"nexusops:{FORMAT_VERSION}:org-dek:{ORG}:1"


def test_binding_changes_with_organization_and_generation() -> None:
    base = EncryptionContext(org_id=ORG, dek_generation=1)
    assert base.binding() != EncryptionContext(org_id=OTHER_ORG, dek_generation=1).binding()
    assert base.binding() != EncryptionContext(org_id=ORG, dek_generation=2).binding()
    # Deterministic: the same context always binds identically.
    assert base.binding() == EncryptionContext(org_id=ORG, dek_generation=1).binding()


def test_generation_zero_is_refused() -> None:
    """Zero is the schema's "no DEK yet" marker, so it can never be a binding."""
    with pytest.raises(ValueError, match="dek_generation"):
        EncryptionContext(org_id=ORG, dek_generation=0)


def test_unknown_purpose_is_refused() -> None:
    """A purpose is a vocabulary word, not a free-form string.

    It is what stops a DEK wrapped for one use being presented as another: a
    purpose nobody declared cannot produce a binding at all.
    """
    with pytest.raises(ValueError, match="purpose"):
        EncryptionContext(org_id=ORG, purpose="dns-credential", dek_generation=1)


def test_unknown_format_version_is_refused() -> None:
    with pytest.raises(ValueError, match="format version"):
        EncryptionContext(org_id=ORG, dek_generation=1, format_version="v99")


def test_provider_context_is_base64_of_the_binding_without_line_breaks() -> None:
    """Wrap-free matters: a newline becomes a provider-side JSON parse error."""
    ctx = EncryptionContext(org_id=ORG, dek_generation=3)
    encoded = ctx.provider_context()
    assert "\n" not in encoded
    assert base64.b64decode(encoded, validate=True).decode("utf-8") == ctx.binding()


def test_wrapped_key_round_trips_through_the_wire_format() -> None:
    wrapped = WrappedKey(
        provider="vault-transit",
        key_id="nexusops-org-dek",
        key_version="3",
        ciphertext=b"vault:v3:AAAA",
    )
    encoded = wrapped.encode()
    assert encoded.startswith(f"{FORMAT_VERSION}:vault-transit:nexusops-org-dek:3:")
    assert WrappedKey.decode(encoded) == wrapped


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("", "empty"),
        ("v1:vault-transit:key:1", "missing field"),
        ("v1:vault-transit:key:1:AAAA:extra", "extra field"),
        ("v2:vault-transit:key:1:AAAA", "unknown version"),
        ("v1:cloud-kms:key:1:AAAA", "unknown provider"),
        ("v1:vault-transit::1:AAAA", "empty key id"),
        ("v1:vault-transit:key::AAAA", "empty key version"),
        ("v1:vault-transit:ke:y:1:AAAA", "separator inside a field"),
        ("v1:vault-transit:key:1:not!base64", "non-canonical base64"),
        ("v1:vault-transit:key:1:" + "A" * (MAX_ENVELOPE_CHARS + 1), "oversized"),
    ],
)
def test_decode_refuses_anything_it_does_not_fully_understand(value: str, reason: str) -> None:
    with pytest.raises(KEKEnvelopeError):
        WrappedKey.decode(value)


def test_decode_requires_a_string() -> None:
    with pytest.raises(KEKEnvelopeError):
        WrappedKey.decode(None)  # type: ignore[arg-type]


def test_wrapped_key_refuses_an_unknown_provider_at_construction() -> None:
    """The guard is at both ends: a value built in code is as suspect as a parsed one."""
    with pytest.raises(KEKEnvelopeError, match="unknown KEK provider"):
        WrappedKey(provider="cloud-kms", key_id="k", key_version="1", ciphertext=b"x")


@pytest.mark.parametrize("length", [0, 8, 31, 200])
def test_implausible_dek_lengths_are_refused(length: int) -> None:
    with pytest.raises(KEKEnvelopeError, match="length"):
        validate_dek(b"a" * length)


def test_a_fernet_sized_dek_is_accepted() -> None:
    from cryptography.fernet import Fernet

    assert validate_dek(Fernet.generate_key()) is not None
