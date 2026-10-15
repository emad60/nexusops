"""The payload binding: what a stored ciphertext belongs to, and what it refuses.

Every secret Phase 5 stores — a certificate key, a chain, a DNS credential, an ACME
account key — is encrypted under the organization DEK, and the interesting property
is not that Fernet round-trips. It is that the value is **bound to its row**: the
organization, the purpose, the record id and the DEK generation are inside the
stored value twice, and a value that was moved, re-labelled or read under the wrong
generation fails as a named error rather than decrypted into the wrong place. The
claims below pin down that behaviour, including the one place the guarantee is
weaker than it sounds (Fernet has no associated data, so the forged-binding check
happens after the token authenticates — see the module docstring).

Nothing here touches the database or a KEK provider: the context binding is a pure
function of bytes and a caller-supplied key, so it is testable without one.
"""

from __future__ import annotations

import uuid

import pytest
from app.services.payload_crypto import (
    PAYLOAD_FORMAT,
    PAYLOAD_PURPOSES,
    PURPOSE_ACME_ACCOUNT_KEY,
    PURPOSE_CERTIFICATE_CHAIN,
    PURPOSE_CERTIFICATE_KEY,
    PURPOSE_DNS_CREDENTIALS,
    PayloadContext,
    PayloadContextMismatch,
    PayloadDecryptionError,
    PayloadEnvelopeError,
    PayloadError,
    decrypt,
    decrypt_str,
    encrypt,
    fingerprint,
)
from cryptography.fernet import Fernet

ORG = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORG = uuid.UUID("22222222-2222-2222-2222-222222222222")
RECORD = uuid.UUID("33333333-3333-3333-3333-333333333333")
OTHER_RECORD = uuid.UUID("44444444-4444-4444-4444-444444444444")

#: A real Fernet key: the module is given one by the envelope service, and a
#: fake-sized key would fail before any of the assertions here could run.
KEY = Fernet.generate_key()

SECRET = b'{"api_token": "cf-token-that-must-never-be-echoed"}'


def context(
    *,
    org_id: uuid.UUID = ORG,
    purpose: str = PURPOSE_DNS_CREDENTIALS,
    record_id: uuid.UUID = RECORD,
    deke_id: int = 1,
) -> PayloadContext:
    return PayloadContext(org_id=org_id, purpose=purpose, record_id=record_id, deke_id=deke_id)


# --- the header is the binding, in a fixed shape ------------------------------


def test_the_header_is_the_documented_canonical_string() -> None:
    """The stored value's shape is an interface: a future reader parses it."""
    assert context().header() == f"{PAYLOAD_FORMAT}:{ORG}:{PURPOSE_DNS_CREDENTIALS}:{RECORD}:1"


def test_every_declared_purpose_is_in_the_closed_set() -> None:
    declared = {
        PURPOSE_CERTIFICATE_KEY,
        PURPOSE_CERTIFICATE_CHAIN,
        PURPOSE_DNS_CREDENTIALS,
        PURPOSE_ACME_ACCOUNT_KEY,
    }
    assert declared == set(PAYLOAD_PURPOSES)
    for purpose in sorted(declared):
        assert context(purpose=purpose).header().split(":")[2] == purpose


# --- round trip ---------------------------------------------------------------


def test_a_payload_round_trips_under_its_own_context() -> None:
    stored = encrypt(Fernet(KEY), context(), SECRET)
    assert decrypt(Fernet(KEY), context(), stored) == SECRET
    assert decrypt_str(Fernet(KEY), context(), stored) == SECRET.decode()


def test_encrypt_is_not_a_deterministic_function_of_the_plaintext() -> None:
    """Two writes of the same secret must not produce the same stored value.

    A deterministic ciphertext would turn the column into a lookup table: an
    attacker who could read it could confirm a guessed token without a key.
    """
    first = encrypt(Fernet(KEY), context(), SECRET)
    second = encrypt(Fernet(KEY), context(), SECRET)
    assert first != second
    assert decrypt(Fernet(KEY), context(), first) == SECRET
    assert decrypt(Fernet(KEY), context(), second) == SECRET


# --- the context is enforced before the key is used ---------------------------


@pytest.mark.parametrize(
    "presented",
    [
        context(org_id=OTHER_ORG),
        context(purpose=PURPOSE_ACME_ACCOUNT_KEY),
        context(record_id=OTHER_RECORD),
        context(deke_id=2),
    ],
    ids=["another organization", "another purpose", "another record", "another generation"],
)
def test_a_ciphertext_moved_to_another_context_is_refused(presented: PayloadContext) -> None:
    stored = encrypt(Fernet(KEY), context(), SECRET)
    with pytest.raises(PayloadContextMismatch) as raised:
        decrypt(Fernet(KEY), presented, stored)
    assert "different organization, purpose, record or DEK generation" in str(raised.value)


def test_the_context_is_checked_before_any_decryption_is_attempted() -> None:
    """A mismatch must not depend on having the right key to be detected.

    This is what makes the failure a *placement* error rather than a key error: the
    caller is handed a value that cannot belong to it, whatever key it holds.
    """
    stored = encrypt(Fernet(KEY), context(), SECRET)
    with pytest.raises(PayloadContextMismatch):
        decrypt(Fernet(Fernet.generate_key()), context(purpose=PURPOSE_CERTIFICATE_KEY), stored)


