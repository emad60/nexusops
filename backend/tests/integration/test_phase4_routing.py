"""Phase 4 through the real HTTP surface, workers and agent contract.

The journey these tests walk is the product journey: enroll a node that reports a
passing nginx pre-flight, report a container with a published port, add a domain,
prove it with (mocked) authoritative DNS, create and enable a route, let the agent
claim the ``nginx.apply`` operation and report the outcome — then assert the
route's state, the node's bounded proxy state, the audit trail and the events.

Two things are mocked, both outside the control plane's own logic:

* the authoritative DNS answers — there is no public domain in CI — through
  ``monkeypatch`` on ``dns_verifier.observe``;
* the node itself, replaced by the same agent HTTP calls a real agent makes.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.tenancy import apply_scope_to_session, system_scope
from app.models import AuditLog, Domain, Monitor, Server, SystemEvent
from app.models.enums import DomainStatus, MonitorTargetType, ServerStatus
from app.services import dns_verifier
from app.services.dns_verifier import STATUS_NO_TXT, STATUS_OK, STATUS_TIMEOUT, TxtObservation
from sqlalchemy import select

from .helpers import API, assert_error_code, bearer, unique_email

pytestmark = pytest.mark.integration

PROXY_CAPABILITY = {
    "present": True,
    "version": "1.27.5",
    "running": True,
    "config_test_ok": True,
    "listener_80": "MANAGED",
    "listener_443": "FREE",
    "routing_eligible": True,
    "reason": "",
}

HELLO = {
    "agent_version": "1.2.0",
    "protocol_version": 2,
    "hostname": "phase4.integration.test",
    "os_name": "Ubuntu",
    "os_version": "24.04 LTS",
    "arch": "x86_64",
    "cpu_cores": 4,
    "memory_total_mb": 8192,
    "disk_total_gb": 200,
    "capabilities": {"docker": {"present": True}, "nginx": PROXY_CAPABILITY},
    "facts": {},
}

CONTAINER_ID = "f" * 64
NS_SET = ("ns1.example.net", "ns2.example.net")

#: The token the mocked authoritative DNS currently serves. Kept in a dict so the
#: fake observer can read whatever the test just created.
DNS: dict[str, object] = {"token": "", "nameservers": NS_SET}


def _fake_observe(name: str) -> TxtObservation:
    return TxtObservation(
        STATUS_OK,
        values=(str(DNS["token"]),),
        nameservers=tuple(DNS["nameservers"]),  # type: ignore[arg-type]
    )


def heartbeat_payload(*, status: str = "RUNNING", ports: list[dict] | None = None) -> dict:
    return {
        "cpu_percent": 5.0,
        "mem_used_mb": 512.0,
        "mem_percent": 20.0,
        "disk_used_gb": 40.0,
        "disk_percent": 50.0,
        "containers": [
            {
                "container_id": CONTAINER_ID,
                "name": "phase4-app",
                "status": status,
                "health": None,
                "image_ref": "app:latest",
                "restart_count": 0,
                "ports": ports
                if ports is not None
                else [
                    {"container_port": 8000, "host_port": 8081, "host_ip": "127.0.0.1"},
                    # Published wildcard addresses in canned port data.
                    {
                        "container_port": 9000,
                        "host_port": 9001,
                        "host_ip": "0.0.0.0",  # noqa: S104 - canned port data
                    },
                    {
                        "container_port": 443,
                        "host_port": 443,
                        "host_ip": "0.0.0.0",  # noqa: S104 - canned port data
                    },
                ],
            }
        ],
    }


# --- fixtures -----------------------------------------------------------------


@pytest.fixture(autouse=True)
def _dns_stub(monkeypatch: pytest.MonkeyPatch):
    """Stand in for authoritative DNS in every test in this module."""
    DNS["token"] = ""
    DNS["nameservers"] = NS_SET
    monkeypatch.setattr(dns_verifier, "observe", _fake_observe)
    yield


# --- helpers ------------------------------------------------------------------


async def _create_node(
    client, owner, *, hostname: str = "phase4.integration.test"
) -> tuple[dict, str]:
    created = await client.post(
        f"{API}/nodes/enrollment-tokens",
        headers=owner["headers"],
        json={"name": f"tok-{uuid.uuid4().hex[:6]}", "expires_in_seconds": 3600},
    )
    assert created.status_code == 201, created.text
    enrolled = await client.post(
        f"{API}/agent/enroll",
        json={
            "enrollment_token": created.json()["token"],
            "hostname": hostname,
            "agent_version": "1.2.0",
        },
    )
    assert enrolled.status_code == 201, enrolled.text
    node_id = enrolled.json()["node_id"]
    agent_token = enrolled.json()["agent_token"]
    hello = await client.post(
        f"{API}/agent/hello",
        headers={"X-Agent-Token": agent_token},
        json={**HELLO, "hostname": hostname},
    )
    assert hello.status_code == 200, hello.text
    node = (await client.get(f"{API}/nodes/{node_id}", headers=owner["headers"])).json()
    return node, agent_token


async def _heartbeat(client, agent_token: str, **kwargs) -> dict:
    response = await client.post(
        f"{API}/agent/heartbeat",
        headers={"X-Agent-Token": agent_token},
        json=heartbeat_payload(**kwargs),
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _container_id(client, owner, node_id: str) -> str:
    listed = await client.get(
        f"{API}/containers", headers=owner["headers"], params={"server_id": node_id}
    )
    assert listed.status_code == 200, listed.text
    items = listed.json()["items"]
    assert items, "the heartbeat should have created the container row"
    return items[0]["id"]


async def _proxy_ready_node(
    client, owner, *, hostname: str = "phase4.integration.test"
) -> tuple[dict, str, str]:
    node, agent_token = await _create_node(client, owner, hostname=hostname)
    await _heartbeat(client, agent_token)
    return node, agent_token, await _container_id(client, owner, node["id"])


async def _claim(client, agent_token: str, operation_id: str) -> dict:
    response = await client.post(
        f"{API}/agent/operations/{operation_id}/claim",
        headers={"X-Agent-Token": agent_token},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _report(client, agent_token: str, operation_id: str, body: dict) -> dict:
    response = await client.post(
        f"{API}/agent/operations/{operation_id}/result",
        headers={"X-Agent-Token": agent_token},
        json=body,
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _drain(
    client, agent_token: str, *, outcome: str = "applied"
) -> list[tuple[str, dict, dict]]:
    """Claim and answer every pending operation, exactly like the agent would.

    ``bootstrap`` and ``status`` always succeed; ``nginx.apply`` reports *outcome*
    (``applied`` / ``failed`` / ``rolled_back`` / ``rollback_failed``) using the
    bundle the control plane actually sent, so attribution is exercised for real.
    """
    handled: list[tuple[str, dict, dict]] = []
    for _ in range(6):
        beat = await _heartbeat(client, agent_token)
        pending = beat.get("pending_operations") or []
        if not pending:
            break
        for operation_id in pending:
            try:
                claimed = await _claim(client, agent_token, operation_id)
            except AssertionError:
                continue  # lost the CAS or expired: not an error
            op_type = claimed["type"]
            bundle = (claimed.get("params") or {}).get("bundle") or {}
            if op_type == "nginx.apply":
                ok = outcome == "applied"
                output = {
                    "outcome": outcome,
                    "bundle_id": bundle.get("bundle_id"),
                    "live_bundle_id": bundle.get("bundle_id") if ok else None,
                    "manifest": bundle.get("manifest", []),
                    "config_test_ok": True,
                    "nginx_version": "1.27.5",
                }
                if not ok:
                    output["error"] = "nginx: [emerg] invalid directive"
                body = {"ok": ok, "output": output}
                if not ok:
                    body["error_code"] = "NGINX_CONFIG_INVALID"
                    body["error_message"] = "nginx: [emerg] invalid directive"
            elif op_type == "nginx.status":
                body = {
                    "ok": True,
                    "output": {
                        "live_bundle_id": bundle.get("bundle_id") or None,
                        "nginx_version": "1.27.5",
                        "config_test_ok": True,
                    },
                }
            else:
                body = {"ok": True, "output": {"bootstrapped": True}}
            reported = await _report(client, agent_token, operation_id, body)
            handled.append((op_type, claimed, reported))
    return handled


async def _create_domain(client, owner, name: str, **extra) -> dict:
    response = await client.post(
        f"{API}/domains", headers=owner["headers"], json={"name": name, **extra}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    DNS["token"] = body["verification"]["record_value"]
    return body


async def _run_verify(client, owner, domain_id: str, *, trigger: str = "user") -> dict:
    from app.tasks.domain_routing import _verify

    return await _verify(uuid.UUID(domain_id), trigger=trigger)


async def _verified_domain(client, owner, name: str = "phase4.example.com") -> dict:
    created = await _create_domain(client, owner, name)
    outcome = await _run_verify(client, owner, created["id"])
    assert outcome["status"] == DomainStatus.VERIFIED.value, outcome
    return (await client.get(f"{API}/domains/{created['id']}", headers=owner["headers"])).json()


async def _create_route(client, owner, *, domain, node_id, container_id, **overrides) -> dict:
    payload = {
        "domain_id": domain["id"],
        "hostname": domain["name"],
        "node_id": node_id,
        "container_id": container_id,
        "port": 8081,
        **overrides,
    }
    response = await client.post(f"{API}/routes", headers=owner["headers"], json=payload)
    return response


async def _node_proxy_state(node_id: str) -> dict:
    """One node's bounded ``proxy_state``, read the way the worker sees it."""
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        with system_scope("test: read node proxy state"):
            await apply_scope_to_session(session)
            row = await session.get(Server, uuid.UUID(node_id))
            assert row is not None
            return dict(row.proxy_state or {})


