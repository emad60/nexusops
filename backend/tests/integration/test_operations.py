"""Node operations: the compare-and-set state machine and its tenant boundary.

Three questions, mirroring the isolation suite's structure:

1. **Does the state machine hold?** A claim is a compare-and-set, so exactly one
   claimant wins; a result is only accepted from a claimed/running row; a
   duplicate report against a terminal row is a no-op; the deadline gates every
   transition and the sweep covers pending and claimed rows alike.
2. **Is the boundary enforced?** A foreign operation id is a 404 for an operator
   in another organization, and an agent token can only ever touch its own
   node's rows — the CAS carries both ``node_id`` and ``org_id``, so a token that
   knows a valid foreign id finds nothing rather than being merely refused.
3. **Are the preconditions real?** Dispatch to an unenrolled or OFFLINE node is
   refused, and the permission checked is the one the operation *type* declares
   (``container.lifecycle``), not a generic node grant.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.tenancy import apply_scope_to_session, system_scope
from app.models import Operation, Server
from app.models.enums import OperationStatus
from sqlalchemy import select

from .helpers import (
    API,
    assert_error_code,
    bearer,
    login_account,
    server_payload,
    unique_email,
)

pytestmark = pytest.mark.integration

#: A protocol-2 hello with docker reported present. Dispatch is capability-gated
#: per node since Phase 3, so a node that has not reported capabilities cannot
#: receive an operation — this fixture is what makes the node operable at all.
HELLO = {
    "agent_version": "test-agent/1.1.0",
    "protocol_version": 2,
    "hostname": "ops.integration.test",
    "os_name": "Ubuntu",
    "os_version": "24.04 LTS",
    "arch": "x86_64",
    "cpu_cores": 4,
    "memory_total_mb": 8192,
    "disk_total_gb": 200,
    "capabilities": {"docker": {"present": True, "api_version": "1.43"}},
}

CONTAINER_ID = "abc123def456"


async def _enrolled_node(client, headers, name: str) -> tuple[dict, str]:
    """A node whose agent completed the handshake, plus its token.

    ``agent_enrolled_at`` is only set by the hello handshake (rotating a token
    clears it), and dispatch requires it — so this mirrors what a real node has
    to do before it can be operated on.
    """
    node = (await client.post(f"{API}/nodes", headers=headers, json=server_payload(name))).json()
    token = (await client.post(f"{API}/nodes/{node['id']}/agent-token", headers=headers)).json()[
        "agent_token"
    ]
    hello = await client.post(f"{API}/agent/hello", headers={"X-Agent-Token": token}, json=HELLO)
    assert hello.status_code == 200, hello.text
    return node, token


def _dispatch_body(node_id: str, op_type: str = "container.start", **params) -> dict:
    return {
        "node_id": node_id,
        "type": op_type,
        "params": {"container_id": CONTAINER_ID, **params},
    }


async def _dispatch(client, headers, node_id: str, op_type: str = "container.start", **params):
    return await client.post(
        f"{API}/operations", headers=headers, json=_dispatch_body(node_id, op_type, **params)
    )


async def _mutate_in_system_scope(model, row_id: str, **values) -> None:
    """Reach past the API to stage a state the API would never produce.

    Runs under a system scope because it deliberately touches one specific row
    whose tenant it already knows; this is test scaffolding, not product code.
    """
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        with system_scope("test: stage row state"):
            await apply_scope_to_session(session)
            row = await session.get(model, uuid.UUID(row_id))
            assert row is not None, f"no {model.__name__} {row_id} to stage"
            for key, value in values.items():
                setattr(row, key, value)
            await session.commit()


# --- 1. the state machine ------------------------------------------------------


async def test_dispatch_creates_a_pending_operation_with_a_deadline(client, owner):
    """A dispatch lands as PENDING with the type's timeout written into expiry,
    and its parameters are normalised (defaults included) rather than echoed."""
    node, _token = await _enrolled_node(client, owner["headers"], "ops-create")

    response = await _dispatch(client, owner["headers"], node["id"])
    assert response.status_code == 201, response.text
    body = response.json()

    assert body["status"] == OperationStatus.PENDING.value
    assert body["type"] == "container.start"
    assert body["node_id"] == node["id"]
    assert body["attempts"] == 0
    assert body["claimed_at"] is None
    assert body["result"] is None
    # container.remove only; `force` defaults in so the agent never re-derives it.
    assert body["params"]["force"] is False
    assert body["params"]["container_id"] == CONTAINER_ID

    created = datetime.fromisoformat(body["created_at"])
    expires = datetime.fromisoformat(body["expires_at"])
    available = datetime.fromisoformat(body["available_until"])
    # The pending hard deadline IS the queue deadline, and it is sized to outlast
    # at least three heartbeats (90s) so an operation created just after a beat
    # cannot die before the next one. It is not the 60s execution timeout.
    assert expires == available
    assert timedelta(seconds=115) < (available - created) <= timedelta(seconds=125)
    # The execution clock only starts at claim.
    assert body["execution_deadline"] is None

    # The audit trail names the operation and the node, in the caller's tenant.
    audit = await client.get(
        f"{API}/audit-logs", headers=owner["headers"], params={"action": "operation.create"}
    )
    assert audit.status_code == 200, audit.text
    assert [row["action"] for row in audit.json()["items"]] == ["operation.create"]


async def test_unknown_operation_type_and_bad_params_are_rejected(client, owner):
    """The whitelist is enforced, and params are validated per type."""
    node, _token = await _enrolled_node(client, owner["headers"], "ops-whitelist")

    not_whitelisted = await client.post(
        f"{API}/operations",
        headers=owner["headers"],
        json={"node_id": node["id"], "type": "nginx.reload", "params": {}},
    )
    assert not_whitelisted.status_code == 422, not_whitelisted.text

    # A field the type's model does not declare is refused rather than passed
    # through to the node (`extra="forbid"`).
    extra = await _dispatch(client, owner["headers"], node["id"], command="uptime")
    assert extra.status_code == 422, extra.text

    # And an unbounded tail is refused at the boundary.
    too_many = await _dispatch(client, owner["headers"], node["id"], op_type="logs.tail", tail=9999)
    assert too_many.status_code == 422, too_many.text


async def test_claim_is_compare_and_set_and_the_loser_learns_the_state(client, owner):
    """Exactly one of two concurrent claims wins; the other is told why."""
    node, token = await _enrolled_node(client, owner["headers"], "ops-cas")
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()

    first = await client.post(
        f"{API}/agent/operations/{operation['id']}/claim",
        headers={"X-Agent-Token": token},
    )
    assert first.status_code == 200, first.text
    assert first.json()["type"] == "container.start"
    assert first.json()["params"]["container_id"] == CONTAINER_ID

    # A second claim of the same id must not win.
    second = await client.post(
        f"{API}/agent/operations/{operation['id']}/claim",
        headers={"X-Agent-Token": token},
    )
    assert second.status_code == 409, second.text
    assert_error_code(second.json(), "OPERATION_ALREADY_CLAIMED")

    # The winning claim is the one that incremented attempts.
    detail = await client.get(f"{API}/operations/{operation['id']}", headers=owner["headers"])
    assert detail.json()["status"] == OperationStatus.CLAIMED.value
    assert detail.json()["attempts"] == 1


async def test_result_transitions_and_a_duplicate_is_a_noop(client, owner):
    """A reported outcome sticks; a re-delivery of it changes nothing."""
    node, token = await _enrolled_node(client, owner["headers"], "ops-result")
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()
    await client.post(
        f"{API}/agent/operations/{operation['id']}/claim", headers={"X-Agent-Token": token}
    )

    reported = await client.post(
        f"{API}/agent/operations/{operation['id']}/result",
        headers={"X-Agent-Token": token},
        json={"ok": True, "output": {"status": "RUNNING"}},
    )
    assert reported.status_code == 200, reported.text
    assert reported.json()["status"] == OperationStatus.SUCCEEDED.value

    # The agent retries the same delivery: terminal rows are immutable, so it is
    # a no-op and *not* an error the agent should try to fix.
    duplicate = await client.post(
        f"{API}/agent/operations/{operation['id']}/result",
        headers={"X-Agent-Token": token},
        json={"ok": False, "output": {}, "error_code": "LATE"},
    )
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json()["status"] == OperationStatus.SUCCEEDED.value

    detail = await client.get(f"{API}/operations/{operation['id']}", headers=owner["headers"])
    assert detail.json()["status"] == OperationStatus.SUCCEEDED.value
    assert detail.json()["result"] == {"status": "RUNNING"}
    assert detail.json()["error_code"] is None

    # The agent actor is attributed in the audit trail.
    audit = await client.get(
        f"{API}/audit-logs", headers=owner["headers"], params={"action": "operation.result"}
    )
    assert any(row["actor_email"].startswith("agent:") for row in audit.json()["items"]), audit.text


async def test_result_against_a_never_claimed_operation_is_refused(client, owner):
    """A report for a PENDING row is a protocol violation, not a no-op."""
    node, token = await _enrolled_node(client, owner["headers"], "ops-pending-result")
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()

    response = await client.post(
        f"{API}/agent/operations/{operation['id']}/result",
        headers={"X-Agent-Token": token},
        json={"ok": True, "output": {}},
    )
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "OPERATION_NOT_CLAIMABLE")


async def test_cancel_only_applies_to_a_pending_operation(client, owner):
    """Cancel is a PENDING transition; a claimed op is already out of reach."""
    node, token = await _enrolled_node(client, owner["headers"], "ops-cancel")
    first = (await _dispatch(client, owner["headers"], node["id"])).json()

    cancelled = await client.post(
        f"{API}/operations/{first['id']}/cancel", headers=owner["headers"]
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == OperationStatus.CANCELLED.value

    # Cancelling again, or cancelling a claimed op, is a conflict — and the
    # cancelled row can no longer be claimed by the agent.
    again = await client.post(f"{API}/operations/{first['id']}/cancel", headers=owner["headers"])
    assert again.status_code == 409, again.text

    second = (await _dispatch(client, owner["headers"], node["id"])).json()
    await client.post(
        f"{API}/agent/operations/{second['id']}/claim", headers={"X-Agent-Token": token}
    )
    claimed_cancel = await client.post(
        f"{API}/operations/{second['id']}/cancel", headers=owner["headers"]
    )
    assert claimed_cancel.status_code == 409, claimed_cancel.text
    assert_error_code(claimed_cancel.json(), "OPERATION_NOT_CANCELLABLE")

    claim_cancelled = await client.post(
        f"{API}/agent/operations/{first['id']}/claim", headers={"X-Agent-Token": token}
    )
    assert claim_cancelled.status_code == 409, claim_cancelled.text


# --- 2. the deadline -----------------------------------------------------------


async def test_expiry_gates_claim(client, owner):
    """A past-deadline operation cannot be claimed, whatever its status says."""
    node, token = await _enrolled_node(client, owner["headers"], "ops-expired")
    operation = (await _dispatch(client, owner["headers"], node["id"])).json()

    # The claim gate is the queue deadline (``available_until``); sending it into
    # the past is what makes the operation unclaimable.
    past = datetime.now(UTC) - timedelta(seconds=1)
    await _mutate_in_system_scope(Operation, operation["id"], available_until=past, expires_at=past)

    response = await client.post(
        f"{API}/agent/operations/{operation['id']}/claim", headers={"X-Agent-Token": token}
    )
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "OPERATION_EXPIRED")

    # The row is untouched — the failed claim did not bump attempts.
    detail = await client.get(f"{API}/operations/{operation['id']}", headers=owner["headers"])
    assert detail.json()["status"] == OperationStatus.PENDING.value
    assert detail.json()["attempts"] == 0


async def test_expiry_sweep_covers_pending_and_claimed_alike(client, owner, second_org):
    """The sweeper expires both, across tenants, and audits each transition.

    A claimed op whose agent died mid-execution must not stay live forever; the
    architecture's decision is to expire it rather than re-queue a possibly
    already-executed action.
    """
    node_a, token_a = await _enrolled_node(client, owner["headers"], "ops-sweep-a")
    node_b, _token_b = await _enrolled_node(client, second_org["headers"], "ops-sweep-b")

    pending = (await _dispatch(client, owner["headers"], node_a["id"])).json()
    claimed = (await _dispatch(client, owner["headers"], node_a["id"])).json()
    await client.post(
        f"{API}/agent/operations/{claimed['id']}/claim", headers={"X-Agent-Token": token_a}
    )
    # A second tenant's op, to prove the sweep is not single-tenant.
    other_tenant = (await _dispatch(client, second_org["headers"], node_b["id"])).json()

    past = datetime.now(UTC) - timedelta(seconds=5)
    for operation_id in (pending["id"], claimed["id"], other_tenant["id"]):
        await _mutate_in_system_scope(Operation, operation_id, expires_at=past)

    # The task calls asyncio.run() internally, so it is driven from a worker
    # thread exactly like beat does.
    from app.core.db import dispose_engine
    from app.tasks.maintenance import expire_operations

    result = await asyncio.to_thread(expire_operations)
    assert result["expired"] >= 3

    await dispose_engine()  # pooled connections are bound to the task's loop
    for headers, operation_id in (
        (owner["headers"], pending["id"]),
        (owner["headers"], claimed["id"]),
        (second_org["headers"], other_tenant["id"]),
    ):
        detail = await client.get(f"{API}/operations/{operation_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        assert detail.json()["status"] == OperationStatus.EXPIRED.value

    # Each expiry is audited, in the organization that owned the row.
    for headers in (owner["headers"], second_org["headers"]):
        audit = await client.get(
            f"{API}/audit-logs", headers=headers, params={"action": "operation.expire"}
        )
        assert [row["action"] for row in audit.json()["items"]], audit.text


# --- 3. the tenant boundary ----------------------------------------------------


async def test_org_b_cannot_see_or_cancel_org_a_operations(client, owner, second_org):
    """A foreign operation id is a 404, indistinguishable from a random one."""
    node_a, _token = await _enrolled_node(client, owner["headers"], "ops-idor-a")
    operation = (await _dispatch(client, owner["headers"], node_a["id"])).json()
    b = second_org["headers"]

    for real, bogus in (
        (
            await client.get(f"{API}/operations/{operation['id']}", headers=b),
            await client.get(f"{API}/operations/{uuid.uuid4()}", headers=b),
        ),
        (
            await client.post(f"{API}/operations/{operation['id']}/cancel", headers=b),
            await client.post(f"{API}/operations/{uuid.uuid4()}/cancel", headers=b),
        ),
    ):
        assert real.status_code == bogus.status_code == 404, real.text
        assert (
            assert_error_code(real.json(), "OPERATION_NOT_FOUND")["code"]
            == assert_error_code(bogus.json(), "OPERATION_NOT_FOUND")["code"]
        )

    # B's list is its own, and A's row survives untouched.
    listed_b = (await client.get(f"{API}/operations", headers=b)).json()["items"]
    assert operation["id"] not in {row["id"] for row in listed_b}

    listed_a = (await client.get(f"{API}/operations", headers=owner["headers"])).json()["items"]
    assert {row["id"] for row in listed_a} == {operation["id"]}
    assert listed_a[0]["status"] == OperationStatus.PENDING.value


async def test_agent_token_can_only_claim_its_own_nodes_operation(client, owner, second_org):
    """A valid token presented with a real foreign operation id gets a 404.

    The id belongs to a node in another organization; to this token it simply
    does not exist, which is what keeps the response from being an oracle.
    """
    node_a, _token_a = await _enrolled_node(client, owner["headers"], "ops-token-a")
    _node_b, token_b = await _enrolled_node(client, second_org["headers"], "ops-token-b")

    foreign = (await _dispatch(client, owner["headers"], node_a["id"])).json()

    response = await client.post(
        f"{API}/agent/operations/{foreign['id']}/claim", headers={"X-Agent-Token": token_b}
    )
    assert response.status_code == 404, response.text
    assert_error_code(response.json(), "OPERATION_NOT_FOUND")

    # …and the same token cannot report a result for it either.
    result = await client.post(
        f"{API}/agent/operations/{foreign['id']}/result",
        headers={"X-Agent-Token": token_b},
        json={"ok": True, "output": {}},
    )
    assert result.status_code == 404, result.text

    # The row is still pending and still claimable by its real node.
    detail = await client.get(f"{API}/operations/{foreign['id']}", headers=owner["headers"])
    assert detail.json()["status"] == OperationStatus.PENDING.value


async def test_agent_token_from_another_node_in_the_same_org_is_refused(client, owner):
    """Even inside one tenant, one node cannot claim another node's work."""
    node_a, _token_a = await _enrolled_node(client, owner["headers"], "ops-same-org-a")
    _node_b, token_b = await _enrolled_node(client, owner["headers"], "ops-same-org-b")

    operation = (await _dispatch(client, owner["headers"], node_a["id"])).json()

    response = await client.post(
        f"{API}/agent/operations/{operation['id']}/claim", headers={"X-Agent-Token": token_b}
    )
    assert response.status_code == 404, response.text
    assert_error_code(response.json(), "OPERATION_NOT_FOUND")


