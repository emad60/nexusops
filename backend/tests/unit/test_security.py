"""Unit tests for app.core.security — no database or Redis required."""

from __future__ import annotations

import hashlib
import uuid

import jwt as pyjwt
import pytest
from app.core.config import get_settings
from app.core.errors import Unauthorized
from app.core.security import (
    create_access_token,
    decode_access_token,
    decrypt_str,
    digest_of,
    encrypt_str,
    generate_agent_token,
    generate_api_key,
    generate_refresh_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    tokens_equal,
    verify_password,
)

# --- Password hashing ---------------------------------------------------------


def test_password_roundtrip() -> None:
    digest = hash_password("S3cure-Passw0rd!")
    assert digest != "S3cure-Passw0rd!"
    assert verify_password(digest, "S3cure-Passw0rd!") is True


def test_wrong_password_rejected() -> None:
    digest = hash_password("correct-horse")
    assert verify_password(digest, "incorrect-horse") is False


def test_verify_malformed_hash_is_false_not_raise() -> None:
    assert verify_password("not-an-argon2-hash", "whatever") is False
    assert verify_password("", "whatever") is False


def test_fresh_hash_does_not_need_rehash() -> None:
    digest = hash_password("another-password")
    assert password_needs_rehash(digest) is False


def test_rehash_garbage_hash_is_false() -> None:
    assert password_needs_rehash("garbage") is False


def test_hashes_are_salted() -> None:
    # Same plaintext must produce different stored hashes (salted argon2).
    assert hash_password("same-input") != hash_password("same-input")


# --- Opaque token generators ----------------------------------------------------


def test_refresh_token_shape_and_hash_separation() -> None:
    raw, stored = generate_refresh_token()
    assert raw != stored  # never store the raw value
    assert len(raw) >= 48  # 48 bytes of entropy, urlsafe base64
    assert stored == hash_token(raw)
    assert len(stored) == 64 and all(c in "0123456789abcdef" for c in stored)


def test_token_generators_are_unique() -> None:
    refresh = {generate_refresh_token()[0] for _ in range(200)}
    keys = {generate_api_key()[0] for _ in range(200)}
    agents = {generate_agent_token()[0] for _ in range(200)}
    assert len(refresh) == 200
    assert len(keys) == 200
    assert len(agents) == 200


def test_api_key_prefix_convention() -> None:
    raw, prefix, stored = generate_api_key()
    assert raw.startswith("nxo_")
    assert prefix == raw[:12]
    assert len(prefix) == 12
    assert stored == hash_token(raw)


def test_agent_token_prefix_convention() -> None:
    raw, prefix, stored = generate_agent_token()
    assert raw.startswith("nxa_")
    assert prefix == raw[:12]
    assert stored == hash_token(raw)


def test_api_and_agent_prefixes_differ() -> None:
    api_raw, _, _ = generate_api_key()
    agent_raw, _, _ = generate_agent_token()
    assert api_raw[:4] != agent_raw[:4]


def test_hash_token_stability() -> None:
    assert hash_token("value") == hash_token("value")
    assert hash_token("value") != hash_token("valuE")
    expected = hashlib.sha256(b"value").hexdigest()
    assert hash_token("value") == expected


def test_tokens_equal_behaviour() -> None:
    assert tokens_equal("abc", "abc") is True
    assert tokens_equal("abc", "abd") is False
    assert tokens_equal("a" * 100, "a" * 100) is True
    assert tokens_equal("a" * 100, "b" * 100) is False


# --- Symmetric encryption -------------------------------------------------------


@pytest.mark.parametrize(
    "plaintext",
    ["", "short", "unicode: schnecke-üncode ✓", "x" * 10_000],
)
def test_encrypt_decrypt_roundtrip(plaintext: str) -> None:
    ciphertext = encrypt_str(plaintext)
    assert ciphertext != plaintext or plaintext == ""
    assert decrypt_str(ciphertext) == plaintext


def test_encryption_is_non_deterministic() -> None:
    assert encrypt_str("same") != encrypt_str("same")


def test_decrypt_with_wrong_ciphertext_raises_value_error() -> None:
    with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
        decrypt_str("definitely-not-a-fernet-token")


# --- Digests ---------------------------------------------------------------------


def test_digest_length_and_determinism() -> None:
    assert len(digest_of("deploy-manifest")) == 12
    assert len(digest_of("deploy-manifest", length=32)) == 32
    assert digest_of("abc") == digest_of("abc")
    assert digest_of("abc") != digest_of("abd")


def test_digest_is_keyed_not_plain_sha256() -> None:
    # Regression: the digest must be an HMAC keyed from ENCRYPTION_KEY, not an
    # unsalted truncated SHA-256 — a plain hash returned over the metadata API
    # is an offline dictionary/confirmation oracle for low-entropy secrets.
    import hmac as hmac_mod

    key = hashlib.sha256(get_settings().encryption_key.encode()).digest()
    expected = hmac_mod.new(key, b"abc", hashlib.sha256).hexdigest()[:12]
    assert digest_of("abc") == expected
    assert digest_of("abc") != hashlib.sha256(b"abc").hexdigest()[:12]


# --- JWT access tokens ------------------------------------------------------------


def test_access_token_roundtrip() -> None:
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    token, jti = create_access_token(
        user_id=user_id, session_id=session_id, email="user@example.com"
    )
    assert jti and len(jti) >= 16
    claims = decode_access_token(token)
    assert claims["sub"] == str(user_id)
    assert claims["sid"] == str(session_id)
    assert claims["email"] == "user@example.com"
    assert claims["jti"] == jti
    assert claims["typ"] == "access"


def test_expired_access_token_rejected() -> None:
    token, _ = create_access_token(
        user_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        email="user@example.com",
        ttl_seconds=-10,
    )
    with pytest.raises(Unauthorized):
        decode_access_token(token)


def test_tampered_access_token_rejected() -> None:
    token, _ = create_access_token(
        user_id=uuid.uuid4(), session_id=uuid.uuid4(), email="user@example.com"
    )
    header, body, signature = token.split(".")
    forged_body = body[:-2] + ("aa" if not body.endswith("aa") else "bb")
    with pytest.raises(Unauthorized):
        decode_access_token(f"{header}.{forged_body}.{signature}")


def test_garbage_token_rejected() -> None:
    with pytest.raises(Unauthorized):
        decode_access_token("three.dot.token")


def test_wrong_token_type_rejected() -> None:
    settings = get_settings()
    token = pyjwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "sid": str(uuid.uuid4()),
            "typ": "refresh",
            "iss": "nexusops",
            "exp": 4_102_444_800,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(Unauthorized, match="token type"):
        decode_access_token(token)


def test_wrong_issuer_rejected() -> None:
    settings = get_settings()
    token = pyjwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "sid": str(uuid.uuid4()),
            "typ": "access",
            "iss": "someone-else",
            "exp": 4_102_444_800,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(Unauthorized):
        decode_access_token(token)


def test_missing_required_claim_rejected() -> None:
    settings = get_settings()
    token = pyjwt.encode(
        {"sub": str(uuid.uuid4()), "typ": "access", "iss": "nexusops", "exp": 4_102_444_800},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(Unauthorized):
        decode_access_token(token)
