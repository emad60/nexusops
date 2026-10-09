"""Phase 3.1 — pre-organization auth events are instance-level and tenant-invisible.

A sign-in happens **before** an organization is chosen. When the account belongs
to exactly one organization the security record can be attributed to it; when it
belongs to none, or to several, there is no honest tenant answer, so the record
is filed at instance level (``org_id IS NULL``) with the user's identity
preserved — never guessed onto one organization and never dropped.

The original failure was a hard 500: the event bus refuses a named-actor event
with no organization, so a returning user with a second organization could not
log in at all (``USER_LOGIN`` had an actor but no organization). This module pins
the fix and the isolation it depends on, for zero, one and multiple memberships,
on both the success and failure paths.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
import sqlalchemy as sa
from app.models import AuditLog, SystemEvent
from app.models.enums import ActorType

from .helpers import API, DEFAULT_PASSWORD, login_account, unique_email

pytestmark = pytest.mark.integration


async def _latest_event(system_db: Any, *, type_: str, actor_id: uuid.UUID) -> SystemEvent | None:
    """Newest event of *type_* attributed to *actor_id*, read under system scope."""
    result = await system_db.execute(
        sa.select(SystemEvent)
        .where(SystemEvent.type == type_, SystemEvent.actor_id == actor_id)
        .order_by(SystemEvent.created_at.desc(), SystemEvent.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _latest_audit(system_db: Any, *, action: str, resource_id: uuid.UUID) -> AuditLog | None:
    result = await system_db.execute(
        sa.select(AuditLog)
        .where(AuditLog.action == action, AuditLog.resource_id == str(resource_id))
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _list_ids(client: Any, path: str, headers: dict[str, str]) -> list[str]:
    """Ids from a cursor- or page-paged listing, tolerant of both envelopes."""
    response = await client.get(f"{API}{path}", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    items = body["items"] if isinstance(body, dict) and "items" in body else body
    return [str(item.get("id")) for item in items]


# --- one organization: attributed to it ---------------------------------------


async def test_single_org_login_attributes_the_event_to_that_org(
    client: Any, owner: dict, system_db: Any
) -> None:
    login = await login_account(
        client, email=owner["credentials"]["email"], password=DEFAULT_PASSWORD
    )
    assert login["active_organization_id"] == owner["active_organization_id"], (
        "a single membership is unambiguous"
    )

    org_id = uuid.UUID(owner["active_organization_id"])
    event = await _latest_event(
        system_db, type_="USER_LOGIN", actor_id=uuid.UUID(owner["user"]["id"])
    )
    assert event is not None and event.org_id == org_id
    audit = await _latest_audit(
        system_db, action="auth.login", resource_id=uuid.UUID(owner["user"]["id"])
    )
    assert audit is not None and audit.org_id == org_id


# --- multiple organizations: instance level, and it must not fail -------------


async def test_multi_org_login_succeeds_and_is_filed_at_instance_level(
    client: Any, owner: dict, second_org: dict, system_db: Any
) -> None:
    """Regression: this used to be a 500 (USER_LOGIN actor without an org)."""
    response = await client.post(
        f"{API}/auth/login",
        json={"email": owner["credentials"]["email"], "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # Both memberships are returned, and no organization is *guessed* as active.
    assert len(body["organizations"]) == 2
    assert body["active_organization_id"] is None

    user_id = uuid.UUID(owner["user"]["id"])
    event = await _latest_event(system_db, type_="USER_LOGIN", actor_id=user_id)
    assert event is not None, "the sign-in must still be recorded"
    assert event.org_id is None, "it must not be attributed to an arbitrary org"
    # The column is a plain string; the value round-trips as ``"USER"``.
    assert str(event.actor_type) == ActorType.USER.value, "identity is preserved"
    assert event.actor_id == user_id

    audit = await _latest_audit(system_db, action="auth.login", resource_id=user_id)
    assert audit is not None
    assert audit.org_id is None
    assert audit.actor_id == user_id


# --- no active organization: instance level -----------------------------------


async def test_login_without_an_active_membership_is_instance_level(
    client: Any, owner: dict, system_db: Any
) -> None:
    roles = await client.get(f"{API}/roles", headers=owner["headers"])
    assert roles.status_code == 200, roles.text
    role_id = next(r["id"] for r in roles.json()["items"] if r["name"] == "Operator")

    email = unique_email("noorg")
    invited = await client.post(
        f"{API}/users",
        headers=owner["headers"],
        json={
            "email": email,
            "full_name": "No Org",
            "role_id": role_id,
            "password": DEFAULT_PASSWORD,
        },
    )
    assert invited.status_code == 201, invited.text
    user_id = uuid.UUID(invited.json()["user"]["id"])

    # Suspend the only membership: the account still exists, but has no tenant.
    suspended = await client.patch(
        f"{API}/users/{user_id}", headers=owner["headers"], json={"is_active": False}
    )
    assert suspended.status_code == 200, suspended.text

    login = await login_account(client, email=email, password=DEFAULT_PASSWORD)
    assert login["organizations"] == []
    assert login["active_organization_id"] is None

    event = await _latest_event(system_db, type_="USER_LOGIN", actor_id=user_id)
    assert event is not None and event.org_id is None
    assert event.actor_id == user_id


# --- failed logins: no 500, and the same instance-level rule ------------------


async def test_failed_login_for_a_known_multi_org_user_is_instance_level(
    client: Any, owner: dict, second_org: dict, system_db: Any
) -> None:
    response = await client.post(
        f"{API}/auth/login",
        json={"email": owner["credentials"]["email"], "password": "wrong-password-123"},
    )
    assert response.status_code == 401, response.text

    user_id = uuid.UUID(owner["user"]["id"])
    event = await _latest_event(system_db, type_="LOGIN_FAILED", actor_id=user_id)
    assert event is not None, "a denied attempt for a known account is recorded"
    assert event.org_id is None, "an ambiguous membership is never guessed"
    assert str(event.actor_type) == ActorType.USER.value


async def test_failed_login_for_an_unknown_address_is_a_system_event(
    client: Any, owner: dict, system_db: Any
) -> None:
    """No account => no actor => a system instance-level row, as before."""
    email = unique_email("ghost")
    response = await client.post(
        f"{API}/auth/login", json={"email": email, "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 401, response.text

    result = await system_db.execute(
        sa.select(SystemEvent)
        .where(SystemEvent.type == "LOGIN_FAILED")
        .order_by(SystemEvent.created_at.desc(), SystemEvent.id.desc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.org_id is None
    assert event.actor_id is None
    assert str(event.actor_type) == ActorType.SYSTEM.value


# --- isolation: instance-level records stay invisible to every tenant ---------


async def test_instance_level_auth_records_are_not_visible_to_any_tenant(
    client: Any, owner: dict, second_org: dict, system_db: Any
) -> None:
    """A NULL-org auth fact is not reachable through either organization."""
    response = await client.post(
        f"{API}/auth/login",
        json={"email": owner["credentials"]["email"], "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 200, response.text

    user_id = uuid.UUID(owner["user"]["id"])
    event = await _latest_event(system_db, type_="USER_LOGIN", actor_id=user_id)
    assert event is not None and event.org_id is None
    event_id = str(event.id)

    event_ids_a = await _list_ids(client, "/events?limit=100", owner["headers"])
    event_ids_b = await _list_ids(client, "/events?limit=100", second_org["headers"])
    assert event_id not in event_ids_a
    assert event_id not in event_ids_b

    audit = await _latest_audit(system_db, action="auth.login", resource_id=user_id)
    assert audit is not None and audit.org_id is None
    audit_id = str(audit.id)
    audit_ids_a = await _list_ids(client, "/audit-logs?limit=100", owner["headers"])
    audit_ids_b = await _list_ids(client, "/audit-logs?limit=100", second_org["headers"])
    assert audit_id not in audit_ids_a
    assert audit_id not in audit_ids_b

    # The owner's own organization still reads its own attributed rows: the
    # instance-level record is hidden, not the whole feed.
    own = await client.get(f"{API}/audit-logs?limit=100", headers=owner["headers"])
    assert own.status_code == 200
    assert own.json()["items"], "a tenant still sees its own organization's audit rows"
