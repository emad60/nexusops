"""Unit tests for app.core.logging redaction (pure functions only)."""

from __future__ import annotations

import json
import logging as stdlib_logging

import pytest
import structlog
from app.core.logging import configure_logging, redact_log_event, redact_mapping

from tests.conftest import FAKE_PRIVATE_KEY_PEM

REDACTED = "[REDACTED]"

#: The armored fixture's body — the part that must never survive anywhere. Kept
#: separate so a test can assert the *secret* is gone without asserting the
#: redaction marker's exact spelling everywhere.
KEY_BODY = "dGhpcyBpcyBub3QgYSByZWFsIHByaXZhdGUga2V5"


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


# --- private-key material inside nested containers ----------------------------
#
# The defect these pin: redaction recursed into dictionaries but returned a list
# untouched, whatever it held, and matched on *key names* alone. A private key
# nested in a list, or parked under an innocuous key, was stored verbatim — and
# operation results and audit metadata are both built from agent-supplied shapes
# the platform does not control.


def test_a_private_key_under_a_benign_key_is_redacted() -> None:
    """No sensitive key name involved: the PEM armor is the only signal."""
    out = redact_mapping({"body": FAKE_PRIVATE_KEY_PEM})
    assert out["body"] == REDACTED


def test_a_private_key_nested_in_a_dictionary_is_redacted() -> None:
    out = redact_mapping(
        {
            "output": {
                "inspect": {"keys": {"material": FAKE_PRIVATE_KEY_PEM}},
                "status": "exited",
            }
        }
    )
    assert out["output"]["inspect"]["keys"]["material"] == REDACTED
    assert out["output"]["status"] == "exited"
    assert KEY_BODY not in json.dumps(out)


def test_a_private_key_nested_in_a_list_is_redacted() -> None:
    out = redact_mapping({"lines": ["starting", FAKE_PRIVATE_KEY_PEM, "done"]})
    assert out["lines"] == ["starting", REDACTED, "done"]
    assert KEY_BODY not in json.dumps(out)


def test_a_private_key_in_mixed_lists_and_dictionaries_is_redacted() -> None:
    """Lists of dicts holding further lists — the shape an agent report takes."""
    data = {
        "result": {
            "logs": [
                {"stream": "stderr", "chunks": [{"text": FAKE_PRIVATE_KEY_PEM}]},
                {"stream": "stdout", "chunks": [{"text": "listening on :8000"}]},
            ]
        }
    }
    out = redact_mapping(data)
    assert out["result"]["logs"][0]["chunks"][0]["text"] == REDACTED
    assert out["result"]["logs"][1]["chunks"][0]["text"] == "listening on :8000"
    assert KEY_BODY not in json.dumps(out)


def test_a_sensitive_key_inside_a_list_of_dicts_is_redacted() -> None:
    """The key-name rule still applies at depth, not just at the top level."""
    out = redact_mapping({"items": [{"name": "a", "api_key": "k"}]})
    assert out["items"][0]["api_key"] == REDACTED
    assert out["items"][0]["name"] == "a"


def test_private_key_armor_variants_are_all_redacted() -> None:
    for kind in ("RSA PRIVATE KEY", "EC PRIVATE KEY", "OPENSSH PRIVATE KEY"):
        armored = FAKE_PRIVATE_KEY_PEM.replace("PRIVATE KEY", kind)
        out = redact_mapping({"note": armored})
        assert out["note"] == REDACTED, kind


def test_surrounding_diagnostic_text_survives_the_scrub() -> None:
    """Only the key is replaced: the reason an operator reads the row is kept."""
    out = redact_mapping({"error": f"nginx: [emerg] bad key\n{FAKE_PRIVATE_KEY_PEM}\nline 42"})
    assert out["error"].startswith("nginx: [emerg] bad key\n")
    assert out["error"].endswith("\nline 42")
    assert REDACTED in out["error"]
    assert KEY_BODY not in out["error"]


