#!/usr/bin/env python3
"""NexusOps host agent — protocol v2.

Reports host metrics and Docker container state to a NexusOps control plane, and
executes a **closed whitelist** of operations the control plane queues for this
node (start/stop/restart/remove a container, tail its logs). Python 3 standard
library only — no pip dependencies — so it runs on any machine with ``python3``.

Usage:
    python3 nexusops_agent.py --server https://nexusops.example.com \\
        --token nxa_... [--interval 30] [--once]

Environment overrides: ``NEXUSOPS_SERVER``, ``NEXUSOPS_TOKEN``,
``NEXUSOPS_INTERVAL``, ``NEXUSOPS_TOKEN_FILE``, ``NEXUSOPS_CA_BUNDLE``.

Security stance (docs/node-agent-architecture.md §6):

* **Transport is HTTPS-only.** A non-loopback ``http://`` server URL is refused
  before any credential is sent, and certificate verification is never disabled
  (a private CA is trusted through ``NEXUSOPS_CA_BUNDLE`` instead).
* **Whitelist, not shell.** Operations map to fixed Docker API calls over the
  unix socket. There is no ``shell=True``, no arbitrary command string, and no
  ``/containers/{id}/exec``. The agent re-validates the operation type and its
  parameters locally; a malformed or malicious control-plane message cannot
  become local code execution.
* **Rotation is survivable.** A new credential is written atomically (temp file
  + rename + fsync) and acknowledged on the next beat; a crash between receive
  and persist self-heals because the control plane re-sends until acknowledged.
"""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import os
import re
import shutil
import signal
import socket
import ssl
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime

AGENT_VERSION = "1.1.0"
#: Wire protocol this agent speaks. The control plane negotiates the lower of the
#: two; an old agent never receives a v2 heartbeat body.
PROTOCOL_VERSION = 2

#: Cadence a server-rejected token is re-checked at. Deliberately long: a
#: revoked or rotated-away token cannot repair itself, and the shipped systemd
#: unit uses ``Restart=always``/``RestartSec=10`` — exiting on 401 turned every
#: revocation into an endless storm of rejected requests. Parking here instead
#: keeps the node quiet until an operator re-enrolls it
#: (docs/node-agent-architecture.md §3.4).
REVOKED_POLL_SECONDS = 900

#: Where the issued node credential is stored. Owner-only, atomic replace.
DEFAULT_TOKEN_FILE = "/etc/nexusops-agent/token"

_STOP = {"flag": False}


def _handle_signal(signum, _frame):  # type: ignore[no-untyped-def]
    _STOP["flag"] = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# --- System metric collection (/proc based) ----------------------------------


def read_cpu_times() -> tuple[int, int]:
    """Return (busy, total) jiffies from /proc/stat."""
    with open("/proc/stat", encoding="ascii") as fh:
        parts = fh.readline().split()
    values = [int(v) for v in parts[1:]]
    # user nice system idle iowait irq softirq steal ...
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    total = sum(values)
    return total - idle, total


def cpu_percent_since(prev: tuple[int, int], cur: tuple[int, int]) -> float:
    busy_d = cur[0] - prev[0]
    total_d = cur[1] - prev[1]
    if total_d <= 0:
        return 0.0
    return round(min(busy_d / total_d * 100.0, 100.0), 1)


def memory_stats() -> tuple[int, float]:
    """Return (used_mb, used_percent) from /proc/meminfo."""
    info = {}
    with open("/proc/meminfo", encoding="ascii") as fh:
        for line in fh:
            key, _, rest = line.partition(":")
            info[key.strip()] = int(rest.split()[0])  # kB
    total_kb = info.get("MemTotal", 0)
    available_kb = info.get("MemAvailable", info.get("MemFree", 0))
    used_mb = max((total_kb - available_kb) // 1024, 0)
    percent = round(used_mb * 1024 / total_kb * 100.0, 1) if total_kb else 0.0
    return used_mb, percent


def memory_total_mb() -> int:
    try:
        with open("/proc/meminfo", encoding="ascii") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0


def disk_stats(path: str = "/") -> tuple[float, float]:
    """Return (used_gb, used_percent)."""
    usage = shutil.disk_usage(path)
    used_gb = round(usage.used / 1024**3, 2)
    percent = round(usage.used / usage.total * 100.0, 1) if usage.total else 0.0
    return used_gb, percent


def load1() -> float:
    try:
        return round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):  # not all platforms have getloadavg
        return 0.0


def uptime_seconds() -> int:
    try:
        with open("/proc/uptime", encoding="ascii") as fh:
            return int(float(fh.read().split()[0]))
    except (OSError, ValueError):
        return 0


def os_info() -> tuple[str, str]:
    name = sys.platform
    version = ""
    try:
        import platform

        name = platform.system() or name
        version = platform.release() or ""
    except Exception:  # pragma: no cover - platform never fails in practice
        pass
    return name, version