async def _live_operations(
    client, owner, node_id: str, *, op_type: str | None = None
) -> list[dict]:
    """Operations on *node_id* still waiting to be executed, optionally by type."""
    listed = (
        await client.get(f"{API}/operations", headers=owner["headers"], params={"node_id": node_id})
    ).json()["items"]
    return [
        op
        for op in listed
        if op["status"] in ("PENDING", "CLAIMED", "RUNNING")
        and (op_type is None or op["type"] == op_type)
    ]


async def _mutate_in_system_scope(model, row_id: str, **values) -> None:
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        with system_scope("test: stage phase4 row"):
            await apply_scope_to_session(session)
            row = await session.get(model, uuid.UUID(row_id))
            assert row is not None
            for key, value in values.items():
                setattr(row, key, value)
            await session.commit()


async def _count_rows_in_system_scope(model, **filters) -> int:
    from app.core.db import get_sessionmaker
    from sqlalchemy import func

    async with get_sessionmaker()() as session:
        with system_scope("test: count rows"):
            await apply_scope_to_session(session)
            stmt = select(func.count()).select_from(model)
            for key, value in filters.items():
                stmt = stmt.where(getattr(model, key) == value)
            return int(await session.scalar(stmt) or 0)


async def _role_id(client, owner, name: str) -> str:
    listed = await client.get(f"{API}/roles", headers=owner["headers"])
    assert listed.status_code == 200, listed.text
    for role in listed.json()["items"]:
        if role["name"] == name:
            return role["id"]
    raise AssertionError(f"role {name} not found")


# --- 1. the node-side pre-flight ------------------------------------------------


async def test_a_reporting_node_queues_bootstrap_once(client, owner):
    """The capability appearing is what triggers the idempotent bootstrap."""
    _node, agent_token = await _create_node(client, owner)
    beat = await _heartbeat(client, agent_token)
    for operation_id in beat["pending_operations"]:
        claimed = await _claim(client, agent_token, operation_id)
        assert claimed["type"] == "nginx.bootstrap"
        assert claimed["params"] == {}
        await _report(
            client, agent_token, operation_id, {"ok": True, "output": {"bootstrapped": True}}
        )
    # A second hello does not re-queue it.
    hello = await client.post(
        f"{API}/agent/hello", headers={"X-Agent-Token": agent_token}, json=HELLO
    )
    assert hello.status_code == 200, hello.text
    beat = await _heartbeat(client, agent_token)
    assert beat["pending_operations"] == []


async def test_proxy_status_reports_the_preflight(client, owner):
    node, agent_token = await _create_node(client, owner)
    await _heartbeat(client, agent_token)
    status = await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["provider"] == "nginx"
    assert body["capability"]["present"] is True
    assert body["capability"]["routing_eligible"] is True
    assert body["capability"]["listener_80"] == "MANAGED"
    assert body["eligible"] is True
    assert body["ineligible_reason"] == ""


async def test_route_creation_is_refused_when_the_preflight_fails(client, owner):
    node, agent_token = await _create_node(client, owner)
    await _mutate_in_system_scope(
        Server,
        node["id"],
        capabilities={
            "docker": {"present": True},
            "nginx": {
                **PROXY_CAPABILITY,
                "running": False,
                "routing_eligible": False,
                "reason": "the nginx service is not running",
            },
        },
    )
    await _heartbeat(client, agent_token)
    container_id = await _container_id(client, owner, node["id"])
    domain = await _verified_domain(client, owner, "notrunning.example.com")

    response = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.notrunning.example.com",
    )
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "NGINX_PREFLIGHT_FAILED")


async def test_a_listener_conflict_is_named_precisely(client, owner):
    node, agent_token = await _create_node(client, owner)
    await _mutate_in_system_scope(
        Server,
        node["id"],
        capabilities={
            "docker": {"present": True},
            "nginx": {
                **PROXY_CAPABILITY,
                "listener_80": "OTHER",
                "routing_eligible": False,
                "reason": "port 80 is held by a process that is not the intended nginx instance",
            },
        },
    )
    await _heartbeat(client, agent_token)
    status = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert status["eligible"] is False
    assert "80" in status["ineligible_reason"]
    assert status["capability"]["listener_80"] == "OTHER"


async def test_stale_capabilities_block_routing(client, owner):
    node, agent_token = await _create_node(client, owner)
    await _heartbeat(client, agent_token)
    await _mutate_in_system_scope(
        Server,
        node["id"],
        last_heartbeat_at=datetime.now(UTC) - timedelta(minutes=30),
    )
    response = await client.post(f"{API}/nodes/{node['id']}/proxy/apply", headers=owner["headers"])
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "NODE_CAPABILITY_STALE")


async def test_capability_that_goes_stale_between_creation_and_enable_blocks_the_route(
    client, owner
):
    """The safety check runs again at enable time, not only at creation."""
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "staleenable.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id
    )
    assert created.status_code == 201, created.text

    await _mutate_in_system_scope(
        Server,
        node["id"],
        capabilities={
            "docker": {"present": True},
            "nginx": {
                **PROXY_CAPABILITY,
                "listener_80": "OTHER",
                "routing_eligible": False,
                "reason": "port 80 is held by another process",
            },
        },
    )
    enabled = await client.post(
        f"{API}/routes/{created.json()['id']}/enable", headers=owner["headers"]
    )
    assert enabled.status_code == 409, enabled.text
    assert_error_code(enabled.json(), "NGINX_PREFLIGHT_FAILED")


