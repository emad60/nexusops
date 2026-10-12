"""The deterministic provider: reproducible, binding-aware, and never a real key.

The point of these tests is not that a test fixture works. It is that the
*failure modes* the envelope depends on are modelled by the test provider exactly
as the production adapter produces them: a wrong organization or generation fails
authentication rather than being compared field-by-field, and a rewrap preserves
the binding across a version change without the DEK ever leaving the call.
"""

from __future__ import annotations

import uuid

import pytest
import structlog
from app.services.kek import (
    EncryptionContext,
    KEKContextMismatchError,
    KEKEnvelopeError,
    ProviderStatus,
    WrappedKey,
)
from app.services.kek.deterministic import DeterministicKEKProvider
from cryptography.fernet import Fernet

ORG = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORG = uuid.UUID("22222222-2222-2222-2222-222222222222")


async def test_wrap_unwrap_round_trip() -> None:
    provider = DeterministicKEKProvider()
    dek = Fernet.generate_key()
    ctx = EncryptionContext(org_id=ORG, dek_generation=1)
    wrapped = await provider.wrap_dek(dek, ctx)
    assert wrapped.provider == "test"
    assert wrapped.key_version == "1"
    assert await provider.unwrap_dek(wrapped, ctx) == dek


async def test_ciphertext_is_deterministic_across_instances() -> None:
    """Fixtures and assertions stay stable; nothing here needs randomness."""
    dek = Fernet.generate_key()
    ctx = EncryptionContext(org_id=ORG, dek_generation=1)
    first = await DeterministicKEKProvider().wrap_dek(dek, ctx)
    second = await DeterministicKEKProvider().wrap_dek(dek, ctx)
    assert first.encode() == second.encode()


async def test_a_different_organization_cannot_unwrap() -> None:
    provider = DeterministicKEKProvider()
    dek = Fernet.generate_key()
    wrapped = await provider.wrap_dek(dek, EncryptionContext(org_id=ORG, dek_generation=1))
    with pytest.raises(KEKContextMismatchError):
        await provider.unwrap_dek(wrapped, EncryptionContext(org_id=OTHER_ORG, dek_generation=1))


async def test_a_different_generation_cannot_unwrap() -> None:
    provider = DeterministicKEKProvider()
    dek = Fernet.generate_key()
    wrapped = await provider.wrap_dek(dek, EncryptionContext(org_id=ORG, dek_generation=1))
    with pytest.raises(KEKContextMismatchError):
        await provider.unwrap_dek(wrapped, EncryptionContext(org_id=ORG, dek_generation=2))


async def test_tampered_ciphertext_fails_the_same_way_as_a_wrong_context() -> None:
    """A corrupted envelope is an authentication failure, not a special case."""
    provider = DeterministicKEKProvider()
    ctx = EncryptionContext(org_id=ORG, dek_generation=1)
    wrapped = await provider.wrap_dek(Fernet.generate_key(), ctx)
    tampered = WrappedKey(
        provider=wrapped.provider,
        key_id=wrapped.key_id,
        key_version=wrapped.key_version,
        ciphertext=bytes([wrapped.ciphertext[0] ^ 0xFF]) + wrapped.ciphertext[1:],
    )
    with pytest.raises(KEKContextMismatchError):
        await provider.unwrap_dek(tampered, ctx)


async def test_an_envelope_from_another_provider_is_refused_before_any_crypto() -> None:
    provider = DeterministicKEKProvider()
    foreign = WrappedKey(
        provider="vault-transit",
        key_id="nexusops-org-dek",
        key_version="1",
        ciphertext=b"vault:v1:AAAA",
    )
    with pytest.raises(KEKEnvelopeError, match="not by this provider"):
        await provider.unwrap_dek(foreign, EncryptionContext(org_id=ORG, dek_generation=1))


async def test_rewrap_is_a_no_op_while_the_version_is_current() -> None:
    provider = DeterministicKEKProvider()
    ctx = EncryptionContext(org_id=ORG, dek_generation=1)
    wrapped = await provider.wrap_dek(Fernet.generate_key(), ctx)
    assert await provider.rewrap_dek(wrapped, ctx) == wrapped


async def test_rewrap_moves_the_version_and_preserves_the_binding() -> None:
    """The KEK-rotation invariant: new version, same binding, no DEK returned."""
    provider = DeterministicKEKProvider()
    dek = Fernet.generate_key()
    ctx = EncryptionContext(org_id=ORG, dek_generation=1)
    wrapped = await provider.wrap_dek(dek, ctx)

    provider.rotate()
    rewrapped = await provider.rewrap_dek(wrapped, ctx)

    assert rewrapped.key_version == "2"
    assert rewrapped.provider == wrapped.provider
    assert rewrapped.ciphertext != wrapped.ciphertext
    assert await provider.unwrap_dek(rewrapped, ctx) == dek
    # The binding survived the move: the same ciphertext under the wrong
    # organization is still refused.
    with pytest.raises(KEKContextMismatchError):
        await provider.unwrap_dek(rewrapped, EncryptionContext(org_id=OTHER_ORG, dek_generation=1))
    # And the old ciphertext still unwraps: rotation is not destructive.
    assert await provider.unwrap_dek(wrapped, ctx) == dek


async def test_rewrap_requires_the_binding_too() -> None:
    provider = DeterministicKEKProvider()
    ctx = EncryptionContext(org_id=ORG, dek_generation=1)
    wrapped = await provider.wrap_dek(Fernet.generate_key(), ctx)
    provider.rotate()
    with pytest.raises(KEKContextMismatchError):
        await provider.rewrap_dek(wrapped, EncryptionContext(org_id=OTHER_ORG, dek_generation=1))


async def test_health_is_ok_but_declares_itself_unsafe_for_production() -> None:
    provider = DeterministicKEKProvider()
    health = await provider.health()
    assert health.status is ProviderStatus.OK
    assert health.provider == "test"
    assert provider.production_safe is False


async def test_no_log_record_carries_the_dek() -> None:
    """A failing call must not log the material it was handling."""
    provider = DeterministicKEKProvider()
    dek = Fernet.generate_key()
    ctx = EncryptionContext(org_id=ORG, dek_generation=1)
    wrapped = await provider.wrap_dek(dek, ctx)
    with structlog.testing.capture_logs() as logs:
        with pytest.raises(KEKContextMismatchError):
            await provider.unwrap_dek(
                wrapped, EncryptionContext(org_id=OTHER_ORG, dek_generation=1)
            )
    rendered = str(logs)
    assert dek.decode() not in rendered
    assert wrapped.ciphertext.hex() not in rendered


async def test_an_implausible_dek_never_reaches_the_aead() -> None:
    provider = DeterministicKEKProvider()
    with pytest.raises(KEKEnvelopeError):
        await provider.wrap_dek(b"short", EncryptionContext(org_id=ORG, dek_generation=1))