# --- 4. dispatch preconditions -------------------------------------------------


async def test_dispatch_refuses_unenrolled_and_offline_nodes(client, owner):
    """A node that cannot answer is not given work."""
    node = (
        await client.post(
            f"{API}/nodes", headers=owner["headers"], json=server_payload("ops-unenrolled")
        )
    ).json()

    unenrolled = await _dispatch(client, owner["headers"], node["id"])
    assert unenrolled.status_code == 400, unenrolled.text
    assert_error_code(unenrolled.json(), "NODE_NOT_ENROLLED")

    enrolled, _token = await _enrolled_node(client, owner["headers"], "ops-offline")
    await _mutate_in_system_scope(Server, enrolled["id"], status="OFFLINE")

    offline = await _dispatch(client, owner["headers"], enrolled["id"])
    assert offline.status_code == 409, offline.text
    assert_error_code(offline.json(), "NODE_OFFLINE")


async def test_dispatch_requires_the_permission_of_the_operation_type(client, owner):
    """Authorisation is per type — a Viewer cannot start containers.

    The codename comes from the registry entry, not from a generic node grant,
    which is why the route cannot express it as a static dependency.
    """
    node, _token = await _enrolled_node(client, owner["headers"], "ops-perm")

    roles = (await client.get(f"{API}/roles", headers=owner["headers"])).json()
    rows = roles["items"] if isinstance(roles, dict) else roles
    viewer_role = next(r for r in rows if r["name"] == "Viewer")

    email = unique_email("ops-viewer")
    created = await client.post(
        f"{API}/users",
        headers=owner["headers"],
        json={
            "email": email,
            "password": "Integration-Pass1",
            "full_name": "Ops Viewer",
            "role_id": viewer_role["id"],
        },
    )
    assert created.status_code in (200, 201), created.text

    session = await login_account(client, email=email, password="Integration-Pass1")
    viewer_headers = bearer(session["access_token"], session["active_organization_id"])

    # The Viewer can read operations (node.read)…
    listed = await client.get(f"{API}/operations", headers=viewer_headers)
    assert listed.status_code == 200, listed.text

    # …but cannot dispatch one that needs container.lifecycle.
    denied = await _dispatch(client, viewer_headers, node["id"])
    assert denied.status_code == 403, denied.text
    assert_error_code(denied.json(), "PERMISSION_DENIED")


