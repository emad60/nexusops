"""ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).

Regression coverage for two findings:

* ``openapi.json`` and the Swagger UI were served unconditionally, while the
  configuration docs promised ``ENVIRONMENT`` "Controls docs exposure" — free
  recon for anyone attacking an internet-facing instance. Production now gets
  neither endpoint.
* ``SecurityHeadersMiddleware`` supports HSTS in production but was wired
  without its ``is_production`` flag, so ``Strict-Transport-Security`` was
  dead code and browsers never recorded an HSTS policy.
"""

from __future__ import annotations

import httpx
import pytest
from app.core.config import get_settings
from app.main import create_app


def _app_for_environment(monkeypatch: pytest.MonkeyPatch, environment: str):
    """create_app() with get_settings() patched to the given environment."""
    settings = get_settings().model_copy(update={"environment": environment})
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    return create_app()


def test_non_production_keeps_docs_and_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    application = _app_for_environment(monkeypatch, "development")
    assert application.openapi_url == "/api/v1/openapi.json"
    assert application.docs_url == "/api/docs"


def test_production_hides_docs_and_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    application = _app_for_environment(monkeypatch, "production")
    assert application.openapi_url is None
    assert application.docs_url is None


async def test_production_emits_hsts(monkeypatch: pytest.MonkeyPatch) -> None:
    application = _app_for_environment(monkeypatch, "production")
    transport = httpx.ASGITransport(app=application, client=("127.0.0.1", 54321))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        response = await c.get("/")
    assert response.status_code == 200
    assert "strict-transport-security" in response.headers
    assert "max-age=" in response.headers["strict-transport-security"]
    # The root index must not advertise docs that do not exist in production.
    assert "docs" not in response.json()


async def test_non_production_does_not_emit_hsts(monkeypatch: pytest.MonkeyPatch) -> None:
    application = _app_for_environment(monkeypatch, "development")
    transport = httpx.ASGITransport(app=application, client=("127.0.0.1", 54321))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        response = await c.get("/")
    assert "strict-transport-security" not in response.headers