# --- Honest network rates -----------------------------------------------------
#
# The v1 contract shipped ``net_rx_kb_s``/``net_tx_kb_s`` hard-coded to 0.0 and
# dashboards rendered that as measured throughput. It was not: a fabricated zero
# is indistinguishable from a genuinely idle interface, and nobody could tell.
# v2 measures from the Linux interface counters and reports ``null`` whenever it
# cannot: first sample (no previous reading to diff), missing counters, or a
# counter reset (interface flap / wrap). ``None`` is *unavailable*, never zero.

#: One module-level sample: build_heartbeat's signature is pinned by the
#: contract tests, so the network diff state lives beside the collector rather
#: than in a third positional argument.
_NET_STATE: dict[str, tuple[int, int, float]] = {}


def network_total_bytes() -> tuple[int, int, int]:
    """Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev."""
    rx = tx = interfaces = 0
    with open("/proc/net/dev", encoding="ascii") as fh:
        lines = fh.readlines()[2:]  # two header lines
    for line in lines:
        name, sep, rest = line.partition(":")
        if not sep:
            continue
        fields = rest.split()
        if len(fields) < 9:
            continue
        if name.strip() == "lo":
            continue  # loopback is not network traffic in any useful sense
        rx += int(fields[0])
        tx += int(fields[8])
        interfaces += 1
    return rx, tx, interfaces


def network_rates() -> tuple[float | None, float | None]:
    """Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable."""
    try:
        rx, tx, _ = network_total_bytes()
    except (OSError, ValueError, IndexError):
        return None, None
    now = time.monotonic()
    previous = _NET_STATE.get("sample")
    _NET_STATE["sample"] = (rx, tx, now)
    if previous is None:
        return None, None  # first sample: no interval to divide by
    prev_rx, prev_tx, prev_at = previous
    elapsed = now - prev_at
    if elapsed <= 0 or rx < prev_rx or tx < prev_tx:
        return None, None  # clock hiccup or counter reset — not a negative rate
    return round((rx - prev_rx) / 1024 / elapsed, 2), round((tx - prev_tx) / 1024 / elapsed, 2)


# --- Docker capability + API access ------------------------------------------


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str, timeout: float = 5.0) -> None:
        super().__init__("localhost", timeout=timeout)
        self._socket_path = socket_path

    def connect(self) -> None:  # noqa: D102 - http.client contract
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self._socket_path)
        self.sock = sock


#: One-shot docker stats calls per heartbeat. Each is a socket roundtrip;
#: the cap keeps a busy host from stretching the heartbeat loop.
MAX_CONTAINER_STATS = 12

_STATE_MAP = {
    "running": "RUNNING",
    "exited": "EXITED",
    "paused": "PAUSED",
    "created": "CREATED",
    "restarting": "RESTARTING",
    "dead": "DEAD",
}

_DOCKER_SOCKETS = ("/var/run/docker.sock", "/run/docker.sock")


def _docker_socket() -> str | None:
    for path in _DOCKER_SOCKETS:
        if os.path.exists(path):
            return path
    return None


def _docker_raw(method: str, path: str, timeout: float = 5.0) -> tuple[int, bytes]:
    """One raw Docker API call; returns ``(status, body_bytes)``."""
    last_error: Exception | None = None
    for sock_path in _DOCKER_SOCKETS:
        if not os.path.exists(sock_path):
            continue
        conn = _UnixHTTPConnection(sock_path, timeout=timeout)
        try:
            conn.request(method, path, headers={"Host": "docker"})
            resp = conn.getresponse()
            body = resp.read()
            return resp.status, body
        except (OSError, http.client.HTTPException) as exc:
            last_error = exc
            continue
        finally:
            try:
                conn.close()
            except Exception:
                pass
    raise OSError(f"docker socket unreachable: {last_error or 'not found'}")


def _docker_request(
    method: str, path: str, timeout: float = 5.0
) -> tuple[int, dict | list | None]:
    status, body = _docker_raw(method, path, timeout=timeout)
    parsed: dict | list | None = None
    if body and status == 200:
        try:
            parsed = json.loads(body.decode("utf-8"))
        except ValueError:
            parsed = None
    return status, parsed


def docker_capability() -> dict:
    """Report Docker availability by *talking to the daemon*, not by path lookup.

    A binary on PATH proves nothing. The capability is present only when the
    socket connects **and** ``/version`` answers, so a stopped daemon, a denied
    socket or an unsupported API is reported honestly rather than as available.
    """
    if _docker_socket() is None:
        return {"present": False}
    try:
        status, payload = _docker_request("GET", "/version", timeout=3.0)
    except (OSError, ValueError):
        return {"present": False}
    if status != 200 or not isinstance(payload, dict):
        return {"present": False}
    api_version = payload.get("ApiVersion")
    return {
        "present": True,
        "version": str(payload.get("Version", ""))[:64] or None,
        "api_version": str(api_version)[:32] if api_version else None,
    }


def systemd_capability() -> dict:
    """systemd is present when it is actually running as the init system."""
    return {"present": os.path.isdir("/run/systemd/system")}


def build_capabilities() -> dict[str, dict]:
    return {"docker": docker_capability(), "systemd": systemd_capability()}


