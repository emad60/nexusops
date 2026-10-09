"""Agent protocol v2: honest metrics, capability detection, and the executor.

The agent is loaded from source (like ``test_agent_contract.py``) so these tests
pin the shipped file rather than a copy. They answer four questions:

* Do the network rates report ``None`` when they are not measurable, instead of a
  fabricated zero?
* Does Docker capability detection talk to the daemon rather than trust a path?
* Is the operation executor a closed, validating registry — no shell, no
  arbitrary type, bounded output?
* Is the transport HTTPS-only, with certificate verification never disabled?
"""

from __future__ import annotations

import importlib.util
import os
import stat
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_AGENT_PATH = _REPO_ROOT / "agent" / "nexusops_agent.py"


def _load_agent() -> Any:
    spec = importlib.util.spec_from_file_location("nexusops_agent_v2_under_test", _AGENT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="agent")
def agent_fixture() -> Any:
    return _load_agent()


# --- honest metrics -----------------------------------------------------------


def test_first_network_sample_is_unavailable_not_zero(agent: Any, monkeypatch) -> None:
    agent._NET_STATE.clear()
    monkeypatch.setattr(agent, "network_total_bytes", lambda: (1000, 500, 1))
    assert agent.network_rates() == (None, None)


def test_network_rates_diff_counters(agent: Any, monkeypatch) -> None:
    agent._NET_STATE.clear()
    readings = iter([(0, 0, 1), (1024 * 1024, 512 * 1024, 1)])
    monkeypatch.setattr(agent, "network_total_bytes", lambda: next(readings))
    monkeypatch.setattr(agent.time, "monotonic", lambda: 0.0)
    agent.network_rates()
    monkeypatch.setattr(agent.time, "monotonic", lambda: 10.0)
    rx, tx = agent.network_rates()
    # 1 MiB over 10s ≈ 102.4 KiB/s.
    assert rx == pytest.approx(102.4, rel=0.01)
    assert tx == pytest.approx(51.2, rel=0.01)


def test_network_counter_reset_is_unavailable(agent: Any, monkeypatch) -> None:
    agent._NET_STATE.clear()
    readings = iter([(5_000, 5_000, 1), (10, 10, 1)])
    monkeypatch.setattr(agent, "network_total_bytes", lambda: next(readings))
    agent.network_rates()
    # A counter that went backwards is a reset, not a negative rate.
    assert agent.network_rates() == (None, None)


def test_missing_proc_net_dev_is_unavailable(agent: Any, monkeypatch) -> None:
    def boom() -> tuple[int, int, int]:
        raise OSError("no /proc/net/dev")

    monkeypatch.setattr(agent, "network_total_bytes", boom)
    assert agent.network_rates() == (None, None)


def test_heartbeat_payload_uses_null_for_unmeasured_rates(agent: Any, monkeypatch) -> None:
    monkeypatch.setattr(agent, "read_cpu_times", lambda: (100, 10))
    monkeypatch.setattr(agent, "memory_stats", lambda: (1.0, 1.0))
    monkeypatch.setattr(agent, "disk_stats", lambda: (1.0, 1.0))
    monkeypatch.setattr(agent, "load1", lambda: 0.0)
    monkeypatch.setattr(agent, "uptime_seconds", lambda: 0)
    monkeypatch.setattr(agent, "collect_containers", lambda max_inspect=10: [])
    monkeypatch.setattr(agent, "network_rates", lambda: (None, None))

    payload, _cpu, _prev = agent.build_heartbeat(None)
    assert payload["net_rx_kb_s"] is None
    assert payload["net_tx_kb_s"] is None


# --- docker capability --------------------------------------------------------


def test_no_socket_means_no_docker_capability(agent: Any, monkeypatch) -> None:
    monkeypatch.setattr(agent, "_docker_socket", lambda: None)
    assert agent.docker_capability() == {"present": False}


