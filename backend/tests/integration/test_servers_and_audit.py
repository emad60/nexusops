"""Server CRUD, cascade delete, audit trail rows and audit immutability."""

from __future__ import annotations

import uuid

import pytest
from app.models import AuditLog
from sqlalchemy import select

from .helpers import API, server_payload

pytestmark = pytest.mark.integration


async def _create_server(client, owner, name: str) -> dict:
    response = await client.post(
        f"{API}/servers", headers=owner["headers"], json=server_payload(name)
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_list_patch_delete_roundtrip(client, owner):
    created = await _create_server(client, owner, "srv-roundtrip")
    assert created["status"] == "UNKNOWN"
    assert created["enrolled"] is False
    assert created["environment"] == "staging"

    listed = await client.get(f"{API}/servers", headers=owner["headers"])
    assert listed.status_code == 200
    page = listed.json()
    assert page["total"] == 1
    assert page["items"][0]["name"] == "srv-roundtrip"

    patched = await client.patch(
        f"{API}/servers/{created['id']}",
        headers=owner["headers"],
        json={"tags": ["edge", "critical"], "location": "rack-B"},
    )
    assert patched.status_code == 200
    # Server.tags is order_by="Tag.name" — deterministic alphabetical contract.
    assert [t["name"] for t in patched.json()["tags"]] == ["critical", "edge"]
    assert patched.json()["location"] == "rack-B"

    detail = await client.get(f"{API}/servers/{created['id']}", headers=owner["headers"])
    assert detail.status_code == 200
    assert detail.json()["counts"]["containers_total"] == 0

    deleted = await client.delete(f"{API}/servers/{created['id']}", headers=owner["headers"])
    assert deleted.status_code == 204
    gone = await client.get(f"{API}/servers/{created['id']}", headers=owner["headers"])
    assert gone.status_code == 404


async def test_duplicate_name_conflicts(client, owner):
    await _create_server(client, owner, "srv-dup")
    response = await client.post(
        f"{API}/servers", headers=owner["headers"], json=server_payload("srv-dup")
    )
    assert response.status_code == 409


async def test_invalid_ip_rejected(client, owner):
    response = await client.post(
        f"{API}/servers",
        headers=owner["headers"],
        json=server_payload("srv-badip", ip_address="999.1.2.3"),
    )
    assert response.status_code == 422


async def test_audit_rows_written_for_server_actions(client, owner, db):
    created = await _create_server(client, owner, "srv-audited")
    await client.delete(f"{API}/servers/{created['id']}", headers=owner["headers"])

    rows = (
        (
            await db.execute(
                select(AuditLog)
                .where(AuditLog.action.in_(["server.create", "server.delete"]))
                .order_by(AuditLog.created_at)
            )
        )
        .scalars()
        .all()
    )
    actions = [row.action for row in rows]
    assert actions == ["server.create", "server.delete"]
    assert rows[0].actor_email == owner["credentials"]["email"]
    assert rows[0].resource_type == "server"
    assert rows[0].metadata_["name"] == "srv-audited"


async def test_audit_log_api_serializes_and_filters(client, owner):
    """The HTTP listing path — schema serialization is exercised end-to-end.

    A regression guard for the AuditOut.metadata_ aliasing bug: the first
    validation alias "metadata" resolved to the declarative Base's MetaData
    object (the reserved attribute), so every NON-EMPTY listing 500'd while
    empty results passed. No earlier test called GET /audit-logs with rows.
    """
    await _create_server(client, owner, "srv-audit-api")

    listed = await client.get(
        f"{API}/audit-logs",
        headers=owner["headers"],
        params={"action": "server.create"},
    )
    assert listed.status_code == 200, listed.text
    page = listed.json()
    assert page["total"] >= 1
    entry = next(i for i in page["items"] if i["action"] == "server.create")
    # Wire contract keeps the `metadata` key and round-trips the payload.
    assert entry["metadata"]["name"] == "srv-audit-api"

    empty = await client.get(
        f"{API}/audit-logs",
        headers=owner["headers"],
        params={"action": "server.does-not-exist"},
    )
    assert empty.status_code == 200
    assert empty.json()["items"] == []


async def test_audit_log_is_append_only(client, owner, db):
    created = await _create_server(client, owner, "srv-immutable")
    row = (
        await db.execute(select(AuditLog).where(AuditLog.action == "server.create"))
    ).scalar_one()

    # The database trigger must reject direct mutations — the guarantee does
    # not depend on application code behaving. The probe runs on a dedicated
    # raw connection so the failed statement never poisons the pooled ORM
    # connection this test session uses.
    import psycopg

    from tests.conftest import _PG_PASSWORD, _PG_PORT, _PG_USER, TEST_PG_HOST

    dsn = f"postgresql://{_PG_USER}:{_PG_PASSWORD}@{TEST_PG_HOST}:{_PG_PORT}/nexusops_test"
    with psycopg.connect(dsn) as conn:
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            conn.execute("UPDATE audit_logs SET action = 'tampered' WHERE id = %s", (str(row.id),))
        conn.rollback()

    still = await db.get(AuditLog, row.id)
    assert still.action == "server.create"
    assert created  # keeps the fixture referenced for clarity


async def test_agent_token_rotation_invalidates_previous(client, owner):
    created = await _create_server(client, owner, "srv-token")

    first = await client.post(
        f"{API}/servers/{created['id']}/agent-token", headers=owner["headers"]
    )
    assert first.status_code == 200
    token_one = first.json()["agent_token"]

    second = await client.post(
        f"{API}/servers/{created['id']}/agent-token", headers=owner["headers"]
    )
    token_two = second.json()["agent_token"]
    assert token_one.startswith("nxa_") and token_two.startswith("nxa_")
    assert token_one != token_two

    hello = {
        "agent_version": "test-agent/0.1",
        "hostname": "srv-token.integration.test",
        "os_name": "Ubuntu",
        "os_version": "24.04",
        "arch": "x86_64",
        "cpu_cores": 4,
        "memory_total_mb": 8192,
        "disk_total_gb": 200,
    }
    stale = await client.post(
        f"{API}/agent/hello", json=hello, headers={"X-Agent-Token": token_one}
    )
    assert stale.status_code == 401

    fresh = await client.post(
        f"{API}/agent/hello", json=hello, headers={"X-Agent-Token": token_two}
    )
    assert fresh.status_code == 200
    assert uuid.UUID(fresh.json()["server_id"]) == uuid.UUID(created["id"])
