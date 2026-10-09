"""Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in code.

Phase 2 created the table as append-only history but granted the runtime
application role ``UPDATE`` and ``DELETE`` on it, with immutability enforced only
by the service layer having no mutation path. This module pins the corrected,
database-level behavior:

* the runtime app role cannot ``UPDATE`` or ``DELETE`` a version row at all
  (both privileges are revoked);
* even a privileged (owner) role cannot rewrite history — a row-level trigger
  refuses ``UPDATE`` outright and refuses ``DELETE`` unless the parent Secret is
  already gone (the ``ON DELETE CASCADE`` that is the documented purge);
* create / rotate / rollback still append versions (`INSERT` + `SELECT` remain);
* deleting a Secret still purges its history by cascade and is audited;
* RLS still confines version rows to their organization.

The raw-SQL probes connect as the real application role with no ORM and no
session guard — the exact path a bug or a rogue worker would take.
"""

from __future__ import annotations

import pytest
from app.models import AuditLog
from sqlalchemy import select

from tests.conftest import (
    TEST_APP_PASSWORD,
    TEST_APP_ROLE,
    TEST_DATABASE_URL,
    TEST_OWNER_DATABASE_URL,
)

from .helpers import API

pytestmark = pytest.mark.integration


def _app_role_dsn() -> str:
    """A libpq DSN for the RLS-enforced application role (no ORM, no guard)."""
    url = TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    assert TEST_APP_ROLE in url and TEST_APP_PASSWORD  # sanity: app role, not owner
    return url


def _owner_dsn() -> str:
    """A libpq DSN for the migration/owner role (bypasses RLS, owns the tables)."""
    return TEST_OWNER_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")


def _probe(
    dsn: str,
    sql: str,
    params: tuple = (),
    *,
    org: str | None = None,
    expect_error: bool = False,
):
    """Run one statement with an explicit tenant GUC; optionally expect an error.

    Parameterized like any other query — these are probes, not a place to
    hand-build SQL strings from test values.
    """
    import psycopg

    with psycopg.connect(dsn) as conn:
        if org is not None:
            conn.execute("SELECT set_config('app.current_org', %s, false)", (org,))
        try:
            return conn.execute(sql, params).fetchall()
        except psycopg.errors.Error as exc:
            if not expect_error:
                raise
            return exc


async def _secret(client, owner, key: str, value: str = "v1") -> dict:
    response = await client.post(
        f"{API}/secrets",
        headers=owner["headers"],
        json={"key": key, "value": value},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_runtime_role_cannot_update_or_delete_version_rows(client, owner):
    """The app role's UPDATE/DELETE were revoked; neither statement may land."""
    created = await _secret(client, owner, "INTEGRITY_KEY")
    versions = (
        await client.get(f"{API}/secrets/{created['id']}/versions", headers=owner["headers"])
    ).json()
    version_id = versions[0]["id"]
    org = owner["active_organization_id"]

    for statement in (
        "UPDATE secret_versions SET ciphertext = 'tampered' WHERE id = %s",
        "DELETE FROM secret_versions WHERE id = %s",
    ):
        error = _probe(_app_role_dsn(), statement, (version_id,), org=org, expect_error=True)
        assert isinstance(error, Exception), f"{statement} unexpectedly succeeded"
        assert "permission denied" in str(error).lower(), f"{statement}: {error}"

    # The row is untouched and still readable.
    row = _probe(
        _app_role_dsn(),
        "SELECT ciphertext FROM secret_versions WHERE id = %s",
        (version_id,),
        org=org,
    )
    assert row and row[0][0] != "tampered"


async def test_owner_guard_blocks_rewrite_and_direct_delete(client, owner):
    """Immutability is a database guarantee, not merely a missing code path.

    The owner role bypasses RLS and owns the table, so it is the strongest
    possible actor: if the trigger holds for it, it holds for everyone.
    """
    created = await _secret(client, owner, "GUARD_KEY")
    sid = created["id"]

    update_error = _probe(
        _owner_dsn(),
        "UPDATE secret_versions SET ciphertext = 'x' WHERE secret_id = %s",
        (sid,),
        expect_error=True,
    )
    assert "append-only" in str(update_error), update_error

    delete_error = _probe(
        _owner_dsn(),
        "DELETE FROM secret_versions WHERE secret_id = %s",
        (sid,),
        expect_error=True,
    )
    assert "parent secret" in str(delete_error), delete_error

    # Both refusals rolled back: the version row is intact.
    assert _probe(
        _owner_dsn(), "SELECT count(*) FROM secret_versions WHERE secret_id = %s", (sid,)
    ) == [(1,)]


async def test_rotation_and_rollback_still_append_versions(client, owner):
    """The legitimate append paths keep working under the guard."""
    created = await _secret(client, owner, "APPEND_KEY")
    sid = created["id"]

    rotated = await client.post(
        f"{API}/secrets/{sid}/rotate", headers=owner["headers"], json={"value": "v2"}
    )
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["version"] == 2

    rolled = await client.post(
        f"{API}/secrets/{sid}/rollback", headers=owner["headers"], json={"version": 1}
    )
    assert rolled.status_code == 200, rolled.text
    assert rolled.json()["version"] == 3

    versions = (await client.get(f"{API}/secrets/{sid}/versions", headers=owner["headers"])).json()
    assert sorted(item["version"] for item in versions) == [1, 2, 3]


async def test_delete_secret_purges_versions_and_is_audited(client, owner, org_db):
    """The documented deletion policy: purging a Secret cascades its history."""
    created = await _secret(client, owner, "PURGE_KEY")
    sid = created["id"]
    await client.post(f"{API}/secrets/{sid}/rotate", headers=owner["headers"], json={"value": "v2"})
    assert _probe(
        _owner_dsn(), "SELECT count(*) FROM secret_versions WHERE secret_id = %s", (sid,)
    ) == [(2,)]

    response = await client.delete(f"{API}/secrets/{sid}", headers=owner["headers"])
    assert response.status_code == 204, response.text

    # History is gone: deletion is a hard delete that cascades (no tombstone).
    assert _probe(
        _owner_dsn(), "SELECT count(*) FROM secret_versions WHERE secret_id = %s", (sid,)
    ) == [(0,)]

    # The purge itself is recorded in the append-only audit trail.
    actions = (
        (await org_db.execute(select(AuditLog.action).where(AuditLog.resource_id == sid)))
        .scalars()
        .all()
    )
    assert "secret.delete" in actions, actions


async def test_version_rows_stay_tenant_scoped(client, owner, second_org):
    """RLS is preserved: another tenant cannot see a version row, even by id."""
    created = await _secret(client, owner, "SCOPE_KEY")
    sid = created["id"]
    org_a = owner["active_organization_id"]
    org_b = second_org["id"]

    assert _probe(
        _app_role_dsn(),
        "SELECT version FROM secret_versions WHERE secret_id = %s",
        (sid,),
        org=org_a,
    ) == [(1,)]
    # Org B: invisible by direct id.
    assert (
        _probe(
            _app_role_dsn(),
            "SELECT version FROM secret_versions WHERE secret_id = %s",
            (sid,),
            org=org_b,
        )
        == []
    )
    # No tenant GUC at all: deny everything.
    assert (
        _probe(_app_role_dsn(), "SELECT version FROM secret_versions WHERE secret_id = %s", (sid,))
        == []
    )