def build_facts() -> dict:
    """Open-ended host facts, stored in the node's flexible JSONB blob.

    Deliberately small and bounded: facts are telemetry, not a data plane. A new
    property can be added here without a database column per property.
    """
    facts: dict = {}
    try:
        _, _, interfaces = network_total_bytes()
        facts["network_interfaces"] = interfaces
    except (OSError, ValueError, IndexError):
        pass
    try:
        usage = shutil.disk_usage("/")
        facts["disks"] = [
            {
                "mount": "/",
                "total_gb": round(usage.total / 1024**3, 1),
                "free_gb": round(usage.free / 1024**3, 1),
            }
        ]
    except OSError:
        pass
    try:
        import platform

        facts["kernel"] = platform.release()[:64]
    except Exception:  # pragma: no cover
        pass
    return facts


def collect_containers(max_inspect: int = 10) -> list[dict]:
    """Best-effort container list; empty when no docker socket is present."""
    try:
        # Unversioned paths negotiate the daemon's current API; pinned old
        # versions (v1.24) are rejected by Docker >= 26.
        status, payload = _docker_request("GET", "/containers/json?all=1")
    except (OSError, ValueError):
        return []
    if status != 200 or not isinstance(payload, list):
        return []

    containers: list[dict] = []
    for item in payload[:50]:
        state = str(item.get("State", "")).lower()
        health = ""
        status_text = str(item.get("Status", ""))
        if "(healthy)" in status_text:
            health = "HEALTHY"
        elif "(unhealthy)" in status_text:
            health = "UNHEALTHY"
        elif "(health: starting)" in status_text:
            health = "STARTING"

        entry = {
            "container_id": str(item.get("Id", ""))[:64],
            "name": (item.get("Names") or ["unknown"])[0].lstrip("/")[:200],
            "status": _STATE_MAP.get(state, "CREATED"),
            # "" is not a ContainerHealth — send null (unknown) instead, or the
            # whole heartbeat is rejected as 422.
            "health": health or None,
            "image_ref": str(item.get("Image", ""))[:300],
            "restart_count": 0,
        }

        # RestartCount/Health need inspect; cap it so a huge fleet stays cheap.
        if len(containers) < max_inspect and entry["container_id"]:
            try:
                istatus, idata = _docker_request(
                    "GET", f"/containers/{entry['container_id'][:12]}/json"
                )
                if istatus == 200 and isinstance(idata, dict):
                    entry["restart_count"] = int(idata.get("RestartCount", 0))
                    health_obj = idata.get("State", {}).get("Health") or {}
                    if not health and health_obj.get("Status"):
                        entry["health"] = str(health_obj["Status"]).upper()
            except (OSError, ValueError):
                pass

        containers.append(entry)
    return containers


def collect_container_stats(
    container_ids: list[str],
    prev_cpu: dict[str, tuple[float, float]],
) -> tuple[dict[str, dict], dict[str, tuple[float, float]]]:
    """One-shot docker stats for running containers, CPU diffed across cycles.

    Docker's one-shot stats carry no previous cycle, so the CPU percentage is
    computed here from the caller's last sample per container (mirroring how
    host CPU is diffed between heartbeats). Returns (updates, new_prev):
    ``updates`` maps container_id -> {cpu_percent, mem_used_mb, mem_limit_mb}
    ready to merge into the heartbeat's container entries; ``cpu_percent`` is
    omitted on a container's first sighting and the platform keeps whatever it
    had. ``new_prev`` only contains containers seen this cycle, so stale ids
    age out on their own.
    """
    updates: dict[str, dict] = {}
    new_prev: dict[str, tuple[float, float]] = {}
    for cid in container_ids[:MAX_CONTAINER_STATS]:
        try:
            status, data = _docker_request(
                "GET", f"/containers/{cid[:12]}/stats?stream=false&one-shot=true", timeout=3.0
            )
        except (OSError, ValueError):
            continue
        if status != 200 or not isinstance(data, dict):
            continue

        cpu_stats = data.get("cpu_stats") or {}
        cpu_usage = cpu_stats.get("cpu_usage") or {}
        cpu_total = float(cpu_usage.get("total_usage") or 0)
        system_total = float(cpu_stats.get("system_cpu_usage") or 0)
        online = float(cpu_stats.get("online_cpus") or 0) or 1.0

        previous = prev_cpu.get(cid)
        if previous is not None:
            delta_cpu = cpu_total - previous[0]
            delta_system = system_total - previous[1]
            # A zero CPU delta is a legitimate 0% reading (idle container) —
            # only a negative one (counter reset / container restart) is
            # unusable and skipped.
            if delta_cpu >= 0 and delta_system > 0:
                updates[cid] = {
                    "cpu_percent": round(min(delta_cpu / delta_system * online * 100.0, 100.0 * online), 2)
                }
        new_prev[cid] = (cpu_total, system_total)

        memory = data.get("memory_stats") or {}
        mem_used = float(memory.get("usage") or 0)
        detail = memory.get("stats") or {}
        # cgroup v2 reports inactive_file, v1 total_inactive_file; both are the
        # cache component docker stats subtracts for "used".
        inactive = detail.get("inactive_file", detail.get("total_inactive_file"))
        if isinstance(inactive, (int, float)):
            mem_used = max(mem_used - float(inactive), 0.0)
        entry = updates.setdefault(cid, {})
        entry["mem_used_mb"] = round(mem_used / 1024 / 1024, 2)
        limit = memory.get("limit")
        if isinstance(limit, (int, float)) and float(limit) > 0:
            entry["mem_limit_mb"] = round(float(limit) / 1024 / 1024, 2)
    return updates, new_prev