async def test_upstream_picker_lists_only_usable_ports(client, owner):
    node, _agent_token, _container = await _proxy_ready_node(client, owner)
    response = await client.get(f"{API}/nodes/{node['id']}/route-targets", headers=owner["headers"])
    assert response.status_code == 200, response.text
    targets = response.json()
    assert len(targets) == 1
    ports = {port["host_port"]: port for port in targets[0]["upstream_ports"]}
    # The loopback publish is preferred; the wildcard bind maps to loopback; the
    # container's own :443 publish is excluded because the proxy owns that port.
    assert ports[8081]["upstream_host"] == "127.0.0.1"
    assert ports[9001]["upstream_host"] == "127.0.0.1"
    assert 443 not in ports
    # The container-internal port is reported but never offered as the upstream.
    assert ports[8081]["container_port"] == 8000


async def test_a_container_without_published_ports_offers_nothing(client, owner):
    node, agent_token = await _create_node(client, owner)
    await _heartbeat(client, agent_token, ports=[])
    container_id = await _container_id(client, owner, node["id"])
    targets = (
        await client.get(f"{API}/nodes/{node['id']}/route-targets", headers=owner["headers"])
    ).json()
    assert targets[0]["upstream_ports"] == []
    assert targets[0]["unavailable_reason"]

    domain = await _verified_domain(client, owner, "noports.example.com")
    response = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, port=8081
    )
    assert response.status_code == 422, response.text
    assert_error_code(response.json(), "PORT_NOT_PUBLISHED")


async def test_proxy_endpoints_respect_the_routing_permissions(client, owner):
    node, _agent_token = await _create_node(client, owner)
    created = await client.post(
        f"{API}/users",
        headers=owner["headers"],
        json={
            "email": unique_email("viewer"),
            "password": "Viewer-Pass1!",
            "full_name": "Viewer",
            "role_id": await _role_id(client, owner, "Viewer"),
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["initial_password"] is None  # a password was supplied
    login = await client.post(
        f"{API}/auth/login",
        json={"email": created.json()["user"]["email"], "password": "Viewer-Pass1!"},
    )
    assert login.status_code == 200, login.text
    headers = bearer(login.json()["access_token"], owner["active_organization_id"])
    assert (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=headers)
    ).status_code == 200
    denied = await client.post(f"{API}/nodes/{node['id']}/proxy/apply", headers=headers)
    assert denied.status_code == 403, denied.text


# --- 2. domains -----------------------------------------------------------------


async def test_domain_creation_returns_exact_txt_instructions(client, owner):
    response = await client.post(
        f"{API}/domains", headers=owner["headers"], json={"name": "Example.COM"}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "example.com"  # canonicalised on write
    assert body["status"] == "PENDING"
    assert body["verification"]["record_name"] == "_nexusops.example.com"
    assert body["verification"]["record_type"] == "TXT"
    assert body["verification"]["record_value"].startswith("nxs-verify=")
    assert body["verified"] is False


@pytest.mark.parametrize(
    "name",
    ["localhost", "192.168.1.1", "example..com", "*.*.example.com", "exa mple.com", "example"],
)
async def test_domain_creation_rejects_invalid_names(client, owner, name):
    response = await client.post(f"{API}/domains", headers=owner["headers"], json={"name": name})
    assert response.status_code == 422, response.text


async def test_wildcard_domain_is_allowed_and_verified_at_the_apex(client, owner):
    created = await client.post(
        f"{API}/domains", headers=owner["headers"], json={"name": "*.wild.example.com"}
    )
    assert created.status_code == 201, created.text
    assert created.json()["verification"]["record_name"] == "_nexusops.wild.example.com"
    DNS["token"] = created.json()["verification"]["record_value"]
    outcome = await _run_verify(client, owner, created.json()["id"])
    assert outcome["status"] == DomainStatus.VERIFIED.value


async def test_duplicate_domain_is_a_conflict(client, owner):
    await _create_domain(client, owner, "dup.example.com")
    again = await client.post(
        f"{API}/domains", headers=owner["headers"], json={"name": "DUP.example.com"}
    )
    assert again.status_code == 409, again.text
    assert_error_code(again.json(), "DOMAIN_EXISTS")


async def test_project_from_another_organization_cannot_be_attached(client, owner, second_org):
    project = await client.post(
        f"{API}/projects", headers=second_org["headers"], json={"name": "foreign"}
    )
    assert project.status_code == 201, project.text
    response = await client.post(
        f"{API}/domains",
        headers=owner["headers"],
        json={"name": "crossproject.example.com", "project_id": project.json()["id"]},
    )
    assert response.status_code == 404, response.text
    assert_error_code(response.json(), "PROJECT_NOT_FOUND")


async def test_verification_token_is_never_returned_after_verification(client, owner):
    domain = await _verified_domain(client, owner, "tokenpolicy.example.com")
    detail = (await client.get(f"{API}/domains/{domain['id']}", headers=owner["headers"])).json()
    assert detail["verification"] is None
    listed = (await client.get(f"{API}/domains", headers=owner["headers"])).json()["items"]
    assert all(item["verification"] is None for item in listed)


async def test_a_pending_domain_keeps_showing_its_record_to_a_manager(client, owner):
    created = await _create_domain(client, owner, "pending.example.com")
    detail = (await client.get(f"{API}/domains/{created['id']}", headers=owner["headers"])).json()
    assert detail["verification"]["record_value"].startswith("nxs-verify=")


async def test_identical_tokens_are_never_shared_between_domains(client, owner):
    first = await _create_domain(client, owner, "one.example.com")
    second = await _create_domain(client, owner, "two.example.com")
    assert first["verification"]["record_value"] != second["verification"]["record_value"]


async def test_verified_names_are_platform_unique_with_a_cross_org_flip(client, owner, second_org):
    """The second organization wins; the first stops being the owner."""
    first = await _verified_domain(client, owner, "contested.example.com")

    created = await client.post(
        f"{API}/domains",
        headers=second_org["headers"],
        json={"name": "contested.example.com"},
    )
    # Two organizations may *track* a name; only one may hold it verified.
    assert created.status_code == 201, created.text
    DNS["token"] = created.json()["verification"]["record_value"]
    outcome = await _run_verify(client, second_org, created.json()["id"])
    assert outcome["status"] == DomainStatus.VERIFIED.value
    assert outcome["flipped"] == "1"

    first_after = (
        await client.get(f"{API}/domains/{first['id']}", headers=owner["headers"])
    ).json()
    assert first_after["status"] == "UNVERIFIED"
    assert "another organization" in first_after["last_error"]
    assert (
        await _count_rows_in_system_scope(
            Domain, name="contested.example.com", status=DomainStatus.VERIFIED
        )
        == 1
    )


async def test_the_released_organization_is_told_it_lost_the_name(client, owner, second_org):
    await _verified_domain(client, owner, "release.example.com")
    created = await client.post(
        f"{API}/domains",
        headers=second_org["headers"],
        json={"name": "release.example.com"},
    )
    DNS["token"] = created.json()["verification"]["record_value"]
    await _run_verify(client, second_org, created.json()["id"])

    events = (
        await client.get(
            f"{API}/events", headers=owner["headers"], params={"type": "DOMAIN_UNVERIFIED"}
        )
    ).json()
    assert any(
        event["data"].get("reason") == "claimed_by_another_organization"
        for event in events["items"]
    ), "the previous owner must be notified, not silently dropped"


async def test_verification_failures_move_through_the_lifecycle(client, owner):
    created = await _create_domain(client, owner, "failing.example.com")

    # No TXT record yet: a missing record, not a wrong one.
    observation = TxtObservation(STATUS_NO_TXT, values=(), nameservers=NS_SET)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: observation)
        outcome = await _run_verify(client, owner, created["id"])
    assert outcome["reason"] == "TXT_MISSING"
    detail = (await client.get(f"{API}/domains/{created['id']}", headers=owner["headers"])).json()
    assert detail["status"] != "VERIFIED"
    assert detail["attempt_count"] == 1

    # A wrong value is a mismatch.
    wrong = TxtObservation(STATUS_OK, values=("nxs-verify-wrong",), nameservers=NS_SET)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: wrong)
        outcome = await _run_verify(client, owner, created["id"])
    assert outcome["reason"] == "TXT_MISMATCH"

    # An authoritative outage is reported as unavailable, never as success.
    outage = TxtObservation(STATUS_TIMEOUT, detail="timed out")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: outage)
        outcome = await _run_verify(client, owner, created["id"])
    assert outcome["reason"] == "DNS_UNAVAILABLE"
    detail = (await client.get(f"{API}/domains/{created['id']}", headers=owner["headers"])).json()
    assert detail["status"] != "VERIFIED"


