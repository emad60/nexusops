"""Unit tests for the simulated docker provider (in-memory rows, no docker)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.models import Container, LogEntry
from app.models.enums import ContainerHealth, ContainerStatus, LogLevel, LogSource
from app.providers.base import DockerProviderError
from app.providers.docker_sim import SimulatedDockerProvider, _seed_int


def _row(
    cid: str = "abc123def456",
    name: str = "web-1",
    status: ContainerStatus = ContainerStatus.RUNNING,
    **overrides: object,
) -> Container:
    fields: dict[str, object] = {
        "docker_host_id": uuid4(),
        "container_id": cid,
        "name": name,
        "image_ref": "nginx:1.27",
        "command": "nginx -g 'daemon off;'",
        "status": status,
        "health": ContainerHealth.HEALTHY,
        "mem_limit_mb": 1024.0,
        "restart_count": 0,
        "observed_at": datetime.now(UTC),
    }
    fields.update(overrides)
    return Container(**fields)


def _log_entry(i: int, ts: datetime, message: str) -> LogEntry:
    return LogEntry(
        id=i,
        source=LogSource.CONTAINER,
        stream="stdout",
        level=LogLevel.INFO,
        message=message,
        ts=ts,
    )


# --- seeded determinism -----------------------------------------------------------------


def test_seed_int_is_deterministic_and_spread() -> None:
    assert _seed_int("host-a", "images") == _seed_int("host-a", "images")
    assert _seed_int("host-a") != _seed_int("host-b")


def test_listings_are_identical_for_same_seed() -> None:
    a = SimulatedDockerProvider("seed-host-1")
    b = SimulatedDockerProvider("seed-host-1")
    assert a.images() == b.images()
    assert a.volumes() == b.volumes()
    assert a.networks() == b.networks()
    # And repeated calls on one instance stay stable too.
    assert a.images() == a.images()


def test_different_seeds_produce_different_fleets() -> None:
    a = SimulatedDockerProvider("sim-alpha").images()
    b = SimulatedDockerProvider("sim-beta").images()
    assert a != b


def test_image_listing_shape_and_bounds() -> None:
    images = SimulatedDockerProvider("shape-host").images()
    assert 4 <= len(images) <= 8
    for image in images:
        assert image["id"].startswith("sha256:")
        assert len(image["repo_tags"]) == 1
        assert image["repo_tags"][0].startswith("nexus/")
        assert ":" in image["repo_tags"][0]
        assert image["architecture"] in {"amd64", "arm64"}
        assert image["size_bytes"] > 0


def test_network_listing_includes_docker_defaults() -> None:
    networks = SimulatedDockerProvider("net-host").networks()
    names = {n["name"] for n in networks}
    assert {"bridge", "host", "none"} <= names
    assert all(n["driver"] for n in networks)


# --- lifecycle mutations -------------------------------------------------------------------


def test_start_stop_restart_pause_transitions() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    row = _row(status=ContainerStatus.CREATED)
    provider.register_container(row)

    provider.start(row.container_id)
    assert row.status == "RUNNING" and row.started_at is not None

    provider.pause(row.container_id)
    assert row.status == "PAUSED"

    provider.unpause(row.container_id)
    assert row.status == "RUNNING"

    provider.stop(row.container_id)
    assert row.status == "EXITED" and row.finished_at is not None

    provider.restart(row.container_id)
    assert row.status == "RUNNING"
    assert row.restart_count == 1


def test_remove_running_requires_force() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    row = _row()
    provider.register_container(row)
    with pytest.raises(DockerProviderError):
        provider.remove(row.container_id)
    provider.remove(row.container_id, force=True)
    assert row.status == "REMOVED"


def test_inspect_maps_row_fields_to_info() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    row = _row(name="api-7", labels={"tier": "backend"})
    provider.register_container(row)
    info = provider.inspect(row.container_id)
    assert info.id == row.container_id
    assert info.name == "api-7"
    assert info.status == "running"
    assert info.health == "healthy"
    assert info.labels == {"tier": "backend"}


def test_prefix_resolution_unique_ok_ambiguous_error() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    row = _row(cid="abcdef1234567890")
    provider.register_container(row)
    assert provider.inspect("abcdef123").id == row.container_id
    with pytest.raises(DockerProviderError):
        provider.inspect("doesnotexist")

    ambiguous = SimulatedDockerProvider(str(uuid4()))
    ambiguous.register_containers([_row(cid="aaa111"), _row(cid="aaa222", name="other")])
    with pytest.raises(DockerProviderError):
        ambiguous.inspect("aaa")


def test_list_containers_filters_stopped() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    running = _row(cid="r1", name="up")
    exited = _row(cid="e1", name="down", status=ContainerStatus.EXITED)
    provider.register_containers([running, exited])
    assert {c.id for c in provider.list_containers()} == {"r1", "e1"}
    assert [c.id for c in provider.list_containers(include_stopped=False)] == ["r1"]


def test_ping_is_true() -> None:
    assert SimulatedDockerProvider(str(uuid4())).ping() is True


# --- stats ------------------------------------------------------------------------------------


def test_running_stats_within_plausible_bounds() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    row = _row(mem_limit_mb=1024.0)
    provider.register_container(row)
    stats = provider.stats(row.container_id)
    assert stats.mem_limit_mb == 1024.0
    assert 0.0 <= stats.cpu_percent <= 11.5
    assert 0.0 < stats.mem_used_mb <= 1024.0 * 0.95 + 0.01
    assert stats.net_rx_kb_s >= 0.0 and stats.net_tx_kb_s >= 0.0


def test_stopped_container_reports_no_cpu_or_traffic() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    row = _row(status=ContainerStatus.EXITED)
    provider.register_container(row)
    stats = provider.stats(row.container_id)
    assert stats.cpu_percent == 0.0
    assert stats.net_rx_kb_s == 0.0
    assert stats.net_tx_kb_s == 0.0


def test_stats_mem_limit_defaults_when_row_has_none() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    row = _row(mem_limit_mb=None)
    provider.register_container(row)
    assert provider.stats(row.container_id).mem_limit_mb == 512.0


# --- log replay ----------------------------------------------------------------------------------


def test_logs_replay_sorted_by_ts_then_id() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    base = datetime(2026, 8, 24, tzinfo=UTC)
    rows = [
        _log_entry(2, base, "second"),
        _log_entry(1, base, "first-same-ts"),
        _log_entry(3, datetime(2026, 8, 25, tzinfo=UTC), "third"),
    ]
    provider.register_log_rows("abc123", rows)
    lines = list(provider.logs("abc123"))
    assert [line.message for line in lines] == ["first-same-ts", "second", "third"]
    assert all(line.stream == "stdout" for line in lines)


def test_logs_tail_keeps_last_n() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    base = datetime(2026, 8, 24, tzinfo=UTC)
    provider.register_log_rows(
        "abc123", [_log_entry(i, base.replace(second=i), f"line-{i}") for i in range(10)]
    )
    lines = list(provider.logs("abc123", tail=3))
    assert [line.message for line in lines] == ["line-7", "line-8", "line-9"]


def test_logs_since_filter_treats_naive_as_utc() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    base = datetime(2026, 8, 24, tzinfo=UTC)
    provider.register_log_rows(
        "abc123",
        [
            _log_entry(1, base.replace(hour=1), "early"),
            _log_entry(2, base.replace(hour=12), "late"),
        ],
    )
    since = datetime(2026, 8, 24, 6, tzinfo=UTC)
    assert [line.message for line in provider.logs("abc123", since=since)] == ["late"]
    naive = since.replace(tzinfo=None)
    assert [line.message for line in provider.logs("abc123", since=naive)] == ["late"]


def test_logs_for_unknown_container_are_empty() -> None:
    provider = SimulatedDockerProvider(str(uuid4()))
    assert list(provider.logs("nope")) == []