# --- Operation executor (the only place the agent acts) -----------------------
#
# The registry is compile-time. A control-plane payload names one of these keys
# and nothing else: there is no generic runner, no shell, and no way for the
# server to introduce a new operation type. Every entry declares the capability
# it needs, its parameter shape and its bound; the agent re-checks all of them
# even though the control plane already validated the operation.

CONTAINER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,71}$")

#: Bound the log operation on every axis: requested lines, bytes collected, and
#: wall-clock time.
LOGS_TAIL_MAX = 500
LOGS_MAX_BYTES = 65536
LOGS_TIMEOUT_SECONDS = 20

#: Byte count of the docker multiplexed-stream frame header.
_DOCKER_FRAME_HEADER = 8

OPERATION_REGISTRY: dict[str, dict] = {
    "container.start": {"capability": "docker", "timeout": 60, "action": "start"},
    "container.stop": {"capability": "docker", "timeout": 60, "action": "stop"},
    "container.restart": {"capability": "docker", "timeout": 60, "action": "restart"},
    "container.remove": {"capability": "docker", "timeout": 60, "action": "remove"},
    "logs.tail": {"capability": "docker", "timeout": 30, "action": "logs"},
}


class OperationError(Exception):
    """A stable, sanitized failure contract for the control plane."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _validate_container_id(value: object) -> str:
    if not isinstance(value, str) or not CONTAINER_ID_RE.match(value):
        raise OperationError("INVALID_PARAMS", "container_id is missing or malformed")
    return value


def _validate_params(op_type: str, params: object) -> dict:
    """Re-validate the operation's parameters locally, against a closed shape."""
    if not isinstance(params, dict):
        raise OperationError("INVALID_PARAMS", "operation params must be an object")
    if op_type == "logs.tail":
        allowed = {"container_id", "tail", "since"}
        if set(params) - allowed:
            raise OperationError("INVALID_PARAMS", "unexpected log parameters")
        _validate_container_id(params.get("container_id"))
        tail = params.get("tail", 100)
        if not isinstance(tail, int) or isinstance(tail, bool) or not 1 <= tail <= LOGS_TAIL_MAX:
            raise OperationError("INVALID_PARAMS", f"tail must be 1..{LOGS_TAIL_MAX}")
        since = params.get("since")
        if since is not None and (not isinstance(since, str) or len(since) > 64):
            raise OperationError("INVALID_PARAMS", "since must be a short string")
        return params
    # container lifecycle/removal
    allowed = {"container_id", "force"}
    if set(params) - allowed:
        raise OperationError("INVALID_PARAMS", "unexpected container parameters")
    _validate_container_id(params.get("container_id"))
    force = params.get("force", False)
    if not isinstance(force, bool):
        raise OperationError("INVALID_PARAMS", "force must be a boolean")
    return params


def _sanitize_text(text: str, *, max_bytes: int) -> str:
    """Make control characters safe and bound the result.

    Never touches container environment variables or secret material by
    construction — it only receives bytes the docker logs endpoint already
    returned for the named container.
    """
    cleaned = "".join(ch if ch in "\n\t" or ch.isprintable() else " " for ch in text)
    encoded = cleaned.encode("utf-8", "replace")
    if len(encoded) > max_bytes:
        cleaned = encoded[:max_bytes].decode("utf-8", "ignore") + "\n[truncated]"
    return cleaned


def _demux_docker_stream(data: bytes) -> bytes | None:
    """Decode docker's 8-byte-header frame stream, or ``None`` if not framed."""
    out = bytearray()
    index = 0
    while index + _DOCKER_FRAME_HEADER <= len(data):
        stream_type = data[index]
        if stream_type not in (0, 1, 2) or data[index + 1 : index + 4] != b"\x00\x00\x00":
            return None
        size = int.from_bytes(data[index + 4 : index + 8], "big")
        chunk = data[index + 8 : index + 8 + size]
        if len(chunk) < size:
            break
        out.extend(chunk)
        index += 8 + size
    return bytes(out)


def _container_status(container_id: str) -> str | None:
    try:
        status, data = _docker_request("GET", f"/containers/{container_id[:12]}/json", timeout=5.0)
    except (OSError, ValueError):
        return None
    if status != 200 or not isinstance(data, dict):
        return None
    state = str((data.get("State") or {}).get("Status", ""))
    return state.upper() or None


