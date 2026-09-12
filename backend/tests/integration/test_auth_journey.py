"""Registration bootstrap, login cookies, refresh rotation and logout."""

from __future__ import annotations

import pytest

from .helpers import (
    API,
    assert_error_code,
    bearer,
    cookie_attributes,
    login_account,
    refresh_cookie_header,
    refresh_cookie_value,
    register_account,
    unique_email,
)

pytestmark = pytest.mark.integration


async def test_first_register_bootstraps_owner(client):
    credentials, body = await register_account(client)
    user = body["user"]
    # The public schema never carries the superadmin flag (security contract);
    # bootstrap is observable through the Owner role binding and /meta.
    assert "is_superadmin" not in user
    assert user["status"] == "ACTIVE"
    assert user["role_name"] == "Owner"

    login = await login_account(
        client, email=credentials["email"], password=credentials["password"]
    )
    meta = await client.get(f"{API}/meta", headers=bearer(login["access_token"]))
    assert meta.status_code == 200
    assert meta.json()["is_superadmin"] is True


async def test_second_register_without_invite_is_rejected(client, owner):
    response = await client.post(
        f"{API}/auth/register",
        json={
            "email": unique_email("intruder"),
            "password": "Integration-Pass1",
            "full_name": "Uninvited",
        },
    )
    assert response.status_code == 403
    assert_error_code(response.json(), "INVITATION_REQUIRED")


async def test_login_sets_hardened_refresh_cookie(client, owner):
    # owner's login already happened; do a fresh one to inspect the header.
    login = await login_account(
        client, email=owner["credentials"]["email"], password=owner["credentials"]["password"]
    )
    header = login["refresh_cookie_header"]
    attrs = cookie_attributes(header)
    assert "httponly" in attrs
    # Browsers parse SameSite case-insensitively; enforce the semantic value.
    assert (attrs.get("samesite") or "").lower() == "strict"
    assert attrs.get("path") == "/api/v1/auth"
    assert login["access_token"]
    assert login["user"]["email"] == owner["credentials"]["email"]


async def test_refresh_rotates_and_replay_fails(client, owner, monkeypatch):
    """Replaying a rotated token is theft — with the grace rescue disabled.

    The grace path (next test) deliberately rescues ONE replay of the
    immediately-superseded token; this test pins refresh_grace_seconds=0 to
    verify the pure theft semantics underneath it.
    """
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "refresh_grace_seconds", 0)

    first = await login_account(
        client, email=owner["credentials"]["email"], password=owner["credentials"]["password"]
    )
    old_refresh = first["refresh_token"]

    rotated = await client.post(f"{API}/auth/refresh", cookies={_cookie_name(first): old_refresh})
    assert rotated.status_code == 200, rotated.text
    new_access = rotated.json()["access_token"]
    new_refresh = refresh_cookie_value(refresh_cookie_header(rotated))
    assert new_refresh != old_refresh

    me = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200

    replay = await client.post(f"{API}/auth/refresh", cookies={_cookie_name(first): old_refresh})
    assert replay.status_code in (401, 403)
    # Replaying a rotated token is reuse; the service revokes the session.
    assert_error_code(replay.json(), "TOKEN_REUSE")

    poisoned = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert poisoned.status_code == 401