def test_prose_about_a_private_key_is_left_alone() -> None:
    """The match is the PEM armor, not the phrase — no over-redaction."""
    prose = "the private key file is readable by the agent user"
    assert redact_mapping({"note": prose})["note"] == prose


def test_certificates_and_public_keys_are_not_redacted() -> None:
    """Diagnostics that are not secrets stay useful."""
    certificate = "-----BEGIN CERTIFICATE-----\nTUlJQmZha2U=\n-----END CERTIFICATE-----"
    public = "-----BEGIN PUBLIC KEY-----\nZmFrZQ==\n-----END PUBLIC KEY-----"
    out = redact_mapping({"chain": certificate, "pub": public})
    assert out["chain"] == certificate
    assert out["pub"] == public


def test_container_types_are_preserved() -> None:
    """A redacted payload keeps the shape its consumer expects."""
    out = redact_mapping({"pair": ("a", FAKE_PRIVATE_KEY_PEM), "items": [1, 2]})
    assert out["pair"] == ("a", REDACTED)
    assert isinstance(out["pair"], tuple)
    assert isinstance(out["items"], list)


def test_nested_input_is_not_mutated() -> None:
    data = {"logs": [{"chunks": [{"text": FAKE_PRIVATE_KEY_PEM}]}], "empty": []}
    snapshot = json.dumps(data)
    redact_mapping(data)
    assert json.dumps(data) == snapshot


def test_an_innocuous_nested_payload_passes_through_intact() -> None:
    data = {
        "manifest": ["r-0123456789abcdef.conf"],
        "files": [{"path": "/etc/nexusops/nginx/routes.d/x.conf", "bytes": 512}],
        "outcome": "applied",
    }
    assert redact_mapping(data) == data


# --- the logging pipeline -----------------------------------------------------
#
# Redaction is applied by callers, and this processor is what catches the callers
# that forget: a log record is agent-supplied text in the same way an operation
# result is, and the formatted traceback can echo the very input that failed.


def test_the_log_processor_scrubs_a_private_key_at_any_depth() -> None:
    event = {
        "event": "operation_failed",
        "logger": "nexusops.agent",
        "payload": {
            "logs": [
                {"stream": "stderr", "chunks": [{"text": FAKE_PRIVATE_KEY_PEM}]},
                {"stream": "stdout", "chunks": [{"text": "listening on :8000"}]},
            ]
        },
        "api_key": "nxo_notarealkey",
    }
    out = redact_log_event(None, "warning", event)

    assert out["payload"]["logs"][0]["chunks"][0]["text"] == REDACTED
    assert out["payload"]["logs"][1]["chunks"][0]["text"] == "listening on :8000"
    assert out["api_key"] == REDACTED
    # The record is still a record: what makes it readable survives.
    assert out["event"] == "operation_failed"
    assert out["logger"] == "nexusops.agent"
    assert KEY_BODY not in json.dumps(out)


def test_the_log_processor_does_not_mutate_the_record_it_was_given() -> None:
    event = {"event": "x", "body": [{"text": FAKE_PRIVATE_KEY_PEM}]}
    snapshot = json.dumps(event)
    redact_log_event(None, "info", event)
    assert json.dumps(event) == snapshot


def test_configure_logging_installs_redaction_on_every_logging_path() -> None:
    """Both chains carry the processor: structlog's, and the foreign one.

    ``foreign_pre_chain`` is what applies to records from stdlib loggers —
    uvicorn, celery, the docker SDK — so without it a third-party line could
    write a record that the app's own logging never touched.
    """
    root = stdlib_logging.getLogger()
    handlers, level = root.handlers[:], root.level
    try:
        configure_logging(level="INFO", json_output=True)
        assert redact_log_event in structlog.get_config()["processors"]
        formatter = root.handlers[0].formatter
        assert formatter is not None
        assert redact_log_event in formatter.foreign_pre_chain
    finally:
        # Nothing else in the unit suite configures structlog, so its defaults
        # (and the root handlers pytest installed) are what was here before.
        structlog.reset_defaults()
        root.handlers[:] = handlers
        root.setLevel(level)