async def test_operations_are_filterable_by_node_and_status(client, owner):
    """The listing is a scoped read with the filters the dashboard needs."""
    node_a, _token = await _enrolled_node(client, owner["headers"], "ops-filter-a")
    node_b, _token_b = await _enrolled_node(client, owner["headers"], "ops-filter-b")

    first = (await _dispatch(client, owner["headers"], node_a["id"])).json()
    await _dispatch(client, owner["headers"], node_b["id"])

    by_node = await client.get(
        f"{API}/operations", headers=owner["headers"], params={"node_id": node_a["id"]}
    )
    assert [row["id"] for row in by_node.json()["items"]] == [first["id"]]

    # Cancelled only, so the filter is doing the work rather than the tenant.
    await client.post(f"{API}/operations/{first['id']}/cancel", headers=owner["headers"])
    cancelled = await client.get(
        f"{API}/operations", headers=owner["headers"], params={"status": "CANCELLED"}
    )
    assert {row["id"] for row in cancelled.json()["items"]} == {first["id"]}

    # An invalid status is a validation error, not a silent empty list.
    invalid = await client.get(
        f"{API}/operations", headers=owner["headers"], params={"status": "NOPE"}
    )
    assert invalid.status_code == 422


async def test_operations_table_is_tenant_scoped_at_the_database(client, owner, second_org):
    """RLS alone hides a foreign row: a raw probe as the app role sees nothing.

    This is the backstop behind the ORM guard and the scoped helpers — the one
    that catches bulk DML, identity-map hits and raw SQL.
    """
    import psycopg

    from tests.conftest import TEST_APP_PASSWORD, TEST_APP_ROLE, TEST_DATABASE_URL

    node_a, _token = await _enrolled_node(client, owner["headers"], "ops-rls-a")
    operation = (await _dispatch(client, owner["headers"], node_a["id"])).json()

    dsn = TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    assert TEST_APP_ROLE in dsn and TEST_APP_PASSWORD

    with psycopg.connect(dsn) as conn:
        # Scoped to B, A's operation is invisible…
        conn.execute("SELECT set_config('app.current_org', %s, false)", (second_org["id"],))
        visible = conn.execute("SELECT count(*) FROM operations").fetchone()[0]
        assert visible == 0

        # …and B cannot insert a row into A's tenant: WITH CHECK refuses it.
        with pytest.raises(psycopg.errors.Error):
            conn.execute(
                "INSERT INTO operations "
                "(id, org_id, node_id, type, status, params, available_until, expires_at) "
                "VALUES (gen_random_uuid(), %s, %s, 'container.start', 'PENDING', "
                "'{}'::jsonb, now() + interval '1 hour', now() + interval '1 hour')",
                (owner["active_organization_id"], node_a["id"]),
            )
        conn.rollback()

        # In A's own scope the row is there.
        conn.execute(
            "SELECT set_config('app.current_org', %s, false)", (owner["active_organization_id"],)
        )
        mine = conn.execute("SELECT id FROM operations").fetchall()
    assert [str(row[0]) for row in mine] == [operation["id"]]


