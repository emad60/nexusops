"""Phase 4 agent contract: nginx capability, port reporting, and bundle validation.

The agent must agree with the control plane on two things that would otherwise
drift silently:

* the **bundle fingerprint algorithm** — if the two implementations disagree, the
  agent either refuses every valid bundle or applies a tampered one;
* the **capability report shape** — ``extra="forbid"`` means one unexpected key
  turns every hello into a 422, which is how the original ``ports`` bug shipped.

Everything here imports the real agent module and the real schemas, so a change
on either side fails in CI rather than on a customer's node.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
from app.schemas.agent import AgentContainerIn, AgentHelloIn, CapabilityReport
from app.schemas.proxy import (
    MANAGED_CONF_PATH,
    ROUTES_DIR,
    BundleFile,
    fingerprint_files,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AGENT_PATH = _REPO_ROOT / "agent" / "nexusops_agent.py"


def _load_agent() -> Any:
    spec = importlib.util.spec_from_file_location("nexusops_agent_phase4", _AGENT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="agent")
def agent_fixture() -> Any:
    return _load_agent()


# --- capability reporting ------------------------------------------------------


def test_capability_report_shape_is_accepted(agent: Any, tmp_path: Path, monkeypatch) -> None:
    """Whatever the pre-flight returns must satisfy the hello schema."""
    monkeypatch.setattr(agent, "_nginx_binary", lambda: None)
    report = agent.nginx_capability()
    parsed = CapabilityReport(**report)
    assert parsed.present is False
    assert parsed.routing_eligible is False
    assert parsed.reason

    # And the whole hello payload (docker + systemd + nginx) validates.
    monkeypatch.setattr(agent, "docker_capability", lambda: {"present": True, "version": "27.0"})
    payload = {"agent_version": agent.AGENT_VERSION, "hostname": "node-1"}
    payload["capabilities"] = agent.build_capabilities()
    AgentHelloIn(**payload)


def test_preflight_does_not_claim_eligibility_from_installation_alone(
    agent: Any, monkeypatch
) -> None:
    """nginx installed but not running is *not* an eligible node."""
    monkeypatch.setattr(agent, "_nginx_binary", lambda: "/usr/sbin/nginx")
    monkeypatch.setattr(agent, "_nginx_version", lambda binary: "1.27.5")
    monkeypatch.setattr(agent, "_nginx_running", lambda: False)
    monkeypatch.setattr(agent, "_nginx_config_test", lambda binary, conf=None: (True, ""))
    monkeypatch.setattr(agent, "_listening_ports", lambda: {80})
    monkeypatch.setattr(agent, "_nginx_owned_ports", lambda binary: set())

    report = agent.nginx_capability()
    assert report["present"] is True
    assert report["running"] is False
    assert report["routing_eligible"] is False
    assert "not running" in report["reason"]


def test_preflight_eligibility_requires_the_managed_listener(agent: Any, monkeypatch) -> None:
    monkeypatch.setattr(agent, "_nginx_binary", lambda: "/usr/sbin/nginx")
    monkeypatch.setattr(agent, "_nginx_version", lambda binary: "1.27.5")
    monkeypatch.setattr(agent, "_nginx_running", lambda: True)
    monkeypatch.setattr(agent, "_nginx_config_test", lambda binary, conf=None: (True, ""))
    monkeypatch.setattr(agent, "_listening_ports", lambda: {80})
    # :80 belongs to somebody else, :443 is free.
    monkeypatch.setattr(agent, "_nginx_owned_ports", lambda binary: {8080})

    report = agent.nginx_capability()
    assert report["listener_80"] == "OTHER"
    assert report["listener_443"] == "FREE"
    assert report["routing_eligible"] is False

    # The intended instance owning both is the eligible case.
    monkeypatch.setattr(agent, "_nginx_owned_ports", lambda binary: {80, 443})
    report = agent.nginx_capability()
    assert report["listener_80"] == "MANAGED"
    assert report["listener_443"] == "MANAGED"
    assert report["routing_eligible"] is True
    # :443 unused is also fine in Phase 4 (certificates are Phase 5).
    monkeypatch.setattr(agent, "_nginx_owned_ports", lambda binary: {80})
    monkeypatch.setattr(agent, "_listening_ports", lambda: {80})
    report = agent.nginx_capability()
    assert report["listener_443"] == "FREE"
    assert report["routing_eligible"] is True


def test_unreadable_listener_table_is_unknown_not_free(agent: Any, monkeypatch) -> None:
    """An unreadable ``/proc`` must never be read as "the port is free"."""
    assert agent._listener_ownership(80, None, None) == "UNKNOWN"
    assert agent._listener_ownership(80, {80}, None) == "UNKNOWN"
    assert agent._listener_ownership(80, {80}, {80}) == "MANAGED"
    assert agent._listener_ownership(80, {8080}, {80}) == "OTHER"
    assert agent._listener_ownership(80, {8080}, {8080}) == "FREE"


def test_listener_table_parsing(agent: Any, tmp_path: Path, monkeypatch) -> None:
    proc = tmp_path / "tcp"
    proc.write_text(
        "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt\n"
        "   0: 00000000:0050 00000000:0000 0A 00000000:00000000 00:00000000 00000000\n"
        "   1: 0100007F:1F90 00000000:0000 0A 00000000:00000000 00:00000000 00000000\n"
        "   2: 0100007F:1F91 00000000:0000 01 00000000:00000000 00:00000000 00000000\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent, "NGINX_MANAGED_ROOT", str(tmp_path))
    original_open = open

    def fake_open(path, *args, **kwargs):
        if path == "/proc/net/tcp":
            return original_open(proc, *args, **kwargs)
        if path == "/proc/net/tcp6":
            raise FileNotFoundError(path)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", fake_open)
    assert agent._listening_ports() == {80, 8080}


# --- port reporting ------------------------------------------------------------


def test_container_ports_report_the_four_facts(agent: Any) -> None:
    ports = agent._container_ports(
        {
            "Ports": [
                {"PrivatePort": 8000, "PublicPort": 8081, "Type": "tcp", "IP": "127.0.0.1"},
                {"PrivatePort": 9000, "Type": "tcp"},  # expose-only: no host port
                {"PrivatePort": 5353, "PublicPort": 5353, "Type": "udp"},
                {
                    "PrivatePort": 80,
                    "PublicPort": 80,
                    "Type": "tcp",
                    "IP": "0.0.0.0",  # noqa: S104 - Docker's own port report
                },
            ]
        }
    )
    AgentContainerIn(container_id="a" * 64, name="x", status="RUNNING", ports=ports)
    by_port = {item["container_port"]: item for item in ports}
    assert by_port[8000]["host_port"] == 8081
    assert by_port[8000]["host_ip"] == "127.0.0.1"
    assert "host_port" not in by_port[9000]  # honestly unpublished
    assert by_port[5353]["protocol"] == "udp"
    assert by_port[80]["host_ip"] == "0.0.0.0"  # noqa: S104 - Docker's own port report


def test_container_ports_tolerate_missing_or_malformed_metadata(agent: Any) -> None:
    assert agent._container_ports({}) == []
    assert agent._container_ports({"Ports": None}) == []
    assert agent._container_ports({"Ports": [{"PrivatePort": "80"}]}) == []
    assert agent._container_ports({"Ports": [{"PrivatePort": 0}]}) == []
    assert agent._container_ports({"Ports": ["nonsense"]}) == []
    # An out-of-range published port is dropped rather than forwarded.
    assert agent._container_ports({"Ports": [{"PrivatePort": 80, "PublicPort": 99999}]}) == [
        {"container_port": 80, "protocol": "tcp"}
    ]


def test_collected_container_entries_validate_with_ports(agent: Any, monkeypatch) -> None:
    canned = [
        {
            "Id": "f" * 64,
            "Names": ["/app"],
            "State": "running",
            "Status": "Up 1 minute",
            "Image": "app:latest",
            "Ports": [
                {
                    "PrivatePort": 8000,
                    "PublicPort": 8081,
                    "Type": "tcp",
                    "IP": "0.0.0.0",  # noqa: S104 - Docker's own port report
                }
            ],
        }
    ]

    def fake_request(method: str, path: str, timeout: float = 5.0) -> tuple[int, Any]:
        if path.startswith("/containers/json"):
            return 200, canned
        return 200, {}

    monkeypatch.setattr(agent, "_docker_request", fake_request)
    entries = agent.collect_containers()
    parsed = AgentContainerIn(**entries[0])
    assert parsed.ports[0].host_port == 8081


# --- bundle validation ---------------------------------------------------------


def _agent_bundle(agent: Any, files: list[tuple[str, str]]) -> dict:
    version = 1
    return {
        "bundle_id": agent._tree_fingerprint(files, version),
        "provider": "nginx",
        "template_version": version,
        "manifest": ["a" * 32],
        "files": [{"path": path, "content": content} for path, content in files],
    }


def test_fingerprint_matches_the_control_plane(agent: Any) -> None:
    """The two implementations must produce byte-identical fingerprints."""
    files = [
        (MANAGED_CONF_PATH, "# NexusOps managed\nserver { listen 80; }\n"),
        (f"{ROUTES_DIR}/r-{'0' * 32}.conf", "# route\nserver { listen 80; }\n"),
    ]
    server_side = fingerprint_files(
        [BundleFile(path=path, content=content) for path, content in files], template_version=1
    )
    assert agent._tree_fingerprint(files, 1) == server_side

    # A rendering on the other side of the wire round-trips through JSON without
    # changing the fingerprint.
    payload = json.loads(json.dumps(_agent_bundle(agent, files)))
    validated = agent._validate_bundle(payload)
    assert validated["bundle_id"] == server_side


def test_valid_bundle_is_accepted(agent: Any) -> None:
    bundle = _agent_bundle(
        agent,
        [
            (MANAGED_CONF_PATH, "# http\n"),
            (f"{ROUTES_DIR}/r-{'1' * 32}.conf", "# route\n"),
        ],
    )
    validated = agent._validate_bundle(bundle)
    assert len(validated["files"]) == 2
    assert validated["manifest"] == ["a" * 32]


def test_tampered_content_is_refused(agent: Any) -> None:
    bundle = _agent_bundle(agent, [(MANAGED_CONF_PATH, "# http\n")])
    bundle["files"][0]["content"] = "# http\nproxy_pass http://evil.test;\n"
    with pytest.raises(agent.OperationError) as excinfo:
        agent._validate_bundle(bundle)
    assert excinfo.value.code == "INVALID_BUNDLE"


@pytest.mark.parametrize(
    "path",
    [
        "/etc/nginx/nginx.conf",
        "/etc/passwd",
        f"{ROUTES_DIR}/evil.conf",
        f"{ROUTES_DIR}/../nexusops.conf",
        f"{ROUTES_DIR}/r-{'a' * 31}.conf",
        "relative.conf",
        None,
        42,
    ],
)
def test_path_traversal_is_refused(agent: Any, path: Any) -> None:
    bundle = _agent_bundle(agent, [(MANAGED_CONF_PATH, "# http\n")])
    bundle["files"].append({"path": path, "content": "x"})
    with pytest.raises(agent.OperationError) as excinfo:
        agent._validate_bundle(bundle)
    assert excinfo.value.code == "INVALID_BUNDLE"


def test_malformed_manifests_are_refused(agent: Any) -> None:
    valid = _agent_bundle(agent, [(MANAGED_CONF_PATH, "# http\n")])
    for mutate in (
        {"manifest": "not-a-list"},
        {"manifest": ["x" * 40]},
        {"manifest": [1, 2]},
    ):
        with pytest.raises(agent.OperationError):
            agent._validate_bundle({**valid, **mutate})
    for mutate in (
        {"bundle_id": "short"},
        {"bundle_id": None},
        {"provider": "traefik"},
        {"template_version": 0},
        {"files": "nope"},
        {"files": []},
        {"extra_key": 1},
    ):
        with pytest.raises(agent.OperationError):
            agent._validate_bundle({**valid, **mutate})


def test_oversized_payloads_are_refused(agent: Any) -> None:
    big = _agent_bundle(agent, [(MANAGED_CONF_PATH, "x" * (agent.NGINX_MAX_FILE_BYTES + 1))])
    with pytest.raises(agent.OperationError) as excinfo:
        agent._validate_bundle(big)
    assert excinfo.value.code == "INVALID_BUNDLE"

    many = [
        (f"{ROUTES_DIR}/r-{index:032x}.conf", "x") for index in range(agent.NGINX_MAX_BUNDLE_FILES)
    ]
    with pytest.raises(agent.OperationError):
        agent._validate_bundle(_agent_bundle(agent, [(MANAGED_CONF_PATH, "# http\n"), *many]))


def test_missing_managed_configuration_is_refused(agent: Any) -> None:
    bundle = _agent_bundle(agent, [(f"{ROUTES_DIR}/r-{'0' * 32}.conf", "x")])
    with pytest.raises(agent.OperationError):
        agent._validate_bundle(bundle)


def test_bundle_with_nul_bytes_is_refused(agent: Any) -> None:
    bundle = _agent_bundle(agent, [(MANAGED_CONF_PATH, "# http\n\x00\n")])
    with pytest.raises(agent.OperationError):
        agent._validate_bundle(bundle)


def test_writing_outside_the_managed_root_is_refused(
    agent: Any, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(agent, "NGINX_MANAGED_ROOT", str(tmp_path))
    with pytest.raises(agent.OperationError):
        agent._write_file(str(tmp_path.parent / "escape.conf"), "x")


def test_symlink_targets_are_refused(agent: Any, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(agent, "NGINX_MANAGED_ROOT", str(tmp_path))
    target = tmp_path / "nexusops.conf"
    outside = tmp_path.parent / "outside.conf"
    outside.write_text("original", encoding="utf-8")
    target.symlink_to(outside)
    with pytest.raises(agent.OperationError):
        agent._write_file(str(target), "overwritten")
    assert outside.read_text(encoding="utf-8") == "original"


# --- operation registry and params --------------------------------------------


def test_nginx_operations_are_registered_with_the_nginx_capability(agent: Any) -> None:
    for op_type in ("nginx.bootstrap", "nginx.apply", "nginx.status"):
        spec = agent.OPERATION_REGISTRY[op_type]
        assert spec["capability"] == "nginx"
    # The closed whitelist did not grow a generic primitive.
    assert "node.execute" not in agent.OPERATION_REGISTRY
    assert "file.write" not in agent.OPERATION_REGISTRY


def test_nginx_params_are_closed_shapes(agent: Any) -> None:
    assert agent._validate_params("nginx.bootstrap", {}) == {}
    assert agent._validate_params("nginx.status", {}) == {}
    for bad in ({"x": 1}, {"action": "restart"}):
        with pytest.raises(agent.OperationError):
            agent._validate_params("nginx.bootstrap", bad)
    with pytest.raises(agent.OperationError):
        agent._validate_params("nginx.apply", {"bundle": {}, "shell": "id"})
    with pytest.raises(agent.OperationError):
        agent._validate_params("nginx.apply", {"bundle": "not-an-object"})
    with pytest.raises(agent.OperationError):
        agent._validate_params("nginx.apply", {"bundle": {}, "reload": "yes"})
    assert agent._validate_params("nginx.apply", {"bundle": {}, "reload": False})["reload"] is False


def test_unsupported_operations_are_refused_locally(agent: Any) -> None:
    ok, _output, code, _message = agent.execute_operation(
        "node.execute", {"cmd": "id"}, deadline=None, capabilities={"nginx": {"present": True}}
    )
    assert not ok
    assert code == "OPERATION_UNSUPPORTED"


def test_capability_is_re_checked_locally(agent: Any) -> None:
    ok, _output, code, _message = agent.execute_operation(
        "nginx.apply", {"bundle": {}}, deadline=None, capabilities={"nginx": {"present": False}}
    )
    assert not ok
    assert code == "CAPABILITY_MISSING"


# --- bootstrap include insertion ----------------------------------------------


def test_include_lines_are_inserted_at_http_level_once(agent: Any) -> None:
    original = (
        "user nginx;\n"
        "events { worker_connections 1024; }\n"
        "http {\n"
        "    include /etc/nginx/mime.types;\n"
        "    server { listen 80; }\n"
        "}\n"
    )
    modified = agent._insert_http_includes(original)
    assert modified is not None
    lines = modified.splitlines()
    include_at = lines.index(f"    {agent.NGINX_INCLUDE_HTTP}")
    assert f"    {agent.NGINX_INCLUDE_ROUTES}" in lines
    # Inside the http block (after its opening brace) and before its closing brace
    # — i.e. at http level, not inside the nested server block or the events block.
    http_open = lines.index("http {")
    http_close = len(lines) - 1
    assert http_open < include_at < http_close
    assert lines.count("}") == 1  # only the http block closes; the server block is single-line
    # The rest of the file is untouched.
    assert lines[0] == "user nginx;"
    assert "include /etc/nginx/mime.types;" in modified


def test_include_insertion_refuses_an_ambiguous_file(agent: Any) -> None:
    assert agent._insert_http_includes("events {}\n") is None
    assert agent._insert_http_includes("") is None


def test_include_insertion_handles_a_stream_block(agent: Any) -> None:
    original = "stream {\n    server { listen 9000; }\n}\nhttp {\n    server { listen 80; }\n}\n"
    modified = agent._insert_http_includes(original)
    assert modified is not None
    lines = modified.splitlines()
    include_at = lines.index(f"    {agent.NGINX_INCLUDE_HTTP}")
    # After the http block opens and before the stream block's own braces are
    # touched — the stream block is left byte-identical.
    assert include_at > lines.index("http {")
    assert lines[: lines.index("http {")] == ["stream {", "    server { listen 9000; }", "}"]


def test_bootstrap_refuses_when_the_master_process_is_unknown(
    agent: Any, tmp_path: Path, monkeypatch
) -> None:
    """An unidentifiable nginx must not be reported as a successful bootstrap."""
    monkeypatch.setattr(agent, "_nginx_binary", lambda: "/usr/sbin/nginx")
    monkeypatch.setattr(agent, "_nginx_running", lambda: None)
    with pytest.raises(agent.OperationError) as excinfo:
        agent._nginx_bootstrap()
    assert excinfo.value.code == "NGINX_STATE_UNKNOWN"


def _bootstrap_fixture(agent: Any, tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """Stage bootstrap's real layout: the system config lives *outside* the tree.

    This is the shape every real node has (``/etc/nginx/nginx.conf`` vs
    ``/etc/nexusops/nginx``), and the one an E2E run caught the write path getting
    wrong: the managed root's own writer refuses any parent outside the tree.
    """
    managed = tmp_path / "managed"
    system_conf = tmp_path / "nginx" / "nginx.conf"
    system_conf.parent.mkdir(parents=True, exist_ok=True)
    system_conf.write_text(
        "user nginx;\nevents {}\nhttp {\n    include mime.types;\n    server { listen 80; }\n}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(agent, "NGINX_MANAGED_ROOT", str(managed))
    monkeypatch.setattr(agent, "NGINX_MANAGED_CONF", str(managed / "nexusops.conf"))
    monkeypatch.setattr(agent, "NGINX_ROUTES_DIR", str(managed / "routes.d"))
    monkeypatch.setattr(agent, "NGINX_STAGED_DIR", str(managed / "staged"))
    monkeypatch.setattr(agent, "NGINX_BACKUP_DIR", str(managed / "backup"))
    monkeypatch.setattr(agent, "NGINX_STATE_DIR", str(managed / "state"))
    monkeypatch.setattr(agent, "NGINX_SYSTEM_CONF", str(system_conf))
    monkeypatch.setattr(agent, "_nginx_binary", lambda: "/usr/sbin/nginx")
    monkeypatch.setattr(agent, "_nginx_running", lambda: True)
    monkeypatch.setattr(agent, "_nginx_config_test", lambda binary, conf=None: (True, ""))
    monkeypatch.setattr(agent, "_reload_nginx", lambda binary: (True, ""))
    return managed, system_conf


def test_bootstrap_edits_the_customer_conf_outside_the_managed_tree(
    agent: Any, tmp_path: Path, monkeypatch
) -> None:
    """The one write outside the tree: the includes land, and it still validates."""
    managed, system_conf = _bootstrap_fixture(agent, tmp_path, monkeypatch)

    result = agent._nginx_bootstrap()

    assert result == {"bootstrapped": True, "changed": True, "config_test_ok": True}
    modified = system_conf.read_text(encoding="utf-8")
    assert agent.NGINX_INCLUDE_HTTP in modified
    assert agent.NGINX_INCLUDE_ROUTES in modified
    # At http level, and the customer's own directives are untouched.
    lines = modified.splitlines()
    assert lines.index("http {") < lines.index(f"    {agent.NGINX_INCLUDE_HTTP}")
    assert "include mime.types;" in modified
    # A recoverable backup of the file it changed, before it changed it.
    assert (managed / "backup" / "nginx.conf.prev").read_text(encoding="utf-8") != modified
    # The include's target exists, so the customer's own `nginx -t` still passes.
    assert (managed / "nexusops.conf").exists()

    # Idempotent: a second run changes nothing and reports that honestly.
    again = agent._nginx_bootstrap()
    assert again == {"bootstrapped": True, "changed": False, "config_test_ok": True}


def test_bootstrap_refuses_to_write_through_a_symlink(
    agent: Any, tmp_path: Path, monkeypatch
) -> None:
    managed, system_conf = _bootstrap_fixture(agent, tmp_path, monkeypatch)
    elsewhere = "user nginx;\nevents {}\nhttp {\n    server { listen 80; }\n}\n"
    target = tmp_path / "elsewhere.conf"
    target.write_text(elsewhere, encoding="utf-8")
    system_conf.unlink()
    system_conf.symlink_to(target)

    with pytest.raises(agent.OperationError) as excinfo:
        agent._nginx_bootstrap()
    assert excinfo.value.code == "NGINX_CONFIG_UNSAFE"
    # The file the symlink points at is untouched — no include appeared in it.
    assert target.read_text(encoding="utf-8") == elsewhere
    assert managed.exists()


def test_status_reports_bounded_state(agent: Any, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(agent, "NGINX_MANAGED_ROOT", str(tmp_path))
    monkeypatch.setattr(agent, "NGINX_MANAGED_CONF", str(tmp_path / "nexusops.conf"))
    monkeypatch.setattr(agent, "NGINX_ROUTES_DIR", str(tmp_path / "routes.d"))
    monkeypatch.setattr(agent, "NGINX_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(agent, "_nginx_binary", lambda: "/usr/sbin/nginx")
    monkeypatch.setattr(agent, "_nginx_version", lambda binary: "1.27.5")
    monkeypatch.setattr(agent, "_nginx_running", lambda: True)
    monkeypatch.setattr(agent, "_nginx_config_test", lambda binary, conf=None: (True, ""))
    (tmp_path / "routes.d").mkdir()
    (tmp_path / "nexusops.conf").write_text(
        "# templates v1\nserver { listen 80; }\n", encoding="utf-8"
    )
    report = agent._nginx_status()
    assert report["nginx_version"] == "1.27.5"
    assert report["config_test_ok"] is True
    assert len(report["live_bundle_id"]) == 64
    assert report["fragments"] == 0
    # No key leaks configuration *text*.
    assert all(isinstance(value, (str, int, bool, type(None))) for value in report.values())