async def test_the_attempt_budget_is_bounded_and_the_domain_fails(client, owner):
    """Retry/backoff exhaustion lands in FAILED rather than retrying forever."""
    from app.services.domain_service import MAX_VERIFY_ATTEMPTS

    created = await _create_domain(client, owner, "budget.example.com")
    await _mutate_in_system_scope(
        Domain, created["id"], status=DomainStatus.PENDING, attempt_count=MAX_VERIFY_ATTEMPTS - 1
    )
    observation = TxtObservation(STATUS_NO_TXT, values=(), nameservers=NS_SET)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: observation)
        outcome = await _run_verify(client, owner, created["id"])
    assert outcome["status"] == DomainStatus.FAILED.value


async def test_a_verified_domain_goes_stale_then_unverified_when_proof_disappears(client, owner):
    domain = await _verified_domain(client, owner, "grace.example.com")
    # Simulate the grace window having elapsed.
    await _mutate_in_system_scope(
        Domain,
        domain["id"],
        proof_lost_at=datetime.now(UTC) - timedelta(hours=80),
        stale_expires_at=datetime.now(UTC) - timedelta(seconds=1),
        status=DomainStatus.STALE,
    )
    observation = TxtObservation(STATUS_NO_TXT, values=(), nameservers=NS_SET)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: observation)
        outcome = await _run_verify(client, owner, domain["id"])
    assert outcome["status"] == DomainStatus.UNVERIFIED.value
    detail = (await client.get(f"{API}/domains/{domain['id']}", headers=owner["headers"])).json()
    assert detail["status"] == "UNVERIFIED"


async def test_a_sweep_invalidates_a_changed_delegation_and_re_verification_restores_it(
    client, owner
):
    domain = await _verified_domain(client, owner, "nschange.example.com")
    moved = TxtObservation(STATUS_OK, values=(str(DNS["token"]),), nameservers=("ns9.other.test",))

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: moved)
        outcome = await _run_verify(client, owner, domain["id"], trigger="sweep")
    assert outcome["reason"] == "NS_CHANGED"
    detail = (await client.get(f"{API}/domains/{domain['id']}", headers=owner["headers"])).json()
    assert detail["status"] == "UNVERIFIED"

    # A deliberate re-verification accepts the new delegation.
    DNS["token"] = detail["verification"]["record_value"]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: moved)
        outcome = await _run_verify(client, owner, domain["id"], trigger="user")
    assert outcome["status"] == DomainStatus.VERIFIED.value


async def test_nameserver_ordering_and_case_do_not_cause_a_false_change(client, owner):
    domain = await _verified_domain(client, owner, "nsorder.example.com")
    reordered = TxtObservation(
        STATUS_OK,
        values=(str(DNS["token"]),),
        nameservers=("NS2.Example.NET", "ns1.example.net."),
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: reordered)
        outcome = await _run_verify(client, owner, domain["id"], trigger="sweep")
    assert outcome["status"] == DomainStatus.VERIFIED.value


async def test_domain_isolation_and_idor(client, owner, second_org):
    domain = await _verified_domain(client, owner, "idor.example.com")
    # Another organization cannot see, verify or delete it.
    assert (
        await client.get(f"{API}/domains/{domain['id']}", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.post(f"{API}/domains/{domain['id']}/verify", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.delete(f"{API}/domains/{domain['id']}", headers=second_org["headers"])
    ).status_code == 404
    listed = (await client.get(f"{API}/domains", headers=second_org["headers"])).json()
    assert listed["items"] == []
    # Guessing ids returns nothing else either.
    random_id = str(uuid.uuid4())
    assert (
        await client.get(f"{API}/domains/{random_id}", headers=owner["headers"])
    ).status_code == 404


async def test_event_payloads_never_contain_the_verification_token(client, owner):
    created = await _create_domain(client, owner, "eventsecret.example.com")
    token = created["verification"]["record_value"]
    events = (await client.get(f"{API}/events", headers=owner["headers"])).json()["items"]
    assert events
    assert token not in str(events)


async def test_audit_rows_never_contain_the_verification_token(client, owner, org_db):
    created = await _create_domain(client, owner, "auditsecret.example.com")
    token = created["verification"]["record_value"]
    rows = (
        (
            await org_db.execute(
                select(AuditLog).where(
                    AuditLog.action == "domain.created", AuditLog.metadata_.is_not(None)
                )
            )
        )
        .scalars()
        .all()
    )
    assert rows
    assert all(token not in str(row.metadata_) for row in rows)


async def test_domain_delete_is_blocked_while_routes_are_enabled(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "deleteme.example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.deleteme.example.com",
        enabled=True,
    )
    assert created.status_code == 201, created.text
    blocked = await client.delete(f"{API}/domains/{domain['id']}", headers=owner["headers"])
    assert blocked.status_code == 409, blocked.text
    assert_error_code(blocked.json(), "DOMAIN_HAS_ENABLED_ROUTES")
    del agent_token


# --- 3. routes ------------------------------------------------------------------


async def test_route_creation_validates_coverage_node_and_port(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "coverage.example.com")

    # Not covered by the domain.
    response = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.unrelated.example.com",
    )
    assert response.status_code == 422, response.text
    assert_error_code(response.json(), "HOSTNAME_NOT_COVERED")

    # One label deeper than allowed.
    response = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="a.b.coverage.example.com",
    )
    assert response.status_code == 422, response.text
    assert_error_code(response.json(), "HOSTNAME_NOT_COVERED")

    # Unpublished port.
    response = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, port=9999
    )
    assert response.status_code == 422, response.text
    assert_error_code(response.json(), "PORT_NOT_PUBLISHED")

    # The proxy's own port can never be an upstream.
    response = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, port=443
    )
    assert response.status_code == 422, response.text
    assert_error_code(response.json(), "PORT_RESERVED")

    # A covered name is accepted.
    ok = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.coverage.example.com",
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["enabled"] is False
    assert ok.json()["url"] == "http://app.coverage.example.com/"