# --- 4. the exec whitelist cannot be widened by accident ----------------------

#: Reserved by the architecture documents for a later phase (certificates,
#: secret delivery, nginx reload). None is dispatchable: each needs the subsystem
#: it belongs to, and a name alone would be a pass-through. Phase 4's
#: ``nginx.apply`` left this list by shipping — the test below is its replacement.
RESERVED = (
    "certificate.issue",
    "certificate.install",
    "certificate.renew",
    "nginx.reload",
    "secret.env.apply",
)


async def test_no_reserved_later_phase_type_is_dispatchable(client, owner):
    """A reserved type is a 422 at dispatch, not a pass-through to the agent."""
    node, _token = await _enrolled_node(client, owner["headers"], "ops-reserved")
    for reserved in RESERVED:
        response = await _dispatch(client, owner["headers"], node["id"], op_type=reserved)
        assert response.status_code == 422, f"{reserved} was accepted: {response.text}"


async def test_a_shipped_phase4_type_is_gated_on_the_node_capability(client, owner):
    """``nginx.apply`` is a real type now: a node without nginx is told so.

    Not a 422 — the request is valid and the refusal is about *this* node, which
    is the difference between "nobody may ever run this" and "this node cannot".
    """
    node, _token = await _enrolled_node(client, owner["headers"], "ops-nginx-gate")
    response = await client.post(
        f"{API}/operations",
        headers=owner["headers"],
        json={"node_id": node["id"], "type": "nginx.apply", "params": {}},
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "NODE_CAPABILITY_MISSING"


async def test_the_database_whitelist_rejects_an_unregistered_type(client, owner):
    """The DB CHECK is a second fence under the app enum, not decoration."""
    import psycopg

    from tests.conftest import TEST_APP_PASSWORD, TEST_APP_ROLE, TEST_DATABASE_URL

    node, _token = await _enrolled_node(client, owner["headers"], "ops-dbwhitelist")
    dsn = TEST_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    assert TEST_APP_ROLE in dsn and TEST_APP_PASSWORD

    with psycopg.connect(dsn) as conn:
        conn.execute(
            "SELECT set_config('app.current_org', %s, false)", (owner["active_organization_id"],)
        )
        with pytest.raises(psycopg.errors.Error) as exc:
            conn.execute(
                "INSERT INTO operations "
                "(id, org_id, node_id, type, status, params, available_until, expires_at) "
                "VALUES (gen_random_uuid(), %s, %s, 'nginx.reload', 'PENDING', "
                "'{}'::jsonb, now() + interval '1 hour', now() + interval '1 hour')",
                (owner["active_organization_id"], node["id"]),
            )
        assert "ck_operations_type_valid" in str(exc.value)
        conn.rollback()


async def test_dispatch_is_refused_for_a_node_that_never_reported_capabilities(client, owner):
    """Absence of capability data is never read as "has the capability".

    A protocol-1 agent (or a node that has not completed a v2 hello) has an empty
    capability map; dispatch must refuse rather than assume.
    """
    node = (
        await client.post(
            f"{API}/nodes", headers=owner["headers"], json=server_payload("ops-v1-caps")
        )
    ).json()
    token = (
        await client.post(f"{API}/nodes/{node['id']}/agent-token", headers=owner["headers"])
    ).json()["agent_token"]
    # Protocol-1 hello: no capabilities block.
    legacy_hello = {
        "agent_version": "1.0.0",
        "hostname": "ops.integration.test",
        "os_name": "Ubuntu",
        "arch": "x86_64",
    }
    hello = await client.post(
        f"{API}/agent/hello", headers={"X-Agent-Token": token}, json=legacy_hello
    )
    assert hello.status_code == 200, hello.text
    assert hello.json()["protocol_version"] == 1

    response = await _dispatch(client, owner["headers"], node["id"])
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "NODE_CAPABILITY_UNVERIFIED")