async def test_replay_within_grace_rescues_lost_rotation(client, owner):
    """The aborted-in-flight-refresh race: rescue once, then theft again.

    A browser navigation can abort the client's in-flight refresh after the
    server committed the rotation — the rotated cookie never reaches the jar
    and the next boot replays the consumed token. That one replay must mint a
    working continuation (grace) instead of revoking the session family; the
    orphaned successor is folded away, and a SECOND replay of the same token
    is treated as the theft it now is.
    """
    first = await login_account(
        client, email=owner["credentials"]["email"], password=owner["credentials"]["password"]
    )
    cookie = {_cookie_name(first): first["refresh_token"]}

    # Rotation #1 — its response "gets lost" (this is the token the client
    # never saw): v1 consumed, v2 minted.
    lost = await client.post(f"{API}/auth/refresh", cookies=cookie)
    assert lost.status_code == 200, lost.text
    lost_cookie = refresh_cookie_value(refresh_cookie_header(lost))

    # Boot retry presents the consumed v1 again, within the grace window.
    rescued = await client.post(f"{API}/auth/refresh", cookies=cookie)
    assert rescued.status_code == 200, rescued.text
    rescued_access = rescued.json()["access_token"]
    rescued_cookie = refresh_cookie_value(refresh_cookie_header(rescued))
    assert rescued_cookie != lost_cookie  # a fresh continuation, not the lost one

    # The rescued chain works: v3 rotates normally.
    again = await client.post(f"{API}/auth/refresh", cookies={_cookie_name(first): rescued_cookie})
    assert again.status_code == 200, again.text

    # ... and the access token minted by the rescue authenticates.
    me = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {rescued_access}"})
    assert me.status_code == 200

    # Second replay of v1: the one-shot flag is spent → theft, family revoked.
    repeat = await client.post(f"{API}/auth/refresh", cookies=cookie)
    assert repeat.status_code in (401, 403)
    assert_error_code(repeat.json(), "TOKEN_REUSE")
    poisoned = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {rescued_access}"}
    )
    assert poisoned.status_code == 401

    # The orphaned successor (v2, the cookie that "got lost") is dead too:
    # presenting it must not resurrect a parallel chain.
    orphan = await client.post(f"{API}/auth/refresh", cookies={_cookie_name(first): lost_cookie})
    assert orphan.status_code in (401, 403)


async def test_grace_replay_after_window_is_theft(client, owner, db, monkeypatch):
    """Outside the grace window the rescue is gone — replay revokes the family.

    Time-travel by backdating the consumed token's updated_at (the window
    check reads it): a replay arriving after refresh_grace_seconds have
    passed since the rotation must take the theft path.
    """
    from datetime import UTC, datetime, timedelta

    from app.core.config import get_settings
    from app.core.security import hash_token
    from app.models import RefreshToken
    from sqlalchemy import update

    settings = get_settings()
    assert settings.refresh_grace_seconds > 0

    first = await login_account(
        client, email=owner["credentials"]["email"], password=owner["credentials"]["password"]
    )
    cookie = {_cookie_name(first): first["refresh_token"]}
    lost = await client.post(f"{API}/auth/refresh", cookies=cookie)
    assert lost.status_code == 200, lost.text

    stale = datetime.now(UTC) - timedelta(seconds=settings.refresh_grace_seconds + 5)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(first["refresh_token"]))
        .values(updated_at=stale)
    )
    await db.commit()

    replay = await client.post(f"{API}/auth/refresh", cookies=cookie)
    assert replay.status_code in (401, 403)
    assert_error_code(replay.json(), "TOKEN_REUSE")


async def test_logout_revokes_session(client, owner):
    second = await login_account(
        client, email=owner["credentials"]["email"], password=owner["credentials"]["password"]
    )
    logout = await client.post(
        f"{API}/auth/logout", headers={"Authorization": f"Bearer {second['access_token']}"}
    )
    assert logout.status_code == 204

    after = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"}
    )
    assert after.status_code == 401


def _cookie_name(login_result: dict) -> str:
    from app.services.auth_service import REFRESH_COOKIE_NAME

    return REFRESH_COOKIE_NAME


async def test_locked_account_response_is_indistinguishable(client, owner):
    """Regression: lockout must not leak which emails exist.

    After login_max_attempts bad passwords the account is locked — yet the
    response must carry the same INVALID_CREDENTIALS code and message as an
    unknown email. A distinct ACCOUNT_LOCKED envelope would give attackers a
    free oracle for enumerating registered addresses (5 bad passwords per
    candidate); the lock detail stays in the audit/event trail server-side.
    """
    from app.core.config import get_settings

    settings = get_settings()
    email = owner["credentials"]["email"]
    correct_password = owner["credentials"]["password"]

    unknown = await client.post(
        f"{API}/auth/login", json={"email": "nobody-here@example.com", "password": "Whatever-1"}
    )
    assert unknown.status_code == 401
    unknown_error = assert_error_code(unknown.json(), "INVALID_CREDENTIALS")

    for _ in range(settings.login_max_attempts):
        failed = await client.post(
            f"{API}/auth/login", json={"email": email, "password": "definitely-wrong"}
        )
        assert failed.status_code == 401
        assert_error_code(failed.json(), "INVALID_CREDENTIALS")

    # Locked now — even the CORRECT password gets the generic envelope.
    locked = await client.post(
        f"{API}/auth/login", json={"email": email, "password": correct_password}
    )
    assert locked.status_code == 401
    locked_error = assert_error_code(locked.json(), "INVALID_CREDENTIALS")
    assert locked_error["message"] == unknown_error["message"]
    assert locked_error["code"] == unknown_error["code"]