async def test_a_container_on_another_node_is_refused(client, owner):
    first, agent_token, container_id = await _proxy_ready_node(client, owner)
    second, _agent_token2 = await _create_node(client, owner, hostname="second.integration.test")
    domain = await _verified_domain(client, owner, "crossnode.example.com")
    response = await _create_route(
        client, owner, domain=domain, node_id=second["id"], container_id=container_id
    )
    assert response.status_code == 422, response.text
    assert_error_code(response.json(), "CONTAINER_NOT_ON_NODE")
    del first, agent_token


async def test_a_stopped_container_cannot_be_enabled(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "stopped.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id
    )
    assert created.status_code == 201, created.text
    await _heartbeat(client, agent_token, status="EXITED")
    enabled = await client.post(
        f"{API}/routes/{created.json()['id']}/enable", headers=owner["headers"]
    )
    assert enabled.status_code == 409, enabled.text
    assert_error_code(enabled.json(), "UPSTREAM_NOT_RUNNING")


async def test_an_unverified_domain_cannot_have_an_enabled_route(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    created = await _create_domain(client, owner, "unverified.example.com")
    response = await _create_route(
        client, owner, domain=created, node_id=node["id"], container_id=container_id
    )
    assert response.status_code == 201, response.text
    enabled = await client.post(
        f"{API}/routes/{response.json()['id']}/enable", headers=owner["headers"]
    )
    assert enabled.status_code == 409, enabled.text
    assert_error_code(enabled.json(), "DOMAIN_NOT_VERIFIED")


async def test_a_domain_losing_verification_pulls_its_route(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "pull.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    assert created.status_code == 201, created.text
    route_id = created.json()["id"]
    await _drain(client, agent_token)
    assert (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()[
        "config_state"
    ] == "IN_SYNC"

    # The domain flips (NS change): the renderer must exclude the route...
    observation = TxtObservation(
        STATUS_OK, values=(str(DNS["token"]),), nameservers=("ns9.other.test",)
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(dns_verifier, "observe", lambda name: observation)
        await _run_verify(client, owner, domain["id"], trigger="sweep")

    # ...and the apply the flip queued must carry a bundle without it.
    handled = await _drain(client, agent_token)
    applies = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies, "a domain flip must queue an apply on the affected node"
    assert applies[-1]["params"]["bundle"]["manifest"] == []
    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "STALE"
    assert "domain" in state["last_apply_error"]


async def test_duplicate_enabled_routes_on_one_node_conflict(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "dupe.example.com")
    first = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.dupe.example.com",
        enabled=True,
    )
    assert first.status_code == 201, first.text
    second = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.dupe.example.com",
        enabled=True,
    )
    assert second.status_code == 409, second.text
    assert_error_code(second.json(), "ROUTE_CONFLICT")


async def test_enabling_writes_the_bundle_and_the_agent_result_sets_in_sync(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "apply.example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.apply.example.com",
        enabled=True,
    )
    assert created.status_code == 201, created.text
    route_id = created.json()["id"]

    handled = await _drain(client, agent_token)
    applies = [
        (claimed, reported) for op_type, claimed, reported in handled if op_type == "nginx.apply"
    ]
    assert len(applies) == 1
    claimed, reported = applies[0]
    bundle = claimed["params"]["bundle"]
    assert reported["status"] == "SUCCEEDED"
    # The bundle is the documented tree: the http-level file plus the fragment.
    assert bundle["provider"] == "nginx"
    assert len(bundle["files"]) == 2
    assert bundle["files"][0]["path"] == "/etc/nexusops/nginx/nexusops.conf"
    assert bundle["files"][1]["path"].startswith("/etc/nexusops/nginx/routes.d/r-")
    assert bundle["manifest"] == [route_id]

    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "IN_SYNC"
    assert state["last_bundle_id"] == bundle["bundle_id"]
    assert state["last_applied_at"]

    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["live_bundle_id"] == bundle["bundle_id"]
    assert proxy["expected_bundle_id"] == bundle["bundle_id"]
    assert proxy["drift"] is False


async def test_a_failed_apply_marks_the_route_failed_with_a_sanitized_reason(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "failapply.example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        enabled=True,
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token, outcome="failed")

    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "FAILED"
    assert "emerg" in state["last_apply_error"]
    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["route_failed"] == 1


async def test_a_rolled_back_apply_leaves_the_previous_configuration_serving(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "rollback.example.com")
    first = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.rollback.example.com",
        enabled=True,
    )
    await _drain(client, agent_token)  # first route applies cleanly
    assert (
        await client.get(f"{API}/routes/{first.json()['id']}", headers=owner["headers"])
    ).json()["config_state"] == "IN_SYNC"

    # A second route whose apply fails and rolls back.
    second = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="second.rollback.example.com",
        path="/api",
        enabled=True,
    )
    assert second.status_code == 201, second.text
    await _drain(client, agent_token, outcome="rolled_back")

    second_state = (
        await client.get(f"{API}/routes/{second.json()['id']}", headers=owner["headers"])
    ).json()
    assert second_state["config_state"] == "STALE"
    assert second_state["last_apply_error"]
    # The first route is still live: the rollback restored the previous tree.
    first_state = (
        await client.get(f"{API}/routes/{first.json()['id']}", headers=owner["headers"])
    ).json()
    assert first_state["config_state"] == "IN_SYNC"


async def test_a_failed_rollback_is_reported_as_a_critical_alert(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "rollbackfail.example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        enabled=True,
    )
    await _drain(client, agent_token, outcome="rollback_failed")
    state = (
        await client.get(f"{API}/routes/{created.json()['id']}", headers=owner["headers"])
    ).json()
    assert state["config_state"] == "FAILED"

    alerts = (await client.get(f"{API}/alerts", headers=owner["headers"])).json()["items"]
    assert any("rollback failed" in alert["title"].lower() for alert in alerts)


async def test_a_disabled_route_is_removed_at_the_next_apply(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "disable.example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        enabled=True,
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token)

    disabled = await client.post(f"{API}/routes/{route_id}/disable", headers=owner["headers"])
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["enabled"] is False
    handled = await _drain(client, agent_token)
    applies = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies
    assert applies[-1]["params"]["bundle"]["manifest"] == []


