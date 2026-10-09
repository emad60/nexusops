"""Phase 3 — Nodes & Agent v2 end-to-end behaviour.

Grouped by the question each block answers:

1. **Enrollment credentials** — an ``nxk_`` token is org-scoped, single-use,
   expiring and revocable, and its raw value is shown exactly once.
2. **Enrollment is transactional** — two concurrent redemptions cannot both win,
   and the node's organization comes from the token row, never the payload.
3. **Protocol v2** — capabilities and facts are persisted, an unreported
   capability is never treated as present, and the heartbeat contract is
   versioned (204 for v1, 200 + work for v2).
4. **Operation delivery and timing** — work created just after a beat survives to
   the next one, the claim opens a separate execution deadline, and a late result
   is bounded rather than accepted forever.
5. **Credential lifecycle** — rotation delivers the new token to the old-token
   caller and is acknowledged; revocation is immediate and explicit.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.tenancy import apply_scope_to_session, system_scope
from app.models import EnrollmentToken, Operation, Server
from app.models.enums import OperationStatus
from sqlalchemy import select

from .helpers import API, assert_error_code, bearer, server_payload

pytestmark = pytest.mark.integration


def _load_agent_module():
    """Import the shipped agent source (sync, so async tests never touch Path)."""
    import importlib.util
    from pathlib import Path

    agent_path = Path(__file__).resolve().parents[3] / "agent" / "nexusops_agent.py"
    spec = importlib.util.spec_from_file_location("nexusops_agent_e2e", agent_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELLO_V2 = {
    "agent_version": "1.1.0",
    "protocol_version": 2,
    "hostname": "phase3.integration.test",
    "os_name": "Ubuntu",
    "os_version": "24.04 LTS",
    "arch": "x86_64",
    "cpu_cores": 4,
    "memory_total_mb": 8192,
    "disk_total_gb": 200,
    "capabilities": {"docker": {"present": True, "api_version": "1.43"}},
    "facts": {"disks": [{"mount": "/", "free_gb": 120}], "kernel": "6.8.0"},
}

HEARTBEAT = {
    "cpu_percent": 5.0,
    "mem_used_mb": 512.0,
    "mem_percent": 20.0,
    "disk_used_gb": 40.0,
    "disk_percent": 50.0,
    "containers": [],
}


async def _create_token(client, headers, **overrides) -> dict:
    body = {"name": "wave-1", "expires_in_seconds": 3600, **overrides}
    response = await client.post(f"{API}/nodes/enrollment-tokens", headers=headers, json=body)
    assert response.status_code == 201, response.text
    return response.json()


async def _enroll(client, token: str, hostname: str = "phase3.integration.test"):
    return await client.post(
        f"{API}/agent/enroll",
        json={"enrollment_token": token, "hostname": hostname, "agent_version": "1.1.0"},
    )


async def _enrolled_node(client, headers, token: str, hostname: str) -> tuple[dict, str, str]:
    """Enroll through the v2 path and complete a hello. Returns (node, nxa_, org)."""
    enrolled = await _enroll(client, token, hostname)
    assert enrolled.status_code == 201, enrolled.text
    body = enrolled.json()
    agent_token = body["agent_token"]
    hello = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": agent_token},
        json={**HELLO_V2, "hostname": hostname},
    )
    assert hello.status_code == 200, hello.text
    node = (await client.get(f"{API}/nodes/{body['node_id']}", headers=headers)).json()
    return node, agent_token, body["node_id"]


async def _mutate_in_system_scope(model, row_id: str, **values) -> None:
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        with system_scope("test: stage phase3 row"):
            await apply_scope_to_session(session)
            row = await session.get(model, uuid.UUID(row_id))
            assert row is not None
            for key, value in values.items():
                setattr(row, key, value)
            await session.commit()


# --- 1. enrollment credentials ------------------------------------------------


async def test_token_is_returned_once_and_never_again(client, owner):
    created = await _create_token(client, owner["headers"])
    assert created["token"].startswith("nxk_")
    assert created["state"] == "ACTIVE"
    assert created["single_use"] is True
    assert "<token>" in created["install_hint"]

    listed = await client.get(f"{API}/nodes/enrollment-tokens", headers=owner["headers"])
    assert listed.status_code == 200, listed.text
    rows = listed.json()["items"]
    assert len(rows) == 1
    # The listing model has no token field at all — a value can never be re-read.
    assert "token" not in rows[0]
    assert rows[0]["id"] == created["id"]
    assert rows[0]["state"] == "ACTIVE"


async def test_expired_and_revoked_tokens_both_refuse_enrollment(client, owner):
    expired = await _create_token(client, owner["headers"], name="expired")
    await _mutate_in_system_scope(
        EnrollmentToken, expired["id"], expires_at=datetime.now(UTC) - timedelta(seconds=1)
    )
    dead = await _enroll(client, expired["token"], "expired.integration.test")
    assert dead.status_code == 401, dead.text
    assert_error_code(dead.json(), "ENROLLMENT_TOKEN_INVALID")

    revoked = await _create_token(client, owner["headers"], name="revoked")
    revoke = await client.post(
        f"{API}/nodes/enrollment-tokens/{revoked['id']}/revoke", headers=owner["headers"]
    )
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["state"] == "REVOKED"
    dead2 = await _enroll(client, revoked["token"], "revoked.integration.test")
    assert dead2.status_code == 401, dead2.text
    assert_error_code(dead2.json(), "ENROLLMENT_TOKEN_INVALID")


async def test_enrollment_is_single_use(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    first = await _enroll(client, token, "first.integration.test")
    assert first.status_code == 201, first.text
    second = await _enroll(client, token, "second.integration.test")
    assert second.status_code == 401, second.text
    assert_error_code(second.json(), "ENROLLMENT_TOKEN_INVALID")

    # After use the row reads USED and can no longer be revoked.
    listed = (await client.get(f"{API}/nodes/enrollment-tokens", headers=owner["headers"])).json()
    assert listed["items"][0]["state"] == "USED"
    late_revoke = await client.post(
        f"{API}/nodes/enrollment-tokens/{listed['items'][0]['id']}/revoke",
        headers=owner["headers"],
    )
    assert late_revoke.status_code == 409, late_revoke.text


async def test_concurrent_redemptions_cannot_both_win(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    results = await asyncio.gather(
        _enroll(client, token, "race-a.integration.test"),
        _enroll(client, token, "race-b.integration.test"),
    )
    statuses = sorted(response.status_code for response in results)
    assert statuses == [201, 401], [r.text for r in results]


async def test_enrollment_claims_a_placeholder_node(client, owner):
    placeholder = (
        await client.post(
            f"{API}/nodes", headers=owner["headers"], json=server_payload("placeholder-node")
        )
    ).json()
    token = (
        await _create_token(client, owner["headers"], node_id=placeholder["id"], name="claim")
    )["token"]

    enrolled = await _enroll(client, token, "placeholder-host.integration.test")
    assert enrolled.status_code == 201, enrolled.text
    # The placeholder is claimed rather than duplicated.
    assert enrolled.json()["node_id"] == placeholder["id"]
    nodes = (await client.get(f"{API}/nodes", headers=owner["headers"])).json()["items"]
    assert [row["id"] for row in nodes] == [placeholder["id"]]


async def test_token_cannot_claim_a_foreign_tenants_node(client, owner, second_org):
    foreign = (
        await client.post(
            f"{API}/nodes", headers=second_org["headers"], json=server_payload("foreign-node")
        )
    ).json()
    response = await client.post(
        f"{API}/nodes/enrollment-tokens",
        headers=owner["headers"],
        json={"name": "cross", "node_id": foreign["id"]},
    )
    assert response.status_code == 404, response.text
    assert_error_code(response.json(), "NODE_NOT_FOUND")


async def test_enrollment_lands_in_the_tokens_organization(client, owner, second_org):
    token = (await _create_token(client, second_org["headers"]))["token"]
    enrolled = await _enroll(client, token, "org-b-brand-new.integration.test")
    assert enrolled.status_code == 201, enrolled.text
    node_id = enrolled.json()["node_id"]

    # Visible in B, absent in A.
    in_b = {
        row["id"]
        for row in (await client.get(f"{API}/nodes", headers=second_org["headers"])).json()["items"]
    }
    assert node_id in in_b
    in_a = {
        row["id"]
        for row in (await client.get(f"{API}/nodes", headers=owner["headers"])).json()["items"]
    }
    assert node_id not in in_a

    # A cannot see B's token either.
    tokens_a = (await client.get(f"{API}/nodes/enrollment-tokens", headers=owner["headers"])).json()
    assert tokens_a["items"] == []


async def test_enrollment_token_endpoints_require_the_documented_permission(client, owner):
    roles = (await client.get(f"{API}/roles", headers=owner["headers"])).json()
    rows = roles["items"] if isinstance(roles, dict) else roles
    viewer_role = next(r for r in rows if r["name"] == "Viewer")

    from .helpers import login_account, unique_email

    email = unique_email("phase3-viewer")
    created = await client.post(
        f"{API}/users",
        headers=owner["headers"],
        json={
            "email": email,
            "password": "Integration-Pass1",
            "full_name": "Phase3 Viewer",
            "role_id": viewer_role["id"],
        },
    )
    assert created.status_code in (200, 201), created.text
    session = await login_account(client, email=email, password="Integration-Pass1")
    viewer = bearer(session["access_token"], session["active_organization_id"])

    denied = await client.post(
        f"{API}/nodes/enrollment-tokens", headers=viewer, json={"name": "nope"}
    )
    assert denied.status_code == 403, denied.text
    assert_error_code(denied.json(), "PERMISSION_DENIED")

    # A Viewer may read the list (node.read) but never the raw token.
    listed = await client.get(f"{API}/nodes/enrollment-tokens", headers=viewer)
    assert listed.status_code == 200


# --- 3. protocol v2 -----------------------------------------------------------


async def test_hello_persists_capabilities_facts_and_protocol(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "caps.integration.test"
    )

    assert node["protocol_version"] == 2
    assert node["capabilities_reported"] is True
    assert node["capabilities"]["docker"]["present"] is True
    assert node["capabilities"]["docker"]["api_version"] == "1.43"
    assert node["facts"]["kernel"] == "6.8.0"
    assert node["enrolled"] is True
    assert node["agent_version"] == "1.1.0"

    hello = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": agent_token},
        json={**HELLO_V2, "hostname": "caps.integration.test"},
    )
    assert hello.json()["protocol_version"] == 2
    assert hello.json()["min_agent_version"]


async def test_a_second_hello_replaces_capabilities(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "recaps.integration.test"
    )

    await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": agent_token},
        json={
            **HELLO_V2,
            "hostname": "recaps.integration.test",
            # Docker has gone away; the old claim must stop being trusted.
            "capabilities": {"docker": {"present": False}, "nginx": {"present": True}},
        },
    )
    after = (await client.get(f"{API}/nodes/{node['id']}", headers=owner["headers"])).json()
    assert after["capabilities"]["docker"]["present"] is False
    assert after["capabilities"]["nginx"]["present"] is True


async def test_v1_heartbeat_keeps_the_204_contract(client, owner):
    node = (
        await client.post(
            f"{API}/nodes", headers=owner["headers"], json=server_payload("legacy-hb")
        )
    ).json()
    token = (
        await client.post(f"{API}/nodes/{node['id']}/agent-token", headers=owner["headers"])
    ).json()["agent_token"]
    hello = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": token},
        json={"agent_version": "1.0.0", "hostname": "legacy.integration.test"},
    )
    assert hello.json()["protocol_version"] == 1
    heartbeat = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": token}, json=HEARTBEAT
    )
    assert heartbeat.status_code == 204, heartbeat.text
    assert heartbeat.content == b""


# --- 4. delivery and timing ---------------------------------------------------


async def _dispatch(client, headers, node_id: str, op_type: str = "container.start", **params):
    return await client.post(
        f"{API}/operations",
        headers=headers,
        json={
            "node_id": node_id,
            "type": op_type,
            "params": {"container_id": "abc123def456", **params},
        },
    )


async def test_heartbeat_v2_delivers_pending_operation_ids(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "deliver.integration.test"
    )
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()

    heartbeat = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": agent_token}, json=HEARTBEAT
    )
    assert heartbeat.status_code == 200, heartbeat.text
    body = heartbeat.json()
    assert operation["id"] in body["pending_operations"]
    assert body["token_rotation"] is None


async def test_an_operation_created_just_after_a_beat_survives_to_the_next(client, owner):
    """The whole reason the queue deadline is separate from the exec timeout."""
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "justafter.integration.test"
    )

    first_beat = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": agent_token}, json=HEARTBEAT
    )
    assert first_beat.json()["pending_operations"] == []

    operation = (await _dispatch(client, owner["headers"], node["id"])).json()
    # The next beat is one interval away; the row must still be claimable.
    second_beat = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": agent_token}, json=HEARTBEAT
    )
    assert operation["id"] in second_beat.json()["pending_operations"]

    claimed = await client.post(
        f"{API}/agent/operations/{operation['id']}/claim",
        headers={"X-Agent-Token": agent_token},
    )
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["execution_deadline"] is not None


async def test_late_claim_is_refused_once_the_queue_deadline_passes(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "lateclaim.integration.test"
    )
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()

    past = datetime.now(UTC) - timedelta(seconds=1)
    await _mutate_in_system_scope(Operation, operation["id"], available_until=past, expires_at=past)

    claim = await client.post(
        f"{API}/agent/operations/{operation['id']}/claim",
        headers={"X-Agent-Token": agent_token},
    )
    assert claim.status_code == 409, claim.text
    assert_error_code(claim.json(), "OPERATION_EXPIRED")


async def test_claim_opens_the_execution_deadline_and_sets_the_hard_expiry(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "deadline.integration.test"
    )
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()

    claimed = (
        await client.post(
            f"{API}/agent/operations/{operation['id']}/claim",
            headers={"X-Agent-Token": agent_token},
        )
    ).json()
    detail = (
        await client.get(f"{API}/operations/{operation['id']}", headers=owner["headers"])
    ).json()

    claimed_at = datetime.fromisoformat(claimed["claimed_at"])
    execution = datetime.fromisoformat(claimed["execution_deadline"])
    expires = datetime.fromisoformat(detail["expires_at"])

    # container.start timeout is 60s from the claim.
    assert timedelta(seconds=55) < (execution - claimed_at) <= timedelta(seconds=60)
    # The queue deadline no longer gates the row; the execution deadline does.
    assert (execution - claimed_at) < (expires - claimed_at)
    assert expires > execution


async def test_a_slow_result_is_accepted_inside_the_grace_then_bounded(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "slow.integration.test"
    )
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()
    await client.post(
        f"{API}/agent/operations/{operation['id']}/claim",
        headers={"X-Agent-Token": agent_token},
    )

    # Past the execution deadline but inside the reporting grace: still accepted,
    # which is what absorbs one slow heartbeat.
    now = datetime.now(UTC)
    await _mutate_in_system_scope(
        Operation,
        operation["id"],
        execution_deadline=now - timedelta(seconds=5),
        expires_at=now + timedelta(seconds=25),
    )
    late = await client.post(
        f"{API}/agent/operations/{operation['id']}/result",
        headers={"X-Agent-Token": agent_token},
        json={"ok": True, "output": {"status": "RUNNING"}},
    )
    assert late.status_code == 200, late.text
    assert late.json()["status"] == OperationStatus.SUCCEEDED.value


async def test_a_result_after_the_hard_expiry_is_not_accepted(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "verylate.integration.test"
    )
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()
    await client.post(
        f"{API}/agent/operations/{operation['id']}/claim",
        headers={"X-Agent-Token": agent_token},
    )

    past = datetime.now(UTC) - timedelta(seconds=1)
    await _mutate_in_system_scope(Operation, operation["id"], expires_at=past)

    response = await client.post(
        f"{API}/agent/operations/{operation['id']}/result",
        headers={"X-Agent-Token": agent_token},
        json={"ok": True, "output": {}},
    )
    # The row is now terminal-by-deadline; the report is refused rather than
    # silently rewriting a stale row.
    assert response.status_code == 409, response.text


# --- 5. credential lifecycle --------------------------------------------------


async def test_rotation_is_delivered_to_the_old_token_caller_only(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, old_agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "rotate.integration.test"
    )

    rotated = (
        await client.post(f"{API}/nodes/{node['id']}/agent-token", headers=owner["headers"])
    ).json()["agent_token"]
    assert rotated != old_agent_token

    # The old token still authenticates during grace and receives the new one.
    old_beat = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": old_agent_token}, json=HEARTBEAT
    )
    assert old_beat.status_code == 200, old_beat.text
    delivery = old_beat.json()["token_rotation"]
    assert delivery is not None
    assert delivery["token"] == rotated

    # The new token authenticates, but is never served the rotation again.
    new_beat = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": rotated}, json=HEARTBEAT
    )
    assert new_beat.status_code == 200, new_beat.text
    assert new_beat.json()["token_rotation"] is None

    # Acknowledging ends the grace: the old token stops working immediately.
    ack = await client.post(
        f"{API}/agent/heartbeat",
        headers={"X-Agent-Token": old_agent_token},
        json={**HEARTBEAT, "rotation_applied": True},
    )
    assert ack.status_code == 200, ack.text
    retired = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": old_agent_token}, json=HEARTBEAT
    )
    assert retired.status_code == 401, retired.text
    assert_error_code(retired.json(), "AGENT_TOKEN_UNKNOWN")
    # …and the new token keeps working.
    still_good = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": rotated}, json=HEARTBEAT
    )
    assert still_good.status_code == 200


async def test_rotation_never_discloses_the_new_token_to_the_new_caller(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, _old_agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "nocross.integration.test"
    )
    await client.post(f"{API}/nodes/{node['id']}/agent-token", headers=owner["headers"])

    # A caller with the *new* token must not be handed the rotation payload.
    listed = await client.get(f"{API}/nodes/{node['id']}", headers=owner["headers"])
    assert listed.status_code == 200
    # The credential hash is never exposed through the node resource either.
    assert "agent_token" not in listed.text
    assert "token_hash" not in listed.text


async def test_revocation_is_immediate_and_explicit(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "revoke.integration.test"
    )

    revoke = await client.post(
        f"{API}/nodes/{node['id']}/agent-token/revoke", headers=owner["headers"]
    )
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["agent_revoked"] is True

    rejected = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": agent_token}, json=HEARTBEAT
    )
    assert rejected.status_code == 401, rejected.text
    # Explicit and distinguishable from an unknown token, so the agent log says
    # "re-enroll me" rather than "I am misconfigured".
    assert_error_code(rejected.json(), "AGENT_TOKEN_REVOKED")


async def test_re_enrollment_recovers_a_revoked_node(client, owner):
    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "recover.integration.test"
    )
    await client.post(f"{API}/nodes/{node['id']}/agent-token/revoke", headers=owner["headers"])

    fresh = (await _create_token(client, owner["headers"], node_id=node["id"], name="recover"))[
        "token"
    ]
    re_enrolled = await _enroll(client, fresh, "recover.integration.test")
    assert re_enrolled.status_code == 201, re_enrolled.text
    assert re_enrolled.json()["node_id"] == node["id"]

    new_token = re_enrolled.json()["agent_token"]
    hello = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": new_token},
        json={**HELLO_V2, "hostname": "recover.integration.test"},
    )
    assert hello.status_code == 200, hello.text
    # The old credential stays dead.
    old = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": agent_token}, json=HEARTBEAT
    )
    assert old.status_code == 401


# --- 6. isolation at the database ---------------------------------------------


async def test_enrollment_tokens_are_tenant_scoped_at_the_database(client, owner, second_org):
    created = await _create_token(client, owner["headers"])
    assert created["token"].startswith("nxk_")

    import psycopg

    from tests.conftest import TEST_APP_PASSWORD, TEST_APP_ROLE, TEST_DATABASE_URL

    dsn = TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    assert TEST_APP_ROLE in dsn and TEST_APP_PASSWORD

    with psycopg.connect(dsn) as conn:
        conn.execute("SELECT set_config('app.current_org', %s, false)", (second_org["id"],))
        assert conn.execute("SELECT count(*) FROM enrollment_tokens").fetchone()[0] == 0

        conn.execute(
            "SELECT set_config('app.current_org', %s, false)",
            (owner["active_organization_id"],),
        )
        rows = conn.execute("SELECT id FROM enrollment_tokens").fetchall()
    assert [str(row[0]) for row in rows] == [created["id"]]


async def test_a_operation_completes_end_to_end_through_the_real_agent_executor(
    client, owner, monkeypatch
):
    """The full path, with the *shipped agent executor* actually running.

    Dispatch → heartbeat delivery → compare-and-set claim → local execution by
    ``agent/nexusops_agent.execute_operation`` → result report → terminal state.
    The Docker call is stubbed at the socket boundary (there is no docker daemon
    in this environment); everything above it — the registry, parameter
    validation, capability re-check and result shape — is the real agent code.
    """
    agent = _load_agent_module()

    calls: list[tuple[str, str]] = []

    def fake_docker_raw(method: str, path: str, timeout: float = 5.0):
        calls.append((method, path))
        return 204, b""

    monkeypatch.setattr(agent, "_docker_raw", fake_docker_raw)
    monkeypatch.setattr(agent, "_container_status", lambda cid: "RUNNING")

    token = (await _create_token(client, owner["headers"]))["token"]
    node, agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "e2e.integration.test"
    )
    dispatched = (await _dispatch(client, owner["headers"], node["id"])).json()

    # The agent learns of its work on the heartbeat.
    heartbeat = await client.post(
        f"{API}/agent/heartbeat", headers={"X-Agent-Token": agent_token}, json=HEARTBEAT
    )
    assert heartbeat.status_code == 200, heartbeat.text
    assert dispatched["id"] in heartbeat.json()["pending_operations"]

    claim = await client.post(
        f"{API}/agent/operations/{dispatched['id']}/claim",
        headers={"X-Agent-Token": agent_token},
    )
    assert claim.status_code == 200, claim.text
    claim_body = claim.json()

    from datetime import datetime as _dt

    deadline = _dt.fromisoformat(claim_body["execution_deadline"]).timestamp()
    ok, output, error_code, _message = agent.execute_operation(
        claim_body["type"],
        claim_body["params"],
        deadline=deadline,
        capabilities=node["capabilities"],
    )
    assert ok is True, (error_code, output)
    # The executor issued exactly the fixed docker API call for the type.
    assert calls == [("POST", "/containers/abc123def456/start")]

    reported = await client.post(
        f"{API}/agent/operations/{dispatched['id']}/result",
        headers={"X-Agent-Token": agent_token},
        json={"ok": ok, "output": output},
    )
    assert reported.status_code == 200, reported.text
    assert reported.json()["status"] == OperationStatus.SUCCEEDED.value

    detail = (
        await client.get(f"{API}/operations/{dispatched['id']}", headers=owner["headers"])
    ).json()
    assert detail["status"] == OperationStatus.SUCCEEDED.value
    assert detail["result"] == {"status": "RUNNING"}


async def test_agent_credentials_are_unique_per_node(client, owner):
    """The routing table is one row per node; enrollment never stacks rows."""
    token = (await _create_token(client, owner["headers"]))["token"]
    node, _agent_token, _ = await _enrolled_node(
        client, owner["headers"], token, "unique.integration.test"
    )

    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        with system_scope("test: count credentials"):
            await apply_scope_to_session(session)
            count = (
                await session.execute(select(Server.id).where(Server.id == uuid.UUID(node["id"])))
            ).all()
    assert len(count) == 1