def test_docker_present_only_when_version_answers(agent: Any, monkeypatch) -> None:
    monkeypatch.setattr(agent, "_docker_socket", lambda: "/run/docker.sock")

    def fake(method: str, path: str, timeout: float = 5.0) -> tuple[int, Any]:
        if path == "/version":
            return 200, {"ApiVersion": "1.43", "Version": "27.0"}
        raise AssertionError(path)

    monkeypatch.setattr(agent, "_docker_request", fake)
    report = agent.docker_capability()
    assert report["present"] is True
    assert report["api_version"] == "1.43"


def test_docker_daemon_failure_is_not_reported_as_present(agent: Any, monkeypatch) -> None:
    monkeypatch.setattr(agent, "_docker_socket", lambda: "/run/docker.sock")

    def denied(method: str, path: str, timeout: float = 5.0) -> tuple[int, Any]:
        raise OSError("permission denied")

    monkeypatch.setattr(agent, "_docker_request", denied)
    assert agent.docker_capability() == {"present": False}


# --- executor: closed registry and validation ---------------------------------


def test_unknown_operation_type_is_refused(agent: Any) -> None:
    ok, _output, code, _message = agent.execute_operation(
        "node.execute", {"cmd": "id"}, deadline=None, capabilities={"docker": {"present": True}}
    )
    assert ok is False
    assert code == "OPERATION_UNSUPPORTED"


def test_reserved_phase4_types_are_not_in_the_local_registry(agent: Any) -> None:
    for reserved in ("nginx.apply", "secret.env.apply", "certificate.install"):
        assert reserved not in agent.OPERATION_REGISTRY


def test_missing_local_capability_refuses_before_running(agent: Any) -> None:
    ok, _output, code, _message = agent.execute_operation(
        "container.start", {"container_id": "abc123"}, deadline=None, capabilities={}
    )
    assert ok is False
    assert code == "CAPABILITY_MISSING"


@pytest.mark.parametrize(
    "params",
    [
        {"container_id": "has space"},
        {"container_id": ""},
        {"container_id": "x" * 73},
        {"container_id": "abc", "command": "rm -rf /"},
    ],
)
def test_invalid_container_params_are_refused(agent: Any, params: dict) -> None:
    ok, _output, code, _message = agent.execute_operation(
        "container.start", params, deadline=None, capabilities={"docker": {"present": True}}
    )
    assert ok is False
    assert code == "INVALID_PARAMS"


def test_logs_tail_bounds_are_enforced(agent: Any) -> None:
    capabilities = {"docker": {"present": True}}
    for bad in (0, 9999, "10", True):
        ok, _out, code, _msg = agent.execute_operation(
            "logs.tail",
            {"container_id": "abc123", "tail": bad},
            deadline=None,
            capabilities=capabilities,
        )
        assert ok is False and code == "INVALID_PARAMS", bad