async def test_deleting_the_only_route_still_reaches_the_node(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "delete-route.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token)

    deleted = await client.delete(f"{API}/routes/{route_id}", headers=owner["headers"])
    assert deleted.status_code == 204, deleted.text
    handled = await _drain(client, agent_token)
    applies = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies, "the empty bundle must still be applied so the fragment is removed"
    assert applies[-1]["params"]["bundle"]["manifest"] == []
    assert len(applies[-1]["params"]["bundle"]["files"]) == 1  # only the http-level file


async def test_an_unchanged_desired_state_does_not_re_queue_an_apply(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "noop.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token)

    # Touching an unrelated field re-renders the same bundle; the desired state is
    # already live, so no second operation is queued.
    updated = await client.patch(
        f"{API}/routes/{route_id}", headers=owner["headers"], json={"path": "/"}
    )
    assert updated.status_code == 200, updated.text
    beat = await _heartbeat(client, agent_token)
    assert beat["pending_operations"] == []


async def test_drift_is_detected_and_re_applied(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "drift.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token)

    # An operator asks the node for its live state; the node answers with a
    # *different* fingerprint than the desired bundle.
    refreshed = await client.post(
        f"{API}/nodes/{node['id']}/proxy/status/refresh", headers=owner["headers"]
    )
    assert refreshed.status_code == 200, refreshed.text
    beat = await _heartbeat(client, agent_token)
    for operation_id in beat["pending_operations"]:
        claimed = await _claim(client, agent_token, operation_id)
        assert claimed["type"] == "nginx.status"
        await _report(
            client,
            agent_token,
            operation_id,
            {
                "ok": True,
                "output": {
                    "live_bundle_id": "0" * 64,
                    "nginx_version": "1.27.5",
                    "config_test_ok": True,
                },
            },
        )
    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "STALE"
    assert "drift" in state["last_apply_error"]
    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["drift"] is True

    drift_events = (
        await client.get(
            f"{API}/events", headers=owner["headers"], params={"type": "NGINX_DRIFT_DETECTED"}
        )
    ).json()["items"]
    assert drift_events

    # Recovery: a safe re-apply of the last known-good desired bundle puts the
    # node back in sync.
    applied = await client.post(f"{API}/nodes/{node['id']}/proxy/apply", headers=owner["headers"])
    assert applied.status_code == 200, applied.text
    await _drain(client, agent_token)
    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "IN_SYNC"
    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["drift"] is False

    # The scheduled sweep is what performs this unattended, and it is safe to run
    # with nothing to do.
    from app.tasks.domain_routing import sweep_routes

    # The sweeps are Celery (sync) tasks that own their event loop, so an async
    # test drives them off-loop rather than calling them inside it.
    counts = await asyncio.to_thread(sweep_routes)
    assert counts["nodes"] >= 1


async def test_offline_node_does_not_flood_the_operation_queue(client, owner):
    """A node that stays offline accumulates one op, not one per attempt."""
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "offline.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    assert created.status_code == 201, created.text
    listed = (
        await client.get(
            f"{API}/operations", headers=owner["headers"], params={"node_id": node["id"]}
        )
    ).json()
    applies = [op for op in listed["items"] if op["type"] == "nginx.apply"]
    assert len(applies) == 1

    # A second enable that renders the same bundle must not queue another apply.
    await client.post(f"{API}/routes/{created.json()['id']}/enable", headers=owner["headers"])
    listed = (
        await client.get(
            f"{API}/operations", headers=owner["headers"], params={"node_id": node["id"]}
        )
    ).json()
    assert len([op for op in listed["items"] if op["type"] == "nginx.apply"]) == 1


async def test_route_isolation_and_idor(client, owner, second_org):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "routeidor.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id
    )
    route_id = created.json()["id"]
    assert (
        await client.get(f"{API}/routes/{route_id}", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.post(f"{API}/routes/{route_id}/enable", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.delete(f"{API}/routes/{route_id}", headers=second_org["headers"])
    ).status_code == 404
    assert (await client.get(f"{API}/routes", headers=second_org["headers"])).json()["items"] == []
    assert (
        await client.get(f"{API}/routes/{uuid.uuid4()}", headers=owner["headers"])
    ).status_code == 404


async def test_a_foreign_organization_cannot_route_to_this_nodes_container(
    client, owner, second_org
):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _create_domain(client, second_org, "foreign.example.com")
    response = await client.post(
        f"{API}/routes",
        headers=second_org["headers"],
        json={
            "domain_id": domain["id"],
            "hostname": "foreign.example.com",
            "node_id": node["id"],
            "container_id": container_id,
            "port": 8081,
        },
    )
    assert response.status_code == 404, response.text
    assert_error_code(response.json(), "NODE_NOT_FOUND")


async def test_redirect_target_must_be_a_verified_name_in_the_organization(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "redirect.example.com")
    bad = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        redirect={"to_host": "someone-elses.example.net", "code": 301},
    )
    assert bad.status_code == 422, bad.text
    assert_error_code(bad.json(), "REDIRECT_TARGET_UNVERIFIED")

    ok = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        redirect={"to_host": "www.redirect.example.com", "code": 302},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["redirect"]["code"] == 302
    # A scheme change is not expressible at all in Phase 4.
    refused = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        redirect={"to_host": "www.redirect.example.com", "to_scheme": "https"},
    )
    assert refused.status_code == 422, refused.text


async def test_schema_rejects_injection_payloads(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "injection.example.com")
    payloads = [
        {"headers": [{"name": "X-Test", "value": "$request_uri"}]},
        {"headers": [{"name": "X-Test\ninjected", "value": "x"}]},
        {"headers": [{"name": "Host", "value": "evil.test", "target": "proxy"}]},
        {"headers": [{"name": "X-Test", "value": "x", "target": "other"}]},
        {"path": "/a;b"},
        {"path": "/$variable"},
        {"rate_limit": {"requests": 10, "burst": 99}},
        {"rate_limit": {"requests": 10, "window": "10s"}},
        {"unknown_field": 1},
    ]
    for extra in payloads:
        response = await _create_route(
            client, owner, domain=domain, node_id=node["id"], container_id=container_id, **extra
        )
        assert response.status_code == 422, f"{extra} should be refused: {response.text}"


async def test_route_update_re_validates_and_re_applies(client, owner):
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "update.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token)

    updated = await client.patch(
        f"{API}/routes/{route_id}",
        headers=owner["headers"],
        json={"path": "/api", "rate_limit": {"requests": 20, "window": "1s", "burst": 5}},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["path"] == "/api"
    handled = await _drain(client, agent_token, outcome="applied")
    applies = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies
    bundle = applies[-1]["params"]["bundle"]
    fragment = next(
        f for f in bundle["files"] if f["path"].startswith("/etc/nexusops/nginx/routes.d/")
    )
    assert "location /api {" in fragment["content"]
    assert "limit_req zone=nx_" in fragment["content"]

    # An update that breaks a rule is refused rather than stored.
    refused = await client.patch(
        f"{API}/routes/{route_id}", headers=owner["headers"], json={"path": "/a b"}
    )
    assert refused.status_code == 422, refused.text


# --- 4. monitors ----------------------------------------------------------------


async def test_enabling_a_route_attaches_an_http_uptime_monitor(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "monitor.example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        hostname="app.monitor.example.com",
        path="/health",
        enabled=True,
    )
    assert created.status_code == 201, created.text
    monitor_id = created.json()["monitor_id"]
    assert monitor_id

    monitor = (await client.get(f"{API}/monitors/{monitor_id}", headers=owner["headers"])).json()
    # HTTP, not HTTPS: TLS is Phase 5, so a certificate-expiry target cannot exist.
    assert monitor["url"] == "http://app.monitor.example.com/health"
    assert monitor["enabled"] is True
    assert monitor["status"] in ("PENDING", "UP")

    # The row is a ROUTE target, which is what the polymorphic model added.
    assert (
        await _count_rows_in_system_scope(
            Monitor, id=uuid.UUID(monitor_id), target_type=MonitorTargetType.ROUTE
        )
        == 1
    )


async def test_disabling_a_route_parks_its_monitor(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "monitoroff.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    monitor_id = created.json()["monitor_id"]
    disabled = await client.post(
        f"{API}/routes/{created.json()['id']}/disable", headers=owner["headers"]
    )
    assert disabled.status_code == 200, disabled.text
    monitor = (await client.get(f"{API}/monitors/{monitor_id}", headers=owner["headers"])).json()
    assert monitor["enabled"] is False
    assert monitor["status"] == "PAUSED"


async def test_monitor_optout_is_respected(client, owner):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "monitoroptout.example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        enabled=True,
        monitor_optout=True,
    )
    assert created.status_code == 201, created.text
    assert created.json()["monitor_id"] is None
    assert await _count_rows_in_system_scope(Monitor, target_type=MonitorTargetType.ROUTE) == 0


async def test_existing_url_monitors_are_untouched_by_routing(client, owner):
    """The polymorphic model must not disturb the original target shape."""
    created = await client.post(
        f"{API}/monitors",
        headers=owner["headers"],
        json={"name": "legacy url monitor", "url": "sim://probe/healthy"},
    )
    assert created.status_code == 201, created.text
    listed = (await client.get(f"{API}/monitors", headers=owner["headers"])).json()["items"]
    row = next(item for item in listed if item["id"] == created.json()["id"])
    # The route-side extension never re-shapes a plain URL monitor.
    assert row["url"] == "sim://probe/healthy"


async def test_route_monitor_checks_run_through_the_existing_pipeline(client, owner):
    """The auto-attached monitor stays on the check → incident → notification path."""
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "monitorpipeline.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    monitor_id = created.json()["monitor_id"]
    checks = await client.get(f"{API}/monitors/{monitor_id}/checks", headers=owner["headers"])
    assert checks.status_code == 200, checks.text
    # The scheduling cursor exists and is due immediately, exactly like a
    # hand-created URL monitor.
    monitor = (await client.get(f"{API}/monitors/{monitor_id}", headers=owner["headers"])).json()
    assert monitor["next_check_at"]
    assert monitor["interval_seconds"] >= 10


async def test_route_monitors_are_organization_scoped(client, owner, second_org):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "monitorscope.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    monitor_id = created.json()["monitor_id"]
    assert (
        await client.get(f"{API}/monitors/{monitor_id}", headers=second_org["headers"])
    ).status_code == 404


# --- 5. worker scoping ----------------------------------------------------------


async def test_the_sweep_re_verifies_due_domains_across_tenants(client, owner):
    from app.tasks.domain_routing import sweep_domains

    await _verified_domain(client, owner, "sweep.example.com")
    # Make both the re-check and the apply due.
    await _mutate_in_system_scope(
        Domain,
        (await client.get(f"{API}/domains", headers=owner["headers"])).json()["items"][0]["id"],
        next_check_at=datetime.now(UTC) - timedelta(seconds=5),
    )
    result = await asyncio.to_thread(sweep_domains)
    assert result["checked"] >= 1
    assert result["verified"] >= 1


async def test_domain_events_and_audit_are_organization_scoped(client, owner, second_org, org_db):
    await _verified_domain(client, owner, "scoped.example.com")
    rows = (await org_db.execute(select(SystemEvent))).scalars().all()
    assert rows
    assert all(str(row.org_id) == owner["active_organization_id"] for row in rows)
    other = (await client.get(f"{API}/events", headers=second_org["headers"])).json()["items"]
    assert all("scoped.example.com" not in str(event) for event in other)


async def test_the_domain_sweep_never_leaks_a_verification_token_into_events(client, owner):
    created = await _create_domain(client, owner, "sweeptoken.example.com")
    from app.tasks.domain_routing import sweep_domains

    await _mutate_in_system_scope(
        Domain,
        created["id"],
        status=DomainStatus.PENDING,
        next_check_at=datetime.now(UTC) - timedelta(seconds=5),
    )
    await asyncio.to_thread(sweep_domains)
    events = (await client.get(f"{API}/events", headers=owner["headers"])).json()["items"]
    assert str(DNS["token"]) not in str(events)
    assert "nxs-verify=" not in str(events)


# --- 6. ownership transfer: the released organization's nodes ------------------
#
# The defect this section pins: releasing a competing claim changed a *different*
# organization's domain, but only the new owner's nodes were ever asked to apply.
# The old organization's routes stopped being rendered while the configuration
# already on its nodes kept carrying them — the name was served by an
# organization that no longer controlled it.


async def _flip_name_to(client, second_org, name: str) -> dict:
    """Have *second_org* prove control of *name*, returning the verify outcome."""
    claimed = await client.post(
        f"{API}/domains", headers=second_org["headers"], json={"name": name}
    )
    assert claimed.status_code == 201, claimed.text
    DNS["token"] = claimed.json()["verification"]["record_value"]
    outcome = await _run_verify(client, second_org, claimed.json()["id"])
    assert outcome["status"] == DomainStatus.VERIFIED.value, outcome
    outcome["domain_id"] = claimed.json()["id"]
    return outcome


async def test_a_transfer_pulls_the_previous_owners_route_from_its_node(
    client, owner, second_org, org_db
):
    """The old owner's node is told to drop the name, and says when it has."""
    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "handover.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    assert created.status_code == 201, created.text
    route_id = created.json()["id"]
    handled = await _drain(client, agent_token)
    applies = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies and applies[-1]["params"]["bundle"]["manifest"] == [route_id]
    assert (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()[
        "config_state"
    ] == "IN_SYNC"

    # The second organization proves control of the same name.
    outcome = await _flip_name_to(client, second_org, "handover.example.com")
    assert outcome["flipped"] == "1"
    # The release discovered the node that has to be told, before the routes
    # became invisible to every ordinary tenant scope.
    assert outcome["released_nodes"] == "1"

    # The previous owner learns what happened, and nothing about the new one.
    first = (await client.get(f"{API}/domains/{domain['id']}", headers=owner["headers"])).json()
    assert first["status"] == "UNVERIFIED"
    events = (
        await client.get(
            f"{API}/events", headers=owner["headers"], params={"type": "DOMAIN_UNVERIFIED"}
        )
    ).json()["items"]
    assert any(event["data"].get("reason") == "claimed_by_another_organization" for event in events)
    assert outcome["domain_id"] not in str(events), "no new-owner data may reach the old owner"
    released = (
        (await org_db.execute(select(AuditLog).where(AuditLog.action == "domain.claim_released")))
        .scalars()
        .all()
    )
    assert released, "the release is audited in the organization that lost the name"
    assert released[0].metadata_["routes_pulled"] == 1
    assert released[0].metadata_["nodes_affected"] == 1

    # The route is visibly not being served, and nothing has claimed otherwise.
    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["enabled"] is True  # still the old owner's row, still its to fix
    assert state["config_state"] == "STALE"
    assert state["last_apply_error"]

    # ...and the node really was asked to remove it: the queued bundle excludes it.
    handled = await _drain(client, agent_token)
    applies = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies, "the released organization's node must receive an apply"
    assert applies[-1]["params"]["bundle"]["manifest"] == []
    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["expected_bundle_id"] == proxy["live_bundle_id"]
    assert proxy["drift"] is False
    # The route stays unresolved even so: it is not in the desired tree, so it is
    # never reported as applied again until its domain is verified.
    assert (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()[
        "config_state"
    ] == "STALE"

    # Neither organization can reach the other's resources.
    assert (
        await client.get(f"{API}/routes/{route_id}", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.post(f"{API}/routes/{route_id}/disable", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.get(f"{API}/domains/{domain['id']}", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.get(f"{API}/nodes/{node['id']}", headers=second_org["headers"])
    ).status_code == 404
    assert (await client.get(f"{API}/routes", headers=second_org["headers"])).json()["items"] == []

    # The new owner serves the name from its own node, with its own route.
    node_b, token_b, container_b = await _proxy_ready_node(
        client, second_org, hostname="handover-b.integration.test"
    )
    domain_b = (
        await client.get(f"{API}/domains/{outcome['domain_id']}", headers=second_org["headers"])
    ).json()
    route_b = await _create_route(
        client,
        second_org,
        domain=domain_b,
        node_id=node_b["id"],
        container_id=container_b,
        enabled=True,
    )
    assert route_b.status_code == 201, route_b.text
    route_b_id = route_b.json()["id"]
    handled = await _drain(client, token_b)
    applies_b = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies_b and applies_b[-1]["params"]["bundle"]["manifest"] == [route_b_id]
    assert (await client.get(f"{API}/routes/{route_b_id}", headers=second_org["headers"])).json()[
        "config_state"
    ] == "IN_SYNC"
    assert (
        await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])
    ).status_code == 200  # the old owner still sees its own row, and only its own


async def test_an_offline_node_keeps_the_revoked_route_unresolved_until_it_returns(
    client, owner, second_org
):
    """Offline during a transfer: unresolved, bounded, and never a false success."""
    from app.services import proxy_service
    from app.tasks.domain_routing import sweep_routes

    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "offlinehandover.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token)
    assert (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()[
        "config_state"
    ] == "IN_SYNC"

    # The node is offline when the name changes hands. No heartbeat is sent from
    # here on (it would bring the node back), so status is read over the API.
    await _mutate_in_system_scope(Server, node["id"], status=ServerStatus.OFFLINE)
    outcome = await _flip_name_to(client, second_org, "offlinehandover.example.com")
    assert outcome["released_nodes"] == "1"

    # Nothing was queued for a node that cannot take it, and the route reads as
    # unresolved rather than as removed.
    assert await _live_operations(client, owner, node["id"]) == []
    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "STALE"
    assert state["last_apply_error"]
    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["eligible"] is False
    assert proxy["drift"] is True
    assert proxy["expected_bundle_id"] != proxy["live_bundle_id"]

    # The sweep keeps retrying and stays bounded: no operation is created and the
    # difference is never announced as repaired.
    counts = await asyncio.to_thread(sweep_routes)
    assert counts["nodes"] >= 1
    assert counts.get(proxy_service.RECONCILE_DEFERRED, 0) >= 1
    assert counts.get(proxy_service.RECONCILE_RECOVERY_QUEUED, 0) == 0
    assert await _live_operations(client, owner, node["id"], op_type="nginx.apply") == []
    assert (
        await client.get(
            f"{API}/events",
            headers=owner["headers"],
            params={"types": "NGINX_DRIFT_RECOVERED"},
        )
    ).json()["items"] == []

    # The node comes back: the next tick queues exactly one apply, and the
    # difference is reported repaired only from the agent's own outcome.
    await _heartbeat(client, agent_token)
    counts = await asyncio.to_thread(sweep_routes)
    assert counts.get(proxy_service.RECONCILE_RECOVERY_QUEUED, 0) == 1
    handled = await _drain(client, agent_token)
    applies = [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    assert applies and applies[-1]["params"]["bundle"]["manifest"] == []
    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["expected_bundle_id"] == proxy["live_bundle_id"]
    assert proxy["drift"] is False
    recovered = (
        await client.get(
            f"{API}/events",
            headers=owner["headers"],
            params={"types": "NGINX_DRIFT_RECOVERED"},
        )
    ).json()["items"]
    assert recovered, "the repair is announced once the node has applied it"
    # The route itself is still not served, and still says why.
    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "STALE"
    assert "unverified" in state["last_apply_error"]


async def test_the_sweep_repairs_drift_and_bounds_a_repeatedly_failing_node(client, owner):
    """A detected difference is repaired unattended — and bounded while it isn't."""
    from app.services import proxy_service
    from app.tasks.domain_routing import sweep_routes

    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "sweepdrift.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    route_id = created.json()["id"]
    await _drain(client, agent_token)

    # The node reports — and keeps — a bundle that is not the desired one. Nothing
    # has queued an apply: the desired state itself never changed.
    await _mutate_in_system_scope(
        Server,
        node["id"],
        proxy_state={"applied_bundle_id": "0" * 64, "live_bundle_id": "0" * 64},
    )

    counts = await asyncio.to_thread(sweep_routes)
    assert counts.get(proxy_service.RECONCILE_RECOVERY_QUEUED, 0) == 1
    # A second tick while the apply is still queued adds nothing to the queue.
    counts = await asyncio.to_thread(sweep_routes)
    assert counts.get(proxy_service.RECONCILE_RECOVERY_QUEUED, 0) == 0
    assert counts.get(proxy_service.RECONCILE_APPLY_IN_FLIGHT, 0) == 1
    live = await _live_operations(client, owner, node["id"], op_type="nginx.apply")
    assert len(live) == 1, "the reconciler must never build an operation queue"

    # The node fails the apply and restores its previous configuration: the
    # difference is still outstanding, so the next attempt is backed off rather
    # than repeated on every tick.
    handled = await _drain(client, agent_token, outcome="failed")
    assert [claimed for op_type, claimed, _ in handled if op_type == "nginx.apply"]
    counts = await asyncio.to_thread(sweep_routes)
    assert counts.get(proxy_service.RECONCILE_RECOVERY_QUEUED, 0) == 0
    assert counts.get(proxy_service.RECONCILE_DEFERRED, 0) == 1
    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "FAILED"  # reported as the node reported it
    assert await _live_operations(client, owner, node["id"], op_type="nginx.apply") == []
    assert (
        await client.get(
            f"{API}/events",
            headers=owner["headers"],
            params={"types": "NGINX_DRIFT_RECOVERED"},
        )
    ).json()["items"] == [], "a failed apply is not a recovery"

    booked = await _node_proxy_state(node["id"])
    assert booked["recovery_attempts"] == 1
    assert booked["next_recovery_at"], "a failing node must be given a retry window"
    assert booked["recovery_pending"] is True

    # Clear the window instead of sleeping through it, then let the retry succeed.
    await _mutate_in_system_scope(
        Server, node["id"], proxy_state={**booked, "next_recovery_at": None}
    )
    counts = await asyncio.to_thread(sweep_routes)
    assert counts.get(proxy_service.RECONCILE_RECOVERY_QUEUED, 0) == 1
    await _drain(client, agent_token)

    state = (await client.get(f"{API}/routes/{route_id}", headers=owner["headers"])).json()
    assert state["config_state"] == "IN_SYNC"
    proxy = (
        await client.get(f"{API}/nodes/{node['id']}/proxy/status", headers=owner["headers"])
    ).json()
    assert proxy["drift"] is False
    assert (
        await client.get(
            f"{API}/events",
            headers=owner["headers"],
            params={"types": "NGINX_DRIFT_RECOVERED"},
        )
    ).json()["items"], "the repair is announced only after the node applied it"
    after = await _node_proxy_state(node["id"])
    assert after["recovery_attempts"] == 0
    assert after["next_recovery_at"] is None
    assert after["recovery_pending"] is False


async def test_a_converged_node_is_polled_on_an_interval_not_every_tick(client, owner):
    """The reconciler does not turn a healthy node into a status-poll loop."""
    from app.services import proxy_service
    from app.tasks.domain_routing import sweep_routes

    node, agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "converged.example.com")
    await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id, enabled=True
    )
    await _drain(client, agent_token)
    before = await _live_operations(client, owner, node["id"], op_type="nginx.apply")

    counts = await asyncio.to_thread(sweep_routes)
    assert counts["nodes"] >= 1
    assert counts.get(proxy_service.RECONCILE_RECOVERY_QUEUED, 0) == 0
    after = await _live_operations(client, owner, node["id"], op_type="nginx.apply")
    assert after == before, "a converged node is not re-applied on every tick"
    # Its fingerprint is still verified — just not on every tick.
    assert counts.get(proxy_service.RECONCILE_STATUS_REQUESTED, 0) == 1
    counts = await asyncio.to_thread(sweep_routes)
    assert counts.get(proxy_service.RECONCILE_STATUS_REQUESTED, 0) == 0
    assert counts.get(proxy_service.RECONCILE_IN_SYNC, 0) == 1