async def test_dispatch_is_refused_when_a_node_reports_the_capability_absent(client, owner):
    """A reported-absent capability is a distinct, harder refusal."""
    node = (
        await client.post(
            f"{API}/nodes", headers=owner["headers"], json=server_payload("ops-no-docker")
        )
    ).json()
    token = (
        await client.post(f"{API}/nodes/{node['id']}/agent-token", headers=owner["headers"])
    ).json()["agent_token"]
    hello = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": token},
        json={**HELLO, "capabilities": {"docker": {"present": False}}},
    )
    assert hello.status_code == 200, hello.text

    response = await _dispatch(client, owner["headers"], node["id"])
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "NODE_CAPABILITY_MISSING")


async def test_dispatch_refuses_a_type_whose_capability_cannot_be_verified(
    client, owner, monkeypatch: pytest.MonkeyPatch
):
    """A spec naming a capability outside the vocabulary is refused.

    Current types need ``docker``, which the node reports. A type needing
    anything the platform does not know how to gate on is refused with 409 rather
    than dispatched on the assumption that a node has it.
    """
    from dataclasses import replace

    from app.models.enums import OperationType
    from app.schemas.operation import OPERATION_SPECS as registry

    node, _token = await _enrolled_node(client, owner["headers"], "ops-capability")
    spec = registry[OperationType.CONTAINER_START]
    monkeypatch.setitem(registry, OperationType.CONTAINER_START, replace(spec, capability="tls"))

    response = await _dispatch(client, owner["headers"], node["id"])
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "NODE_CAPABILITY_UNVERIFIED")


async def test_unscoped_orm_access_to_operations_fails_loudly(client, owner):
    """Without a tenant scope the guard refuses rather than returning nothing."""
    from app.core.db import get_sessionmaker
    from app.core.tenancy import apply_scope_to_session, system_scope

    node, _token = await _enrolled_node(client, owner["headers"], "ops-guard")
    await _dispatch(client, owner["headers"], node["id"])

    # Under a system scope the read succeeds (that is the documented carve-out)…
    async with get_sessionmaker()() as session:
        with system_scope("test: unscoped probe"):
            await apply_scope_to_session(session)
            assert (await session.execute(select(Operation))).scalars().all()

    # …but with no scope at all it raises, which is the whole point: a missing
    # filter must be a bug report, not a silent cross-tenant read.
    from app.core.tenancy import TenancyScopeError

    async with get_sessionmaker()() as session:
        with pytest.raises(TenancyScopeError):
            await session.execute(select(Operation))