def test_the_wrong_key_is_a_decryption_failure_and_not_a_context_mismatch() -> None:
    """The two errors are distinct so an operator can tell the causes apart.

    (§6.5: a generation whose material cannot be decrypted is marked failed and
    re-issued — a decision that is impossible if both failures look the same.)
    """
    stored = encrypt(Fernet(KEY), context(), SECRET)
    with pytest.raises(PayloadDecryptionError) as raised:
        decrypt(Fernet(Fernet.generate_key()), context(), stored)
    assert "DEK" in str(raised.value)


def test_a_re_labelled_ciphertext_is_caught_by_the_authenticated_binding() -> None:
    """The forgeable case: the outer header is rewritten, the token is not.

    Anyone who can write the column can move a value to another purpose or record
    by editing the header. The authenticated copy inside the token disagrees, and
    that is the copy that decides — so the forged read fails instead of returning
    key material to a row it was not issued for.
    """
    fernet = Fernet(KEY)
    stored = encrypt(fernet, context(), SECRET)
    _, _, token = stored.rpartition(":")
    forged_context = context(purpose=PURPOSE_ACME_ACCOUNT_KEY)
    forged = f"{forged_context.header()}:{token}"

    with pytest.raises(PayloadContextMismatch) as raised:
        decrypt(fernet, forged_context, forged)
    assert "authenticated binding" in str(raised.value)


# --- the stored value is parsed strictly --------------------------------------


@pytest.mark.parametrize(
    ("stored", "reason"),
    [
        ("", "empty value"),
        ("nxp1", "no token at all"),
        (":not-a-real-header", "missing fields"),
        (f"nxp1:{ORG}:{PURPOSE_DNS_CREDENTIALS}:{RECORD}", "header without a ciphertext"),
        (f"nxp1:{ORG}:{PURPOSE_DNS_CREDENTIALS}:{RECORD}:1:", "empty ciphertext"),
        (f"nxp2:{ORG}:{PURPOSE_DNS_CREDENTIALS}:{RECORD}:1:AAAA", "unknown format tag"),
        (f"nxp1:{ORG}:{PURPOSE_DNS_CREDENTIALS}:{RECORD}:zero:AAAA", "non-numeric generation"),
        (f"nxp1:not-a-uuid:{PURPOSE_DNS_CREDENTIALS}:{RECORD}:1:AAAA", "unparsable org id"),
        (f"nxp1:{ORG}:{PURPOSE_DNS_CREDENTIALS}:not-a-uuid:1:AAAA", "unparsable record id"),
    ],
)
def test_a_malformed_envelope_is_refused_and_not_guessed_at(stored: str, reason: str) -> None:
    with pytest.raises(PayloadEnvelopeError):
        decrypt(Fernet(KEY), context(), stored)


def test_an_altered_token_is_a_decryption_failure() -> None:
    """A byte changed inside the token is a forgery, not a placement mistake."""
    stored = encrypt(Fernet(KEY), context(), SECRET)
    header, _, token = stored.rpartition(":")
    flipped = "A" if token[0] != "A" else "B"
    with pytest.raises(PayloadDecryptionError):
        decrypt(Fernet(KEY), context(), f"{header}:{flipped}{token[1:]}")


def test_a_payload_that_is_not_utf8_is_refused_by_the_text_helper() -> None:
    """``decrypt_str`` is for credentials and PEM, so binary is a writer bug."""
    fernet = Fernet(KEY)
    stored = encrypt(fernet, context(), b"\xff\xfe\x00")
    assert decrypt(fernet, context(), stored) == b"\xff\xfe\x00"
    with pytest.raises(PayloadDecryptionError) as raised:
        decrypt_str(fernet, context(), stored)
    assert "UTF-8" in str(raised.value)


# --- the context itself cannot be nonsense ------------------------------------


def test_an_undeclared_purpose_cannot_be_bound() -> None:
    """A purpose is a vocabulary word: an unlisted one is a bug being announced."""
    with pytest.raises(PayloadEnvelopeError) as raised:
        context(purpose="dns-credential")
    assert "unknown payload purpose" in str(raised.value)


@pytest.mark.parametrize("deke_id", [0, -1])
def test_generation_zero_and_negative_generations_are_refused(deke_id: int) -> None:
    """``0`` is the schema's "no DEK yet", so it never encrypted anything."""
    with pytest.raises(PayloadEnvelopeError) as raised:
        context(deke_id=deke_id)
    assert "DEK generation" in str(raised.value)


# --- fingerprints -------------------------------------------------------------


def test_a_fingerprint_is_domain_separated_and_stable() -> None:
    assert fingerprint(SECRET, kind="dns.credentials") == fingerprint(
        SECRET, kind="dns.credentials"
    )
    assert len(fingerprint(SECRET, kind="dns.credentials")) == 64
    # The same bytes stored as two different things are two different handles, so a
    # fingerprint from one subsystem cannot be compared against another's.
    assert fingerprint(SECRET, kind="dns.credentials") != fingerprint(
        SECRET, kind="acme.account_key"
    )
    assert fingerprint(SECRET, kind="dns.credentials") != fingerprint(
        SECRET + b"x", kind="dns.credentials"
    )
    # Never the value itself, in any form.
    assert "cf-token" not in fingerprint(SECRET, kind="dns.credentials")


def test_a_fingerprint_needs_a_kind() -> None:
    with pytest.raises(PayloadError, match="kind"):
        fingerprint(SECRET, kind="")
