"""Regression: the catch-all 500 handler must not log raw exception text.

SQLAlchemy statement errors embed a repr of their bound parameters in
``str(exc)`` — password hashes, secret ciphertext, refresh-token hashes — so
logging the message verbatim would dump credential material into the
persistent log sink (key-name redaction cannot scrub an exception string).
The handler therefore logs the exception CLASS alongside ``exc_info``.
"""

from __future__ import annotations

from app.core import errors as errors_mod
from fastapi import FastAPI
from fastapi.testclient import TestClient


class _SpyLogger:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def error(self, event: str, **kwargs: object) -> None:
        self.calls.append((event, kwargs))

    def warning(self, event: str, **kwargs: object) -> None:  # pragma: no cover
        self.calls.append((event, kwargs))


def test_unhandled_exception_handler_logs_class_not_message(monkeypatch) -> None:
    spy = _SpyLogger()
    monkeypatch.setattr(errors_mod, "log", spy)

    application = FastAPI()
    errors_mod.register_exception_handlers(application)

    @application.get("/boom")
    async def boom():
        raise RuntimeError(
            "INSERT INTO secrets ... password_hash=$argon2id… ciphertext=gAAAAA token_hash=abc"
        )

    client = TestClient(application, raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"

    assert spy.calls, "handler must log the failure"
    event, kwargs = spy.calls[-1]
    assert event == "unhandled_exception"
    assert kwargs["error"] == "RuntimeError"
    flattened = str(kwargs)
    assert "argon2id" not in flattened
    assert "gAAAAA" not in flattened
    assert "token_hash=abc" not in flattened