async def test_refresh_cookie_secure_follows_transport(client):
    """Regression: ``Secure`` must reflect the actual transport, not ENVIRONMENT.

    Tying the flag to production mode made production-over-plain-http (this
    compose stack's default shape) drop every auth cookie in the browser:
    login returned 200 but the browser refused the Secure cookie, so the
    silent refresh never worked and every reload bounced back to /login.
    """
    credentials, _body = await register_account(client)
    payload = {"email": credentials["email"], "password": credentials["password"]}

    http_login = await client.post(f"{API}/auth/login", json=payload)
    assert http_login.status_code == 200, http_login.text
    http_attrs = cookie_attributes(refresh_cookie_header(http_login))
    assert "secure" not in http_attrs, "no Secure attribute over plain http"

    https_login = await client.post(
        f"{API}/auth/login", json=payload, headers={"X-Forwarded-Proto": "https"}
    )
    assert https_login.status_code == 200, https_login.text
    https_attrs = cookie_attributes(refresh_cookie_header(https_login))
    assert https_attrs.get("secure") == "", "Secure required when the edge reports https"


async def test_meta_advertises_bootstrap_until_first_owner(client):
    """The login page learns whether to offer account creation from /meta."""
    fresh = (await client.get(f"{API}/meta")).json()["bootstrap_available"]
    assert fresh is True, "empty database must advertise bootstrap"

    await register_account(client)

    used = (await client.get(f"{API}/meta")).json()["bootstrap_available"]
    assert used is False, "bootstrap flag must drop once an owner exists"


async def test_login_records_forwarded_client_ip_in_session(client, owner):
    """Sessions must carry the real client address, not the proxy hop's peer.

    Behind Cloudflare → host nginx → edge, ``request.client.host`` is a docker
    network address; X-Forwarded-For (stamped by the outer proxy we control)
    is the only truthful source. Regression: every session used to show the
    docker gateway IP, and the login rate limiter collapsed into one bucket.
    """
    payload = {"email": owner["credentials"]["email"], "password": owner["credentials"]["password"]}
    login = await client.post(
        f"{API}/auth/login",
        json=payload,
        headers={"X-Forwarded-For": "203.0.113.7, 172.23.0.1"},
    )
    assert login.status_code == 200, login.text

    sessions = await client.get(
        f"{API}/sessions", headers=bearer(login.json()["access_token"])
    )
    assert sessions.status_code == 200, sessions.text
    ips = [item["ip_address"] for item in sessions.json()["items"]]
    assert "203.0.113.7" in ips, f"forwarded client IP not recorded: {ips}"
    assert "172.23.0.1" not in ips, "proxy hop's docker address must never be recorded"


async def test_login_ignores_spoofed_forwarded_entries(client, owner):
    """Client-injected leftmost XFF entries must not poison the session IP."""
    payload = {"email": owner["credentials"]["email"], "password": owner["credentials"]["password"]}
    login = await client.post(
        f"{API}/auth/login",
        json=payload,
        headers={"X-Forwarded-For": "6.6.6.6, 198.51.100.9, 172.23.0.1"},
    )
    assert login.status_code == 200, login.text

    sessions = await client.get(
        f"{API}/sessions", headers=bearer(login.json()["access_token"])
    )
    ips = [item["ip_address"] for item in sessions.json()["items"]]
    assert "198.51.100.9" in ips, f"outermost trusted stamp should win: {ips}"
    assert "6.6.6.6" not in ips, "spoofed leftmost entry must be ignored"