def test_expired_deadline_reports_a_timeout_without_running(agent: Any, monkeypatch) -> None:
    def must_not_run(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("docker must not be called past the deadline")

    monkeypatch.setattr(agent, "_docker_raw", must_not_run)
    ok, _out, code, _msg = agent.execute_operation(
        "container.start",
        {"container_id": "abc123"},
        deadline=agent.time.time() - 5,
        capabilities={"docker": {"present": True}},
    )
    assert ok is False
    assert code == "OPERATION_TIMEOUT"


def test_container_start_maps_to_a_fixed_api_call(agent: Any, monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_raw(method: str, path: str, timeout: float = 5.0) -> tuple[int, bytes]:
        calls.append((method, path))
        return 204, b""

    monkeypatch.setattr(agent, "_docker_raw", fake_raw)
    monkeypatch.setattr(agent, "_container_status", lambda cid: "RUNNING")

    ok, output, code, _msg = agent.execute_operation(
        "container.start",
        {"container_id": "abc123def456"},
        deadline=None,
        capabilities={"docker": {"present": True}},
    )
    assert ok is True and code is None
    assert calls == [("POST", "/containers/abc123def456/start")]
    assert output["status"] == "RUNNING"


def test_remove_honours_force_and_never_shells(agent: Any, monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_raw(method: str, path: str, timeout: float = 5.0) -> tuple[int, bytes]:
        calls.append((method, path))
        return 204, b""

    monkeypatch.setattr(agent, "_docker_raw", fake_raw)
    ok, output, code, _msg = agent.execute_operation(
        "container.remove",
        {"container_id": "abc123", "force": True},
        deadline=None,
        capabilities={"docker": {"present": True}},
    )
    assert ok is True and code is None
    assert calls == [("DELETE", "/containers/abc123?force=1&v=0")]
    assert output["force"] is True


def test_docker_404_becomes_a_stable_sanitized_error(agent: Any, monkeypatch) -> None:
    monkeypatch.setattr(
        agent, "_docker_raw", lambda *a, **k: (404, b"<html>raw daemon body</html>")
    )
    ok, _output, code, message = agent.execute_operation(
        "container.stop",
        {"container_id": "abc123"},
        deadline=None,
        capabilities={"docker": {"present": True}},
    )
    assert ok is False
    assert code == "CONTAINER_NOT_FOUND"
    assert "raw daemon body" not in (message or "")


def test_logs_are_demuxed_bounded_and_sanitized(agent: Any, monkeypatch) -> None:
    def frame(payload: bytes, stream: int = 1) -> bytes:
        return bytes([stream, 0, 0, 0]) + len(payload).to_bytes(4, "big") + payload

    body = frame(b"line one\n") + frame(b"line two\n") + frame(b"\x00\x01bad\x02")

    monkeypatch.setattr(agent, "_docker_raw", lambda *a, **k: (200, body))
    ok, output, code, _msg = agent.execute_operation(
        "logs.tail",
        {"container_id": "abc123", "tail": 2},
        deadline=None,
        capabilities={"docker": {"present": True}},
    )
    assert ok is True and code is None
    assert output["lines"] <= 2
    # Control characters are scrubbed, not delivered verbatim.
    assert "\x02" not in output["log"]


def test_logs_output_is_size_bounded(agent: Any, monkeypatch) -> None:
    monkeypatch.setattr(agent, "_docker_raw", lambda *a, **k: (200, b"A" * 500_000))
    ok, output, _code, _msg = agent.execute_operation(
        "logs.tail",
        {"container_id": "abc123", "tail": 500},
        deadline=None,
        capabilities={"docker": {"present": True}},
    )
    assert ok is True
    assert len(output["log"].encode()) <= agent.LOGS_MAX_BYTES + 32


# --- transport ----------------------------------------------------------------


#: Every non-loopback destination that must be refused over plain HTTP. This
#: includes link-local, which is deliberately *not* exempt: the credential can
#: reach another host on that segment just as easily as any LAN peer.
_NON_LOOPBACK_PLAIN_HTTP = [
    "http://control-plane.example.com",  # ordinary DNS name
    "http://localhost.evil.example",  # a name that merely starts with localhost
    "http://10.0.0.5:8080",  # private LAN (RFC 1918)
    "http://192.168.1.10",  # private LAN
    "http://172.16.0.1",  # private LAN
    "http://169.254.169.254",  # IPv4 link-local (cloud metadata)
    "http://[fe80::1]:8080",  # IPv6 link-local
    "http://[fd00::1]",  # IPv6 ULA
    "http://8.8.8.8",  # public IPv4
    "http://[2001:4860:4860::8888]",  # public IPv6
    "http://0.0.0.0",  # unspecified address is not loopback
]

#: Genuine loopback only, where the credential cannot leave the host.
_LOOPBACK_PLAIN_HTTP = [
    "http://127.0.0.1:8000",
    "http://127.5.5.5",  # the whole 127.0.0.0/8 range is loopback
    "http://localhost",
    "http://localhost:8000/api",
    "http://[::1]",
    "http://[::1]:8000",
    "http://[::ffff:127.0.0.1]:8000",  # IPv4-mapped loopback
]


@pytest.mark.parametrize("url", _NON_LOOPBACK_PLAIN_HTTP)
def test_plain_http_to_a_non_loopback_host_is_refused(agent: Any, url: str) -> None:
    with pytest.raises(ValueError, match="plain HTTP"):
        agent.AgentClient(url, "nxa_test")


@pytest.mark.parametrize("url", _LOOPBACK_PLAIN_HTTP)
def test_plain_http_is_allowed_only_for_genuine_loopback(agent: Any, url: str) -> None:
    client = agent.AgentClient(url, "nxa_test")
    assert client.use_tls is False


def test_https_uses_a_verifying_context(agent: Any) -> None:
    client = agent.AgentClient("https://control-plane.example.com", "nxa_test")
    assert client.use_tls is True
    assert client._ctx is not None
    # A default context verifies certificates; check_verify would be False only
    # for the insecure context this agent must never build.
    assert client._ctx.verify_mode.name == "CERT_REQUIRED"
    assert client._ctx.check_hostname is True


def test_https_with_a_private_ca_still_verifies(agent: Any) -> None:
    """Trusting a private CA must not weaken verification."""
    import certifi

    client = agent.AgentClient(
        "https://control-plane.internal", "nxa_test", ca_bundle=certifi.where()
    )
    assert client.use_tls is True
    assert client._ctx is not None
    assert client._ctx.verify_mode.name == "CERT_REQUIRED"
    assert client._ctx.check_hostname is True
    # The bundle is genuinely loaded (a non-empty trust store), not bypassed.
    assert client._ctx.get_ca_certs()


def test_a_missing_private_ca_bundle_fails_closed(agent: Any, tmp_path: Path) -> None:
    """An unloadable CA file must error, never silently fall back to no verify."""
    with pytest.raises(OSError):
        agent.AgentClient(
            "https://control-plane.internal",
            "nxa_test",
            ca_bundle=str(tmp_path / "does-not-exist.pem"),
        )


def test_a_refused_transport_sends_no_credential(
    agent: Any, monkeypatch: Any, tmp_path: Path, capsys: Any
) -> None:
    """A link-local URL over plain HTTP must fail before any request or write."""
    sent: list[Any] = []
    original = agent.AgentClient.request

    def spy(self: Any, *args: Any, **kwargs: Any) -> Any:
        sent.append((args, kwargs))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(agent.AgentClient, "request", spy)
    token_file = str(tmp_path / "token")

    code = agent.main(
        [
            "--server",
            "http://169.254.169.254",
            "--token",
            "nxk_super_secret",
            "--token-file",
            token_file,
        ]
    )

    assert code != 0, "a refused transport must exit non-zero"
    assert sent == [], "no request (enrollment or heartbeat) may be attempted"
    assert not Path(token_file).exists(), "no credential may be persisted"
    err = capsys.readouterr().err
    assert "refusing to start" in err
    assert "nxk_super_secret" not in err, "the credential must never be echoed"


def test_the_insecure_transport_flag_is_gone(agent: Any, monkeypatch: Any) -> None:
    """No CLI switch may disable TLS verification."""
    with pytest.raises(SystemExit):
        agent.main(["--server", "https://cp.example.com", "--token", "nxa_x", "--insecure"])


# --- credential persistence ---------------------------------------------------


def test_token_persistence_is_owner_only_and_atomic(agent: Any, tmp_path: Path) -> None:
    path = str(tmp_path / "nexusops-agent" / "token")
    assert agent.persist_token(path, "nxa_secret_value") is True
    assert agent.read_token_file(path) == "nxa_secret_value"
    mode = stat.S_IMODE(os.stat(path).st_mode)
    assert mode == 0o600, oct(mode)
    # No temp file is left behind.
    assert [p.name for p in Path(path).parent.iterdir()] == ["token"]


def test_rotation_persist_keeps_old_credential_on_failure(
    agent: Any, tmp_path: Path, monkeypatch
) -> None:
    path = str(tmp_path / "token")
    assert agent.persist_token(path, "nxa_old") is True

    def fail_replace(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(agent.os, "replace", fail_replace)
    assert agent.persist_token(path, "nxa_new") is False
    # The previous credential is intact and readable.
    assert agent.read_token_file(path) == "nxa_old"
    assert not any(p.name.startswith(".token.") for p in tmp_path.iterdir())