def _run_docker_action(action: str, params: dict, timeout: float) -> dict:
    """Perform one registry action. Raises :class:`OperationError` on failure."""
    container_id = _validate_container_id(params.get("container_id"))
    short = container_id[:12]
    try:
        if action in ("start", "stop", "restart"):
            status, _ = _docker_raw("POST", f"/containers/{short}/{action}", timeout=timeout)
            # 204 done / 304 already in the requested state.
            if status not in (204, 304):
                raise _docker_error(status, f"container.{action} failed")
            new_status = _container_status(container_id)
            return {"status": new_status} if new_status else {"action": action}
        if action == "remove":
            force = "1" if params.get("force") else "0"
            status, _ = _docker_raw(
                "DELETE", f"/containers/{short}?force={force}&v=0", timeout=timeout
            )
            if status not in (204, 200):
                raise _docker_error(status, "container.remove failed")
            return {"removed": True, "force": bool(params.get("force"))}
        if action == "logs":
            tail = int(params.get("tail", 100))
            query = f"stdout=1&stderr=1&timestamps=0&tail={tail}"
            status, body = _docker_raw(
                "GET", f"/containers/{short}/logs?{query}", timeout=timeout
            )
            if status != 200:
                raise _docker_error(status, "logs.tail failed")
            payload = _demux_docker_stream(body[:LOGS_MAX_BYTES])
            if payload is None:
                payload = body[:LOGS_MAX_BYTES]
            text = payload.decode("utf-8", "replace")
            # Bound again to the *requested* tail: the daemon is asked for
            # ``tail=N`` but the agent does not rely on it obeying.
            lines = text.splitlines()[: min(tail, LOGS_TAIL_MAX)]
            return {
                "container_id": short,
                "lines": len(lines),
                "log": _sanitize_text("\n".join(lines), max_bytes=LOGS_MAX_BYTES),
            }
    except socket.timeout as exc:
        raise OperationError("OPERATION_TIMEOUT", "docker call timed out") from exc
    except OSError as exc:
        raise OperationError("DOCKER_UNAVAILABLE", _sanitize_text(str(exc), max_bytes=200)) from exc
    raise OperationError("OPERATION_UNSUPPORTED", f"unknown action {action!r}")


def _docker_error(status: int, fallback: str) -> OperationError:
    if status == 404:
        return OperationError("CONTAINER_NOT_FOUND", "container not found on this node")
    if status == 409:
        return OperationError("CONTAINER_CONFLICT", "the container cannot change state now")
    if status == 403:
        return OperationError("DOCKER_PERMISSION_DENIED", "docker denied the operation")
    return OperationError("DOCKER_ERROR", f"{fallback} (docker status {status})")


def execute_operation(
    op_type: str,
    params: object,
    *,
    deadline: float | None,
    capabilities: dict,
) -> tuple[bool, dict, str | None, str | None]:
    """Run one whitelisted operation locally.

    Returns ``(ok, output, error_code, error_message)``. Every failure path is a
    stable code + a sanitized message — never a raw daemon body, and never
    another container's environment or secret data.
    """
    spec = OPERATION_REGISTRY.get(op_type)
    if spec is None:
        return False, {}, "OPERATION_UNSUPPORTED", "operation type is not in the local registry"
    # Local capability re-check: a stale or falsely-reported server-side claim
    # must never cause an unsafe execution.
    capability = spec["capability"]
    report = capabilities.get(capability) or {}
    if not report.get("present"):
        return False, {}, "CAPABILITY_MISSING", f"local capability '{capability}' is unavailable"

    try:
        validated = _validate_params(op_type, params)
    except OperationError as exc:
        return False, {}, exc.code, exc.message

    remaining = spec["timeout"] if deadline is None else min(spec["timeout"], deadline - time.time())
    if remaining <= 0:
        return False, {}, "OPERATION_TIMEOUT", "the operation deadline had already passed"
    timeout = max(min(remaining, spec["timeout"]), 1.0)

    try:
        output = _run_docker_action(spec["action"], validated, timeout)
    except OperationError as exc:
        return False, {}, exc.code, exc.message
    except Exception as exc:  # never leak an unhandled traceback over the wire
        return False, {}, "AGENT_ERROR", _sanitize_text(str(exc), max_bytes=200)
    return True, output, None, None


# --- Credential persistence ---------------------------------------------------


def read_token_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def persist_token(path: str, token: str) -> bool:
    """Atomically store *token* at 0600.

    Temp file in the same directory + fsync + ``os.replace`` + directory fsync:
    a crash before the rename leaves the old credential intact, and a crash
    after leaves the new one — never a half-written file.
    """
    directory = os.path.dirname(path) or "."
    try:
        os.makedirs(directory, mode=0o700, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=directory, prefix=".token.")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(token)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temp_path, path)
        except BaseException:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
        dir_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
        return True
    except OSError as exc:
        print(f"[nexusops-agent] could not persist the credential: {exc}", file=sys.stderr)
        return False


# --- Server transport ----------------------------------------------------------


