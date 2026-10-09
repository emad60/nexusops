"""Unit tests for agent-facing schemas (heartbeat + container payloads)."""

from __future__ import annotations

import pytest
from app.schemas.agent import AgentContainerIn, AgentHeartbeatIn, AgentHelloIn
from pydantic import ValidationError


def _container(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "container_id": "abc123def",
        "name": "web-1",
        "status": "RUNNING",
    }
    payload.update(overrides)
    return payload


def _heartbeat(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "cpu_percent": 12.5,
        "mem_used_mb": 1024.0,
        "mem_percent": 40.0,
        "disk_used_gb": 20.0,
        "disk_percent": 55.0,
    }
    payload.update(overrides)
    return payload


# --- heartbeat ------------------------------------------------------------------


def test_minimal_heartbeat_accepted() -> None:
    hb = AgentHeartbeatIn(**_heartbeat())
    assert hb.containers == []
    assert hb.cpu_percent == 12.5
    # Network rates are optional and default to **unavailable** (None), not 0.0:
    # a fabricated zero is indistinguishable from a genuinely idle interface, so
    # the schema refuses to invent one.
    assert hb.net_rx_kb_s is None
    assert hb.net_tx_kb_s is None
    assert hb.load1 == 0
    assert hb.uptime_seconds == 0
    assert hb.os_name is None


def test_measured_network_rates_round_trip() -> None:
    hb = AgentHeartbeatIn(**_heartbeat(net_rx_kb_s=12.5, net_tx_kb_s=3.25))
    assert hb.net_rx_kb_s == 12.5
    assert hb.net_tx_kb_s == 3.25


def test_missing_required_metric_rejected() -> None:
    incomplete = _heartbeat()
    del incomplete["mem_used_mb"]
    with pytest.raises(ValidationError):
        AgentHeartbeatIn(**incomplete)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cpu_percent", 100.01),
        ("cpu_percent", -0.1),
        ("mem_used_mb", -1),
        ("mem_percent", 101),
        ("disk_percent", -5),
        ("net_rx_kb_s", -0.001),
        ("load1", 10_001),
        ("uptime_seconds", -1),
    ],
)
def test_out_of_range_metrics_rejected(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        AgentHeartbeatIn(**_heartbeat(**{field: value}))


def test_upper_bounds_are_inclusive() -> None:
    hb = AgentHeartbeatIn(
        **_heartbeat(cpu_percent=100, mem_percent=100, disk_percent=100, load1=10_000)
    )
    assert hb.cpu_percent == 100


def test_more_than_200_containers_rejected() -> None:
    containers = [_container(container_id=f"c{i:03d}") for i in range(201)]
    with pytest.raises(ValidationError):
        AgentHeartbeatIn(**_heartbeat(containers=containers))
    ok = AgentHeartbeatIn(**_heartbeat(containers=containers[:200]))
    assert len(ok.containers) == 200


# --- containers -------------------------------------------------------------------


@pytest.mark.parametrize("status", ["RUNNING", "EXITED", "PAUSED", "CREATED", "RESTARTING", "DEAD"])
def test_allowed_container_statuses(status: str) -> None:
    assert AgentContainerIn(**_container(status=status)).status.value == status


def test_removed_status_never_accepted() -> None:
    with pytest.raises(ValidationError, match="Unsupported container status"):
        AgentContainerIn(**_container(status="REMOVED"))


def test_bogus_status_string_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentContainerIn(**_container(status="DANCING"))


@pytest.mark.parametrize("cid", ["abc123", "A_.-9", "x" * 72])
def test_container_id_pattern_accepts(cid: str) -> None:
    assert AgentContainerIn(**_container(container_id=cid)).container_id == cid


@pytest.mark.parametrize("cid", ["", "-leading", ".dot", "has space", "x" * 73])
def test_container_id_pattern_rejects(cid: str) -> None:
    with pytest.raises(ValidationError):
        AgentContainerIn(**_container(container_id=cid))


def test_container_numeric_bounds() -> None:
    c = AgentContainerIn(**_container(restart_count=0, cpu_percent=0, mem_used_mb=0))
    assert c.restart_count == 0
    with pytest.raises(ValidationError):
        AgentContainerIn(**_container(restart_count=-1))
    with pytest.raises(ValidationError):
        AgentContainerIn(**_container(cpu_percent=-1))
    assert AgentContainerIn(**_container(cpu_percent=10_000)).cpu_percent == 10_000


def test_health_is_optional_enum() -> None:
    assert AgentContainerIn(**_container()).health is None
    assert AgentContainerIn(**_container(health="HEALTHY")).health.value == "HEALTHY"
    with pytest.raises(ValidationError):
        AgentContainerIn(**_container(health="PERFECT"))


# --- hello -------------------------------------------------------------------------


def test_agent_hello_minimal() -> None:
    hello = AgentHelloIn(agent_version="1.4.2", hostname="edge01")
    assert hello.cpu_cores == 0
    assert hello.memory_total_mb == 0
    assert hello.os_name == ""


def test_agent_hello_bounds() -> None:
    with pytest.raises(ValidationError):
        AgentHelloIn(agent_version="", hostname="h")
    with pytest.raises(ValidationError):
        AgentHelloIn(agent_version="1.0", hostname="")
    with pytest.raises(ValidationError):
        AgentHelloIn(agent_version="1.0", hostname="h", cpu_cores=4097)


def test_v1_hello_defaults_to_protocol_one_with_no_capabilities() -> None:
    """An absent protocol version is the oldest contract, never v2."""
    hello = AgentHelloIn(agent_version="1.0.0", hostname="legacy")
    assert hello.protocol_version == 1
    assert hello.capabilities == {}
    assert hello.facts == {}


def test_v2_hello_carries_capabilities_and_facts() -> None:
    hello = AgentHelloIn(
        agent_version="1.1.0",
        hostname="edge",
        protocol_version=2,
        capabilities={
            "docker": {"present": True, "api_version": "1.43"},
            "nginx": {"present": False},
        },
        facts={"disks": [{"mount": "/", "free_gb": 42}], "kernel": "6.8.0"},
    )
    assert hello.capabilities["docker"].present is True
    assert hello.capabilities["docker"].api_version == "1.43"
    assert hello.capabilities["nginx"].present is False
    assert hello.facts["kernel"] == "6.8.0"


def test_unknown_capability_extra_field_is_rejected() -> None:
    """A capability report forbids unknown keys, so its shape is closed."""
    with pytest.raises(ValidationError):
        AgentHelloIn(
            agent_version="1.1.0",
            hostname="edge",
            protocol_version=2,
            capabilities={"docker": {"present": True, "secret": "x"}},
        )


def test_capability_map_is_bounded() -> None:
    too_many = {f"cap{i}": {"present": True} for i in range(17)}
    with pytest.raises(ValidationError):
        AgentHelloIn(
            agent_version="1.1.0", hostname="edge", protocol_version=2, capabilities=too_many
        )


def test_overlarge_facts_blob_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentHelloIn(
            agent_version="1.1.0",
            hostname="edge",
            protocol_version=2,
            facts={"blob": "x" * 9000},
        )
