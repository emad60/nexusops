"""Cryptographic primitives: password hashing, tokens, symmetric encryption."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken
from jwt import PyJWTError, decode, encode

from app.core.config import get_settings
from app.core.errors import Unauthorized

_pwd_hasher = PasswordHasher()  # argon2id defaults (m=64MiB, t=3, p=4)


# --- Passwords ---------------------------------------------------------------


def hash_password(password: str) -> str:
    return _pwd_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _pwd_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed/stale hash — treat as mismatch, never leak
        return False


def password_needs_rehash(password_hash: str) -> bool:
    try:
        return _pwd_hasher.check_needs_rehash(password_hash)
    except Exception:
        return False


# --- JWT access tokens --------------------------------------------------------


def create_access_token(
    *, user_id: uuid.UUID, session_id: uuid.UUID, email: str, ttl_seconds: int | None = None
) -> tuple[str, str]:
    """Return ``(token, jti)`` for a short-lived access token."""
    settings = get_settings()
    now = datetime.now(UTC)
    jti = secrets.token_urlsafe(16)
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "email": email,
        "jti": jti,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds or settings.access_token_ttl)).timestamp()),
        "iss": "nexusops",
    }
    token = encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, jti


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode + validate an access token or raise :class:`Unauthorized`."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer="nexusops",
            options={"require": ["exp", "sub", "sid", "typ"]},
        )
    except PyJWTError as exc:
        raise Unauthorized("Invalid or expired access token") from exc
    if payload.get("typ") != "access":
        raise Unauthorized("Wrong token type")
    return payload


# --- Opaque tokens (refresh / api keys / agent enrollment) ---------------------


def generate_refresh_token() -> tuple[str, str]:
    """Return ``(raw_token, sha256_hex_hash)``."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)


def generate_api_key() -> tuple[str, str, str]:
    """Return ``(raw_key, prefix, hash)``. Keys look like ``nxo_live_<random>``."""
    raw = f"nxo_{secrets.token_urlsafe(30)}"
    return raw, raw[:12], hash_token(raw)


def generate_agent_token() -> tuple[str, str, str]:
    raw = f"nxa_{secrets.token_urlsafe(30)}"
    return raw, raw[:12], hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def tokens_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


# --- Symmetric encryption (secrets at rest) ------------------------------------

_fernet_cache: dict[str, Fernet] = {}


def _fernet() -> Fernet:
    settings = get_settings()
    key = settings.encryption_key
    box = _fernet_cache.get(key)
    if box is None:
        box = Fernet(key.encode())
        _fernet_cache[key] = box
    return box


def encrypt_str(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_str(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "Decryption failed — ENCRYPTION_KEY does not match the one used to encrypt "
            "this value. Restore the original key or re-create the affected secrets."
        ) from exc


def digest_of(value: str, length: int = 12) -> str:
    """Short non-reversible digest used for change detection display."""
    return hashlib.sha256(value.encode()).hexdigest()[:length]