def _tls_context(ca_bundle: str | None) -> ssl.SSLContext:
    """A verifying TLS context. Verification is never disabled.

    A private/self-hosted CA is trusted by pointing ``NEXUSOPS_CA_BUNDLE`` at the
    CA file (or by installing it in the system trust store) — not by turning off
    certificate checks, which would let an on-path attacker impersonate the
    control plane and harvest the node credential.
    """
    if ca_bundle:
        return ssl.create_default_context(cafile=ca_bundle)
    return ssl.create_default_context()


class AgentClient:
    def __init__(
        self,
        server_url: str,
        token: str,
        ca_bundle: str | None = None,
    ) -> None:
        parsed = urllib.parse.urlparse(server_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError(
                f"invalid server URL {server_url!r}: an https:// base URL is required"
            )
        self.use_tls = parsed.scheme == "https"
        self.host = parsed.hostname
        self.port = parsed.port or (443 if self.use_tls else 80)
        self.base_path = parsed.path.rstrip("/")
        self.token = token
        self._ctx = _tls_context(ca_bundle) if self.use_tls else None
        if not self.use_tls:
            self._require_loopback_plain_http()

    def _require_loopback_plain_http(self) -> None:
        """Refuse to send credentials over plain HTTP to a non-loopback server.

        The ``X-Agent-Token`` header authenticates every call, and the enrollment
        token mints node identities. Over plain HTTP any passive observer on the
        path captures it. Only a **genuine loopback** destination is exempt —
        ``localhost``, or an address in the ``127.0.0.0/8`` / ``::1`` ranges,
        where the credential cannot leave the host. Everything else, including
        link-local (169.254.0.0/16, fe80::/10), private LAN and public addresses,
        is a hard error with no override — terminate TLS at the edge instead.
        """
        host = (self.host or "").strip()
        # ``localhost`` is the only name exempted, and only as a whole host: a
        # name like ``localhost.example.com`` resolves to a real remote host, so
        # a prefix match would be an impersonation hole.
        is_named_loopback = host.lower() in ("localhost", "localhost.")
        try:
            # ``ip_address`` rejects a bracketless/zoney form, so anything it
            # cannot parse is treated as a remote name (never exempt). This also
            # catches IPv4-mapped loopback (``::ffff:127.0.0.1``), whose
            # ``is_loopback`` is true.
            is_ip_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_ip_loopback = False
        if is_named_loopback or is_ip_loopback:
            return
        raise ValueError(
            f"refusing to send the agent credential over plain HTTP to {host}:{self.port}. "
            "Only genuine loopback (localhost, 127.0.0.0/8, ::1) may skip TLS; use an "
            "https:// server URL (terminate TLS at your edge). Certificate verification "
            "is never disabled; trust a private CA with NEXUSOPS_CA_BUNDLE."
        )

    def request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        conn: http.client.HTTPConnection
        if self.use_tls:
            assert self._ctx is not None
            conn = http.client.HTTPSConnection(self.host, self.port, timeout=15, context=self._ctx)
        else:
            conn = http.client.HTTPConnection(self.host, self.port, timeout=15)
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "X-Agent-Token": self.token,
            "Content-Type": "application/json",
            "User-Agent": f"nexusops-agent/{AGENT_VERSION}",
        }
        try:
            conn.request(method, self.base_path + f"/api/v1{path}", body=body, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            data = json.loads(raw.decode("utf-8")) if raw and raw.strip().startswith(b"{") else {}
            return resp.status, data
        finally:
            try:
                conn.close()
            except Exception:
                pass


# --- Main loop ------------------------------------------------------------------


def build_heartbeat(
    prev_cpu: tuple[int, int] | None,
    prev_container_cpu: dict[str, tuple[float, float]] | None = None,
) -> tuple[dict, tuple[int, int], dict[str, tuple[float, float]]]:
    now_cpu = read_cpu_times()
    cpu = cpu_percent_since(prev_cpu, now_cpu) if prev_cpu else 0.0
    mem_used_mb, mem_percent = memory_stats()
    disk_used_gb, disk_percent = disk_stats()
    net_rx, net_tx = network_rates()
    payload = {
        "cpu_percent": cpu,
        "mem_used_mb": mem_used_mb,
        "mem_percent": mem_percent,
        "disk_used_gb": disk_used_gb,
        "disk_percent": disk_percent,
        # None = not measurable, rendered as unavailable rather than 0.0.
        "net_rx_kb_s": net_rx,
        "net_tx_kb_s": net_tx,
        "load1": load1(),
        "uptime_seconds": uptime_seconds(),
    }
    containers = collect_containers()
    container_cpu_prev = prev_container_cpu or {}
    if containers:
        stats_by_cid, container_cpu_prev = collect_container_stats(
            [e["container_id"] for e in containers if e.get("status") == "RUNNING"],
            container_cpu_prev,
        )
        for entry in containers:
            stats = stats_by_cid.get(entry["container_id"])
            if stats:
                entry.update(stats)
        payload["containers"] = containers
    return payload, now_cpu, container_cpu_prev


def _interruptible_sleep(seconds: float) -> None:
    """Sleep in short slices so SIGTERM/SIGINT stop the agent promptly."""
    deadline = time.monotonic() + seconds
    while not _STOP["flag"] and time.monotonic() < deadline:
        time.sleep(0.5)


def _warn_revoked(warned: bool) -> bool:
    """Print the revoked-state notice once per entry; return True thereafter."""
    if warned:
        return True
    print(
        "[nexusops-agent] token rejected by server — this node is revoked or was "
        "rotated away. NOT exiting (systemd would restart into a request storm); "
        f"retrying every {REVOKED_POLL_SECONDS // 60} minutes. Re-enroll this node "
        "with a fresh token to restore reporting.",
        file=sys.stderr,
    )
    return True


def _build_hello_payload() -> dict:
    usage = shutil.disk_usage("/")
    os_name, os_version = os_info()
    import platform

    return {
        "agent_version": AGENT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "os_name": os_name,
        "os_version": os_version,
        "arch": platform.machine(),
        "cpu_cores": os.cpu_count() or 1,
        "memory_total_mb": memory_total_mb(),
        "disk_total_gb": int(usage.total / 1024**3),
        "hostname": socket.gethostname(),
        "capabilities": build_capabilities(),
        "facts": build_facts(),
    }


def _enroll(client: "AgentClient", enrollment_token: str) -> tuple[bool, str]:
    """Exchange an ``nxk_`` enrollment token for a node credential.

    Returns ``(ok, token)``. The raw credential is only ever written by the
    caller through :func:`persist_token`.
    """
    import platform

    try:
        usage = shutil.disk_usage("/")
        status, data = client.request(
            "POST",
            "/agent/enroll",
            {
                "enrollment_token": enrollment_token,
                "hostname": socket.gethostname(),
                "agent_version": AGENT_VERSION,
                "arch": platform.machine(),
                "cpu_cores": os.cpu_count() or 1,
                "memory_total_mb": memory_total_mb(),
                "disk_total_gb": int(usage.total / 1024**3),
            },
        )
    except (OSError, http.client.HTTPException) as exc:
        print(f"[nexusops-agent] enrollment failed: {exc}", file=sys.stderr)
        return False, ""
    if status == 201 and isinstance(data, dict) and data.get("agent_token"):
        return True, str(data["agent_token"])
    code = ""
    if isinstance(data, dict):
        code = str((data.get("error") or {}).get("code", ""))
    print(f"[nexusops-agent] enrollment rejected (HTTP {status}) {code}".strip(), file=sys.stderr)
    return False, ""


def _process_pending_operations(
    client: "AgentClient",
    pending: list,
    capabilities: dict,
) -> None:
    """Claim, execute and report operations — strictly one at a time."""
    for raw_id in pending[:5]:
        operation_id = str(raw_id)
        try:
            status, claim = client.request("POST", f"/agent/operations/{operation_id}/claim")
        except (OSError, http.client.HTTPException) as exc:
            print(f"[nexusops-agent] claim failed: {exc}", file=sys.stderr)
            return
        if status != 200:
            # Lost the CAS to another heartbeat, or it expired: not an error.
            continue
        op_type = str(claim.get("type", ""))
        deadline = None
        raw_deadline = claim.get("execution_deadline")
        if isinstance(raw_deadline, str):
            try:
                deadline = datetime.fromisoformat(raw_deadline).timestamp()
            except ValueError:
                deadline = None
        ok, output, error_code, error_message = execute_operation(
            op_type,
            claim.get("params", {}),
            deadline=deadline,
            capabilities=capabilities,
        )
        body: dict = {"ok": ok, "output": output}
        if error_code:
            body["error_code"] = error_code
        if error_message:
            body["error_message"] = error_message
        try:
            client.request("POST", f"/agent/operations/{operation_id}/result", body)
        except (OSError, http.client.HTTPException) as exc:
            # Uncertain execution outcome: the control plane will expire the row
            # rather than re-deliver it, so a possibly-executed action is never
            # run twice.
            print(f"[nexusops-agent] result report failed: {exc}", file=sys.stderr)
            return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NexusOps host agent")
    parser.add_argument("--server", default=os.environ.get("NEXUSOPS_SERVER", ""),
                        help="Base URL of the NexusOps server")
    parser.add_argument("--token", default=os.environ.get("NEXUSOPS_TOKEN", ""),
                        help="Node token (nxa_...) or one-time enrollment token (nxk_...)")
    parser.add_argument("--token-file", default=os.environ.get("NEXUSOPS_TOKEN_FILE", DEFAULT_TOKEN_FILE),
                        help="Where the enrolled node credential is stored (0600)")
    parser.add_argument("--ca-bundle", default=os.environ.get("NEXUSOPS_CA_BUNDLE", ""),
                        help="PEM CA file to trust for the control plane (private CA)")
    parser.add_argument("--interval", type=int, default=int(os.environ.get("NEXUSOPS_INTERVAL", "30")),
                        help="Heartbeat interval seconds (>=5)")
    parser.add_argument("--once", action="store_true", help="Send one hello + heartbeat, then exit")
    args = parser.parse_args(argv)

    # Credential precedence: explicit --token/env, then the persisted file. The
    # file matters for restarts: a rotated or newly enrolled credential survives
    # a service restart without re-running the installer.
    explicit = args.token.strip()
    stored = read_token_file(args.token_file)
    # A re-run of the installer passes the same one-time nxk_ token again; once a
    # node credential exists it wins, so a restart never burns the enrollment
    # token twice (which the server would refuse anyway).
    if explicit.startswith("nxk_") and stored.startswith("nxa_"):
        token = stored
    else:
        token = explicit or stored
    if not args.server or not token:
        parser.error(
            "--server and --token are required (or set NEXUSOPS_SERVER/NEXUSOPS_TOKEN, "
            "or enroll into NEXUSOPS_TOKEN_FILE)"
        )
    interval = max(args.interval, 5)

    ca_bundle = args.ca_bundle or None
    # A non-loopback plain-HTTP URL (or an unloadable CA bundle) is refused here,
    # before any credential is built or sent. Fail clearly and non-zero rather
    # than with a traceback, and never fall back to an unverified transport.
    try:
        client = AgentClient(args.server, token, ca_bundle=ca_bundle)
    except (ValueError, OSError) as exc:
        print(f"[nexusops-agent] refusing to start: {exc}", file=sys.stderr)
        return 2

    # Enrollment: an nxk_ token is exchanged once for this node's own credential.
    if token.startswith("nxk_"):
        ok, node_token = _enroll(client, token)
        if not ok:
            if args.once:
                return 1
            print("[nexusops-agent] enrollment failed; nothing to do until re-enrolled",
                  file=sys.stderr)
            return 1
        client.token = node_token
        persist_token(args.token_file, node_token)
        print("[nexusops-agent] enrolled; credential stored", file=sys.stderr)

    capabilities: dict = {}
    heartbeat_body: dict = {}

    # Hello: register/enroll, receive authoritative intervals and negotiate.
    hello_payload = _build_hello_payload()
    capabilities = hello_payload.get("capabilities", {})
    revoked_warned = False
    while not _STOP["flag"]:
        try:
            status, data = client.request("POST", "/agent/hello", hello_payload)
        except (OSError, http.client.HTTPException) as exc:
            print(f"[nexusops-agent] server unreachable: {exc}", file=sys.stderr)
            return 1
        if status == 200:
            break
        if status == 401:
            # A rejected token is not a transient failure: park, don't exit.
            revoked_warned = _warn_revoked(revoked_warned)
            if args.once:
                return 1
            _interruptible_sleep(REVOKED_POLL_SECONDS)
            continue
        print(f"[nexusops-agent] enrollment rejected (HTTP {status}): "
              f"{data.get('error', {}).get('code', 'unknown')}", file=sys.stderr)
        return 1
    if _STOP["flag"]:
        return 0  # shutdown requested while parked in the revoked cadence
    interval = max(int(data.get("heartbeat_interval_seconds", interval)), 5)
    negotiated = int(data.get("protocol_version", 1))
    print(f"[nexusops-agent] enrolled as '{data.get('name', '?')}'; "
          f"protocol v{negotiated}; heartbeating every {interval}s", file=sys.stderr)

    prev_cpu = None
    prev_container_cpu: dict[str, tuple[float, float]] = {}
    failures = 0
    rotation_applied = False
    while not _STOP["flag"]:
        try:
            payload, prev_cpu, prev_container_cpu = build_heartbeat(prev_cpu, prev_container_cpu)
            payload = dict(payload)
            if rotation_applied:
                payload["rotation_applied"] = True
            status, body = client.request("POST", "/agent/heartbeat", payload)
            if status in (200, 204):
                failures = 0
                rotation_applied = False
                if status == 200 and isinstance(body, dict):
                    rotation = body.get("token_rotation")
                    if isinstance(rotation, dict) and rotation.get("token"):
                        # Persist atomically, then acknowledge on the next beat.
                        if persist_token(args.token_file, str(rotation["token"])):
                            client.token = str(rotation["token"])
                            rotation_applied = True
                            print("[nexusops-agent] credential rotated", file=sys.stderr)
                    pending = body.get("pending_operations") or []
                    if isinstance(pending, list) and pending:
                        _process_pending_operations(client, pending, capabilities)
            elif status == 401:
                # Revoked/rotated-away token: park instead of exiting (see
                # REVOKED_POLL_SECONDS). Retrying is not pointless — a server
                # misconfiguration that 401s transiently heals on its own —
                # but a genuine revocation needs a re-enroll, which the
                # operator is told about once per state entry.
                revoked_warned = _warn_revoked(revoked_warned)
                failures = 0
                if args.once:
                    return 1
                _interruptible_sleep(REVOKED_POLL_SECONDS)
                continue
            else:
                failures += 1
        except (OSError, http.client.HTTPException) as exc:
            failures += 1
            print(f"[nexusops-agent] heartbeat failed ({failures}): {exc}", file=sys.stderr)
        if args.once:
            break
        backoff = min(interval * (2 ** min(failures, 4)), 300) if failures else interval
        deadline = time.monotonic() + backoff
        while not _STOP["flag"] and time.monotonic() < deadline:
            time.sleep(0.5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
