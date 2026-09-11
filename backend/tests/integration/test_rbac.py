"""Role-based access control: least-privileged users are properly boxed in."""

from __future__ import annotations

import pytest

from .helpers import API, assert_error_code, bearer, login_account, server_payload, unique_email

pytestmark = pytest.mark.integration


async def _invite_user(client, owner_headers, role_name: str) -> dict:
    """Admin invites a user with *role_name*; returns their credentials dict."""
    roles = await client.get(f"{API}/roles", headers=owner_headers)
    assert roles.status_code == 200, roles.text
    payload = roles.json()
    rows = payload["items"] if isinstance(payload, dict) else payload
    role = next(r for r in rows if r["name"] == role_name)

    email = unique_email(role_name.lower())
    invited = await client.post(
        f"{API}/users",
        headers=owner_headers,
        json={
            "email": email,
            "password": "Integration-Pass1",
            "full_name": f"Test {role_name}",
            "role_id": role["id"],
        },
    )
    assert invited.status_code in (200, 201), invited.text
    return {"email": email, "password": "Integration-Pass1"}


async def test_viewer_cannot_create_but_can_read(client, owner):
    creds = await _invite_user(client, owner["headers"], "Viewer")
    session = await login_account(client, **creds)
    viewer_headers = bearer(session["access_token"])

    allowed = await client.get(f"{API}/servers", headers=viewer_headers)
    assert allowed.status_code == 200

    denied = await client.post(
        f"{API}/servers",
        headers=viewer_headers,
        json={"name": "nope", "hostname": "nope.integration.test"},
    )
    assert denied.status_code == 403
    assert_error_code(denied.json(), "PERMISSION_DENIED")


async def test_operator_reads_but_cannot_manage_secrets(client, owner):
    creds = await _invite_user(client, owner["headers"], "Operator")
    session = await login_account(client, **creds)
    operator_headers = bearer(session["access_token"])

    listed = await client.get(f"{API}/secrets", headers=operator_headers)
    assert listed.status_code == 200

    created = await client.post(
        f"{API}/secrets",
        headers=operator_headers,
        json={"key": "NOPE_KEY", "value": "hunter2-nope"},
    )
    assert created.status_code == 403
    assert_error_code(created.json(), "PERMISSION_DENIED")


async def test_scoped_api_key_cannot_exceed_its_grant(client, owner):
    """Regression: a superadmin-owned key is still limited to its scope list.

    The owner created by the bootstrap registration is a superadmin; a machine
    key minted by them with scopes=["server.read"] must act like a read-only
    credential even though its owner could do everything. Previously the
    superadmin shortcut in AuthContext.has_permission ran before the key-scope
    intersection, so any leaked "read-only" key had full platform control.
    """
    created = await client.post(
        f"{API}/api-keys",
        headers=owner["headers"],
        json={"name": "ci read-only", "scopes": ["server.read"]},
    )
    assert created.status_code == 201, created.text
    raw_key = created.json()["key"]
    key_headers = {"X-API-Key": raw_key}

    allowed = await client.get(f"{API}/servers", headers=key_headers)
    assert allowed.status_code == 200

    denied = await client.post(
        f"{API}/servers",
        headers=key_headers,
        json=server_payload("nope-via-key"),
    )
    assert denied.status_code == 403
    assert_error_code(denied.json(), "PERMISSION_DENIED")

    # Control: a wildcard-scoped key DOES act with its owner's full power.
    wild = await client.post(
        f"{API}/api-keys",
        headers=owner["headers"],
        json={"name": "ci full", "scopes": ["*"]},
    )
    assert wild.status_code == 201, wild.text
    allowed_write = await client.post(
        f"{API}/servers",
        headers={"X-API-Key": wild.json()["key"]},
        json=server_payload("yes-via-key"),
    )
    assert allowed_write.status_code in (200, 201), allowed_write.text
