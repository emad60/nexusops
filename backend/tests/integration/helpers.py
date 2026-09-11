"""Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

API = "/api/v1"
DEFAULT_PASSWORD = "Integration-Pass1"


def unique_email(prefix: str = "user") -> str:
    """A fresh, deliverable-shaped address unique to a single test.

    ``example.com`` is the IANA-reserved documentation domain — pydantic's
    email-validator accepts it, unlike RFC 6761 ``*.test`` names.
    """
    return f"{prefix}-{uuid4().hex[:12]}@example.com"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def server_payload(name: str, **overrides: Any) -> dict[str, Any]:
    """A valid POST /servers body with per-test overrides."""
    payload: dict[str, Any] = {
        "name": name,
        "hostname": f"{name}.integration.test",
        "ip_address": "10.250.0.10",
        "os_name": "Ubuntu",
        "os_version": "24.04 LTS",
        "arch": "x86_64",
        "environment": "staging",
        "location": "test-rack",
        "description": "created by the integration suite",
    }
    payload.update(overrides)
    return payload


async def register_account(
    client: httpx.AsyncClient,
    *,
    email: str | None = None,
    password: str | None = None,
    full_name: str = "Journey Owner",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Register a user; returns ``(request_payload, response_body)``."""
    payload = {
        "email": email or unique_email("owner"),
        "password": password or DEFAULT_PASSWORD,
        "full_name": full_name,
    }
    response = await client.post(f"{API}/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload, response.json()


def refresh_cookie_header(response: httpx.Response) -> str:
    """The raw Set-Cookie header carrying the refresh token."""
    from app.services.auth_service import REFRESH_COOKIE_NAME

    for header in response.headers.get_list("set-cookie"):
        if header.startswith(f"{REFRESH_COOKIE_NAME}="):
            return header
    raise AssertionError(f"no {REFRESH_COOKIE_NAME} Set-Cookie header in {response!r}")


def refresh_cookie_value(header: str) -> str:
    """Extract just the opaque token from a Set-Cookie header."""
    pair = header.split(";", 1)[0]
    _name, _, value = pair.partition("=")
    assert value, f"empty cookie value in header {header.split(';')[0]!r}"
    return value


def cookie_attributes(header: str) -> dict[str, str]:
    """Parse Set-Cookie attributes (lowercased keys, empty string for flags)."""
    attributes: dict[str, str] = {}
    for part in header.split(";")[1:]:
        key, _, value = part.strip().partition("=")
        attributes[key.lower()] = value if value else ""
    return attributes


async def login_account(client: httpx.AsyncClient, *, email: str, password: str) -> dict[str, Any]:
    """Login and unpack tokens, the raw cookie header and the user object."""
    response = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    body = response.json()
    header = refresh_cookie_header(response)
    return {
        "access_token": body["access_token"],
        "refresh_token": refresh_cookie_value(header),
        "refresh_cookie_header": header,
        "expires_in": body["expires_in"],
        "user": body["user"],
    }


def login_headers(login_result: dict[str, Any]) -> dict[str, str]:
    return bearer(login_result["access_token"])


async def register_and_login(client: httpx.AsyncClient) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bootstrap owner account + session; returns ``(credentials, login_result)``."""
    credentials, _created = await register_account(client)
    login = await login_account(
        client, email=credentials["email"], password=credentials["password"]
    )
    return credentials, login


def error_of(body: dict[str, Any]) -> dict[str, Any]:
    """Unwrap an API error envelope."""
    assert set(body.keys()) == {"error"}, f"expected a single 'error' key, got {body.keys()}"
    return body["error"]


def assert_error_code(
    body: dict[str, Any], code: str, *, exact_keys: set[str] | None = None
) -> dict[str, Any]:
    """Assert envelope shape + code; returns the inner error object."""
    error = error_of(body)
    expected_keys = exact_keys if exact_keys is not None else {"code", "message", "request_id"}
    assert set(error.keys()) == expected_keys, (
        f"error keys {sorted(error)} != {sorted(expected_keys)}"
    )
    assert error["code"] == code, f"expected code {code}, got {error['code']}"
    assert isinstance(error["message"], str) and error["message"]
    request_id = error["request_id"]
    assert isinstance(request_id, str) and len(request_id) >= 8
    return error
