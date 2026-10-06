"""Agent auth-failure backoff: a rejected token must never hot-loop the process.

Regression: the agent returned exit status 1 on any 401, and the shipped
systemd unit runs with ``Restart=always`` / ``RestartSec=10`` — so every
revoked or rotated-away token produced an endless storm of rejected requests
instead of a quiet node (docs/node-agent-architecture.md §3.4;
docs/platform-security-model.md H4). The agent now parks in a long, bounded
re-attempt cadence and says so once.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_AGENT_PATH = _REPO_ROOT / "agent" / "nexusops_agent.py"


def _load_agent() -> Any:
    spec = importlib.util.spec_from_file_location("nexusops_agent_backoff_under_test", _AGENT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="agent")
def agent_fixture() -> Any:
    return _load_agent()


def _patch_host(agent: Any, monkeypatch: pytest.MonkeyPatch, request_fn: Any) -> None:
    """Stub the network client and the /proc-backed collectors."""

    class FakeClient:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None: ...

        request = staticmethod(request_fn)

    monkeypatch.setattr(agent, "AgentClient", FakeClient)
    monkeypatch.setattr(agent, "os_info", lambda: ("Debian GNU/Linux", "12"))
    monkeypatch.setattr(agent, "memory_total_mb", lambda: 2048)
    # Heartbeats would read /proc and the docker socket; the loop logic under
    # test does not care what the payload contains.
    monkeypatch.setattr(agent, "build_heartbeat", lambda prev, prev_cpu=None: ({}, None, {}))


def _install_sleep(agent: Any, monkeypatch: pytest.MonkeyPatch, slept: list[float]) -> None:
    """Record the park duration and request shutdown after the first one."""

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        agent._STOP["flag"] = True

    monkeypatch.setattr(agent, "_interruptible_sleep", fake_sleep)


def test_heartbeat_401_parks_instead_of_exiting(
    agent: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[str] = []

    def request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        calls.append(path)
        if path.endswith("/agent/hello"):
            return 200, {"name": "node-1", "heartbeat_interval_seconds": 30}
        return 401, {"error": {"code": "AGENT_TOKEN_REVOKED"}}

    _patch_host(agent, monkeypatch, request)
    slept: list[float] = []
    _install_sleep(agent, monkeypatch, slept)

    exit_code = agent.main(["--server", "https://cp.example.com", "--token", "nxa_dead"])

    assert exit_code == 0, "a rejected token must not terminate the process"
    assert slept == [agent.REVOKED_POLL_SECONDS]
    assert agent.REVOKED_POLL_SECONDS >= 600, "the park cadence must be long enough to matter"
    # hello + exactly one rejected heartbeat: no tight loop.
    assert calls == ["/agent/hello", "/agent/heartbeat"]

    stderr = capsys.readouterr().err
    assert "revoked or was rotated away" in stderr
    # The old behavior said "token rejected by server; exiting" and returned 1.
    assert "token rejected by server; exiting" not in stderr


def test_hello_401_parks_instead_of_exiting(
    agent: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[str] = []

    def request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        calls.append(path)
        return 401, {"error": {"code": "AGENT_TOKEN_UNKNOWN"}}

    _patch_host(agent, monkeypatch, request)
    slept: list[float] = []
    _install_sleep(agent, monkeypatch, slept)

    assert agent.main(["--server", "https://cp.example.com", "--token", "nxa_dead"]) == 0

    assert slept == [agent.REVOKED_POLL_SECONDS]
    assert calls == ["/agent/hello"]
    stderr = capsys.readouterr().err
    # Logged once per state entry, not once per attempt.
    assert stderr.count("revoked or was rotated away") == 1


def test_revoked_notice_is_logged_only_once(
    agent: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two consecutive parks must not re-print the notice each cycle."""

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        if len(slept) == 2:
            agent._STOP["flag"] = True

    def request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        return 401, {"error": {"code": "AGENT_TOKEN_REVOKED"}}

    _patch_host(agent, monkeypatch, request)
    slept: list[float] = []
    monkeypatch.setattr(agent, "_interruptible_sleep", fake_sleep)

    assert agent.main(["--server", "https://cp.example.com", "--token", "nxa_dead"]) == 0

    assert slept == [agent.REVOKED_POLL_SECONDS, agent.REVOKED_POLL_SECONDS]
    stderr = capsys.readouterr().err
    assert stderr.count("revoked or was rotated away") == 1


@pytest.mark.parametrize("path_401", ["/agent/hello", "/agent/heartbeat"])
def test_once_mode_still_reports_a_rejected_token(
    agent: Any, monkeypatch: pytest.MonkeyPatch, path_401: str
) -> None:
    """``--once`` is a smoke test: it must fail loudly, not park."""

    def request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        if path == path_401:
            return 401, {"error": {"code": "AGENT_TOKEN_REVOKED"}}
        return 200, {"name": "node-1", "heartbeat_interval_seconds": 30}

    _patch_host(agent, monkeypatch, request)
    slept: list[float] = []
    _install_sleep(agent, monkeypatch, slept)

    assert agent.main(["--server", "https://cp.example.com", "--token", "nxa_dead", "--once"]) == 1
    assert slept == []
