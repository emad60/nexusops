"""Contract tests: the shipped agent's payloads must satisfy the ingest schemas.

The agent (`agent/nexusops_agent.py`) and the backend schemas
(`app/schemas/agent.py`) live in different runtimes and are versioned
together in this repo, but nothing stopped them from drifting — the agent
once sent `health: ""` and an undocumented `ports` key, and every heartbeat
was 422'd while hello still worked, so enrollment looked fine. These tests
import the real agent module and validate what it builds against the real
schemas, so drift fails CI instead of production.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
from app.models.enums import ContainerHealth
from app.schemas.agent import AgentContainerIn, AgentHeartbeatIn

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AGENT_PATH = _REPO_ROOT / "agent" / "nexusops_agent.py"


def _load_agent() -> Any:
    spec = importlib.util.spec_from_file_location("nexusops_agent_under_test", _AGENT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="agent")
def agent_fixture() -> Any:
    return _load_agent()


def _patch_stats(monkeypatch: pytest.MonkeyPatch, agent: Any) -> None:
    """Pin the host-stat collectors to deterministic values (no /proc, no os)."""
    monkeypatch.setattr(agent, "read_cpu_times", lambda: (100, 10))
    monkeypatch.setattr(agent, "memory_stats", lambda: (2048.0, 25.0))
    monkeypatch.setattr(agent, "disk_stats", lambda: (40.0, 50.0))
    monkeypatch.setattr(agent, "load1", lambda: 0.5)
    monkeypatch.setattr(agent, "uptime_seconds", lambda: 86400)


def test_build_heartbeat_matches_schema(agent: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_stats(monkeypatch, agent)
    monkeypatch.setattr(agent, "collect_containers", lambda max_inspect=10: [])

    payload, prev_cpu, _prev_container_cpu = agent.build_heartbeat(None)

    assert prev_cpu == (100, 10)
    # extra="forbid" on the schema makes this reject any key the agent adds
    # that the platform does not know about.
    AgentHeartbeatIn(**payload)


def test_build_heartbeat_containers_match_schema(
    agent: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Representative entries shaped exactly like the docker /containers/json
    view the collector derives from — including the no-healthcheck case."""
    _patch_stats(monkeypatch, agent)
    monkeypatch.setattr(
        agent,
        "collect_containers",
        lambda max_inspect=10: [
            {
                "container_id": "a" * 64,
                "name": "nexusops-api-1",
                "status": "RUNNING",
                "health": "HEALTHY",
                "image_ref": "nexusops-api:latest",
                "restart_count": 0,
            },
            {
                "container_id": "b" * 64,
                "name": "worker",
                "status": "EXITED",
                "health": None,
                "image_ref": "nexusops-api:latest",
                "restart_count": 2,
            },
        ],
    )

    payload, _cpu, _container_cpu = agent.build_heartbeat((100, 10))

    parsed = AgentHeartbeatIn(**payload)
    assert [c.status for c in parsed.containers] == ["RUNNING", "EXITED"]
    assert parsed.containers[0].health == ContainerHealth.HEALTHY
    assert parsed.containers[1].health is None


def test_collect_container_stats_matches_schema(
    agent: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One-shot docker stats reduce to cpu/mem/limit fields the schema accepts,
    with CPU appearing only from the second cycle (no prior sample to diff)."""
    sample: dict[str, Any] = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 2_000_000},
            "system_cpu_usage": 10_000_000_000,
            "online_cpus": 2,
        },
        "memory_stats": {
            "usage": 300_000_000,
            "limit": 8_000_000_000,
            "stats": {"inactive_file": 50_000_000},
        },
    }

    def fake_stats(method: str, path: str, timeout: float = 5.0) -> tuple[int, Any]:
        if "stats" in path:
            return 200, sample
        raise AssertionError(f"unexpected request {method} {path}")

    monkeypatch.setattr(agent, "_docker_request", fake_stats)
    cid = "e" * 64

    updates, prev = agent.collect_container_stats([cid], {})

    # First sighting: memory present, CPU absent (nothing to diff against).
    assert "cpu_percent" not in updates[cid]
    assert updates[cid]["mem_used_mb"] > 0
    assert updates[cid]["mem_limit_mb"] > 0
    AgentContainerIn(container_id=cid, name="x", status="RUNNING", **updates[cid])

    # Second cycle with both counters advanced: a real percentage comes out.
    sample["cpu_stats"]["cpu_usage"]["total_usage"] = 3_000_000
    sample["cpu_stats"]["system_cpu_usage"] = 11_000_000_000
    updates2, _ = agent.collect_container_stats([cid], prev)
    assert updates2[cid]["cpu_percent"] is not None
    assert 0 < updates2[cid]["cpu_percent"] <= 200  # 2 online cpus → ≤ 200%
    AgentContainerIn(container_id=cid, name="x", status="RUNNING", **updates2[cid])


def test_collect_containers_shape_matches_schema(
    agent: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The collector's output against a canned docker API response — this is
    where the undocumented `ports` key and the empty-string health used to
    leak into the wire payload."""
    canned_list = [
        {
            "Id": "c" * 64,
            "Names": ["/nexusops-nginx-1"],
            "State": "running",
            "Status": "Up 3 hours (healthy)",
            "Image": "nginx:1.27",
            "Ports": [
                {"PrivatePort": 80, "PublicPort": 8080, "Type": "tcp"},
                {"PrivatePort": 443, "Type": "tcp"},  # not published
            ],
        },
        {
            "Id": "d" * 64,
            "Names": ["/mailer"],
            "State": "running",
            "Status": "Up 3 hours",  # no healthcheck at all
            "Image": "axllent/mailpit",
            "Ports": [],
        },
    ]

    def fake_docker_request(method: str, path: str) -> tuple[int, Any]:
        if path.startswith("/containers/json"):
            return 200, canned_list
        if path.startswith("/containers/"):
            # Only the first container has a healthcheck; "mailer" reports none.
            data: dict[str, Any] = {"RestartCount": 1}
            if "cccc" in path:
                data["State"] = {"Health": {"Status": "healthy"}}
            return 200, data
        raise AssertionError(f"unexpected request {method} {path}")

    monkeypatch.setattr(agent, "_docker_request", fake_docker_request)

    entries = agent.collect_containers()

    assert len(entries) == 2
    for entry in entries:
        # Rejects both the stale "" health and any extra key like `ports`.
        AgentContainerIn(**entry)
    published = [e for e in entries if e["container_id"].startswith("c")]
    assert published[0]["restart_count"] == 1
    assert published[0]["health"] == "HEALTHY"
    no_health = next(e for e in entries if e["container_id"].startswith("d"))
    assert no_health["health"] is None
