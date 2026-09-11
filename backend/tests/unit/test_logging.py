"""Unit tests for app.core.logging redaction (pure functions only)."""

from __future__ import annotations

import pytest
from app.core.logging import redact_mapping

REDACTED = "[REDACTED]"


def test_flat_sensitive_keys_redacted() -> None:
    data = {"password": "hunter2", "username": "bob", "count": 3}
    out = redact_mapping(data)
    assert out["password"] == REDACTED
    assert out["username"] == "bob"
    assert out["count"] == 3


@pytest.mark.parametrize(
    ("key", "value"),
    [
        # case-insensitive substring matching
        ("Authorization", "Bearer abc"),
        ("AUTHORIZATION", "Bearer abc"),
        ("X-Api-Key", "nxo_abc"),
        ("API_TOKEN", "tok"),
        ("apikey", "k"),
        ("Private_Key", "-----BEGIN"),
        ("SESSION_ID", "s-123"),
        ("client_secret", "s"),
        ("refresh_token", "rt"),
        ("db_password", "p"),
        ("CREDENTIAL_FILE", "vault://cred"),
        ("session_cookie", "c"),
        ("my-password-hash", "h"),
    ],
)
def test_case_insensitive_substring_match(key: str, value: str) -> None:
    out = redact_mapping({key: value})
    assert out[key] == REDACTED
    # innocuous sibling untouched
    out2 = redact_mapping({key: value, "name": "n"})
    assert out2["name"] == "n"


def test_nested_dicts_are_recursed() -> None:
    data = {
        "db": {
            "host": "db.internal",
            "password": "pw",
            "options": {"api_key": "k", "retries": 2},
        },
        "user": {"email": "a@example.com"},
    }
    out = redact_mapping(data)
    assert out["db"]["host"] == "db.internal"
    assert out["db"]["password"] == REDACTED
    assert out["db"]["options"]["api_key"] == REDACTED
    assert out["db"]["options"]["retries"] == 2
    assert out["user"]["email"] == "a@example.com"


def test_sensitive_top_level_key_replaces_whole_subtree() -> None:
    data = {"credentials": {"user": "u", "nested": {"deep": True}}}
    assert redact_mapping(data)["credentials"] == REDACTED


def test_input_dict_is_not_mutated() -> None:
    data = {"password": "x", "keep": 1}
    redact_mapping(data)
    assert data == {"password": "x", "keep": 1}


def test_non_string_keys_are_handled() -> None:
    out = redact_mapping({42: "answer", "token": "t"})
    assert out[42] == "answer"
    assert out["token"] == REDACTED


def test_innocuous_payload_passes_through_intact() -> None:
    data = {"method": "GET", "path": "/servers", "status_code": 200, "duration_ms": 12.5}
    assert redact_mapping(data) == data
