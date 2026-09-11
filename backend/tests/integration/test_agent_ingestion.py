"""Agent ingest pipeline: hello, heartbeat, staleness transitions, events."""

from __future__ import annotations

import uuid

import pytest
from app.models import Container, MetricSnapshot, SystemEvent
from sqlalchemy import func, select

from .helpers import API, server_payload

pytestmark = pytest.mark.integration

HELLO = {
    "agent_version": "test-agent/0.1",
    "hostname": "ingest.integration.test",
    "os_name": "Ubuntu",
    "os_version": "24.04 LTS",
    "arch": "x86_64",
    "cpu_cores": 8,
    "memory_total_mb": 16384,
    "disk_total_gb": 500,
}


def _heartbeat(**overrides):
    payload = {
        "cpu_percent": 42.5,
        "mem_used_mb": 4096.0,
        "mem_percent": 25.0,
        "disk_used_gb": 120.0,
        "disk_percent": 24.0,
        "net_rx_kb_s": 12.5,
        "net_tx_kb_s": 3.2,
        "load1": 0.4,
        "uptime_seconds": 86_400,
        "containers": [
            {
                "container_id": "abc123def456",
                "name": "web",
                "status": "RUNNING",
                "health": "HEALTHY",
                "image_ref": "nginx:1.27",
                "restart_count": 0,
                "cpu_percent": 3.1,
                "mem_used_mb": 128.0,
            }
        ],
    }
    payload.update(overrides)
    return payload


async def _enrolled(client, owner, name="srv-ingest"):
    created = (
        await client.post(f"{API}/servers", headers=owner["headers"], json=server_payload(name))
    ).json()
    token = (
        await client.post(f"{API}/servers/{created['id']}/agent-token", headers=owner["headers"])
    ).json()["agent_token"]
    return created, token


async def test_unknown_token_rejected(client, owner):
    for header in ({}, {"X-Agent-Token": "garbage"}, {"X-Agent-Token": "nxa_deadbeef"}):
        response = await client.post(f"{API}/agent/hello", json=HELLO, headers=header)
        assert response.status_code == 401, f"{header} => {response.status_code}"


async def test_hello_persists_facts_and_negotiates_interval(client, owner):
    created, token = await _enrolled(client, owner)
    response = await client.post(f"{API}/agent/hello", json=HELLO, headers={"X-Agent-Token": token})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["server_id"] == created["id"]
    assert body["name"] == "srv-ingest"
    assert body["heartbeat_interval_seconds"] >= 5

    detail = (await client.get(f"{API}/servers/{created['id']}", headers=owner["headers"])).json()
    assert detail["enrolled"] is True
    assert detail["os_name"] == "Ubuntu"
    assert detail["cpu_cores"] == 8


async def test_heartbeat_updates_status_metrics_and_containers(client, owner, db):
    created, token = await _enrolled(client, owner)

    beat = await client.post(
        f"{API}/agent/heartbeat", json=_heartbeat(), headers={"X-Agent-Token": token}
    )
    assert beat.status_code == 204, beat.text

    detail = (await client.get(f"{API}/servers/{created['id']}", headers=owner["headers"])).json()
    assert detail["status"] == "ONLINE"
    assert detail["last_heartbeat_at"] is not None
    assert detail["counts"] == {"containers_running": 1, "containers_total": 1}

    metrics = await db.execute(
        select(func.count())
        .select_from(MetricSnapshot)
        .where(MetricSnapshot.server_id == uuid.UUID(created["id"]))
    )
    assert metrics.scalar_one() >= 1

    container = (await db.execute(select(Container))).scalar_one()
    assert container.name == "web"
    assert container.container_id == "abc123def456"

    # A stopped transition must be mirrored and produce a CONTAINER_STOPPED event.
    stopped = _heartbeat(
        containers=[
            {
                "container_id": "abc123def456",
                "name": "web",
                "status": "EXITED",
                "health": "NONE",
                "restart_count": 0,
            }
        ]
    )
    again = await client.post(
        f"{API}/agent/heartbeat", json=stopped, headers={"X-Agent-Token": token}
    )
    assert again.status_code == 204

    event_types = {
        row[0]
        for row in (
            await db.execute(select(SystemEvent.type).where(SystemEvent.type.like("CONTAINER%")))
        ).all()
    }
    assert "CONTAINER_STARTED" in event_types
    assert "CONTAINER_STOPPED" in event_types


async def test_malformed_heartbeat_is_422_not_500(client, owner):
    _, token = await _enrolled(client, owner, "srv-badbeat")
    bad = _heartbeat(cpu_percent=150.0)  # outside Field(ge=0, le=100)
    response = await client.post(
        f"{API}/agent/heartbeat", json=bad, headers={"X-Agent-Token": token}
    )
    assert response.status_code == 422
