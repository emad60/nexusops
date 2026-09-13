#!/usr/bin/env python3
"""NexusOps host agent.

Reports CPU/memory/disk/load metrics and Docker container state to a NexusOps
server. Python 3 standard library only — no pip dependencies — so it runs on
any machine that has ``python3``.

Usage:
    python3 nexusops_agent.py --server https://nexusops.example.com \
        --token nxa_... [--interval 30] [--once] [--insecure] [--allow-insecure-transport]

Environment overrides: NEXUSOPS_SERVER, NEXUSOPS_TOKEN, NEXUSOPS_INTERVAL.

The agent only ever *reports* state. It never executes commands received from
the server; the server cannot run arbitrary code on this host through the
agent (see docs/agent.md).
"""

from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import os
import shutil
import signal
import socket
import ssl
import sys
import time
import urllib.parse

AGENT_VERSION = "1.0.0"

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


# --- Docker container observation (HTTP over the docker socket) ---------------


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: str) -> None:
        super().__init__("localhost")
        self._socket_path = socket_path

    def connect(self) -> None:  # noqa: D102 - http.client contract
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)
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


def _docker_request(method: str, path: str, timeout: float = 5.0) -> tuple[int, dict | list | None]:
    last_error: Exception | None = None
    for sock_path in _DOCKER_SOCKETS:
        if not os.path.exists(sock_path):
            continue
        conn = _UnixHTTPConnection(sock_path)
        try:
            conn.request(method, path, headers={"Host": "docker"})
            resp = conn.getresponse()
            body = resp.read()
            status = resp.status
            parsed = json.loads(body.decode("utf-8")) if body and status == 200 else None
            return status, parsed
        except (OSError, http.client.HTTPException, ValueError) as exc:
            last_error = exc
            continue
        finally:
            try:
                conn.close()
            except Exception:
                pass
    raise OSError(f"docker socket unreachable: {last_error or 'not found'}")


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


# --- Server transport ----------------------------------------------------------


class AgentClient:
    def __init__(
        self,
        server_url: str,
        token: str,
        insecure: bool = False,
        allow_insecure_transport: bool = False,
    ) -> None:
        parsed = urllib.parse.urlparse(server_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError(f"invalid server URL: {server_url!r}")
        self.use_tls = parsed.scheme == "https"
        self.host = parsed.hostname
        self.port = parsed.port or (443 if self.use_tls else 80)
        self.base_path = parsed.path.rstrip("/")
        self.token = token
        self._ctx = None
        if self.use_tls:
            self._ctx = (
                ssl._create_unverified_context()  # noqa: S323 - opt-in via --insecure
                if insecure
                else ssl.create_default_context()
            )
        else:
            self._warn_insecure_transport(allow_insecure_transport)

    def _warn_insecure_transport(self, allowed: bool) -> None:
        """Flag plain-HTTP transports that expose the enrollment token.

        The X-Agent-Token header authenticates every hello/heartbeat; over
        plain HTTP any passive observer on the path captures it and gains a
        permanent data-injection credential. Loopback/link-local targets are
        exempt. Pass --allow-insecure-transport to acknowledge the risk.
        """
        if allowed:
            return
        host = self.host or ""
        try:
            addr = ipaddress.ip_address(host)
            local = addr.is_loopback or addr.is_link_local
        except ValueError:
            local = host.lower() in ("localhost", "localhost.")
        if local:
            return
        print(
            f"[nexusops-agent] WARNING: sending the enrollment token over plain "
            f"HTTP to {self.host}:{self.port} — anyone on the network path can "
            f"read it and impersonate this server. Terminate TLS at your edge "
            f"and use an https:// URL, or pass --allow-insecure-transport to "
            f"silence this warning.",
            file=sys.stderr,
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
    payload = {
        "cpu_percent": cpu,
        "mem_used_mb": mem_used_mb,
        "mem_percent": mem_percent,
        "disk_used_gb": disk_used_gb,
        "disk_percent": disk_percent,
        "net_rx_kb_s": 0.0,
        "net_tx_kb_s": 0.0,
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NexusOps host agent")
    parser.add_argument("--server", default=os.environ.get("NEXUSOPS_SERVER", ""),
                        help="Base URL of the NexusOps server")
    parser.add_argument("--token", default=os.environ.get("NEXUSOPS_TOKEN", ""),
                        help="Agent enrollment token (nxa_...)")
    parser.add_argument("--interval", type=int, default=int(os.environ.get("NEXUSOPS_INTERVAL", "30")),
                        help="Heartbeat interval seconds (>=5)")
    parser.add_argument("--once", action="store_true", help="Send one hello + heartbeat, then exit")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS verification (testing only)")
    parser.add_argument("--allow-insecure-transport", action="store_true",
                        help="Silence the plain-HTTP token-exposure warning (non-loopback http://)")
    args = parser.parse_args(argv)

    if not args.server or not args.token:
        parser.error("--server and --token are required (or set NEXUSOPS_SERVER/NEXUSOPS_TOKEN)")
    interval = max(args.interval, 5)

    import platform

    client = AgentClient(
        args.server,
        args.token,
        insecure=args.insecure,
        allow_insecure_transport=args.allow_insecure_transport,
    )

    # Hello: register/enroll, receive authoritative intervals.
    usage = shutil.disk_usage("/")
    os_name, os_version = os_info()
    hello_payload = {
        "agent_version": AGENT_VERSION,
        "os_name": os_name,
        "os_version": os_version,
        "arch": platform.machine(),
        "cpu_cores": os.cpu_count() or 1,
        "memory_total_mb": memory_total_mb(),
        "disk_total_gb": int(usage.total / 1024**3),
        "hostname": socket.gethostname(),
    }
    try:
        status, data = client.request("POST", "/agent/hello", hello_payload)
    except (OSError, http.client.HTTPException) as exc:
        print(f"[nexusops-agent] server unreachable: {exc}", file=sys.stderr)
        return 1
    if status != 200:
        print(f"[nexusops-agent] enrollment rejected (HTTP {status}): "
              f"{data.get('error', {}).get('code', 'unknown')}", file=sys.stderr)
        return 1
    interval = max(int(data.get("heartbeat_interval_seconds", interval)), 5)
    print(f"[nexusops-agent] enrolled as '{data.get('name', '?')}'; "
          f"heartbeating every {interval}s", file=sys.stderr)

    prev_cpu = None
    prev_container_cpu: dict[str, tuple[float, float]] = {}
    failures = 0
    while not _STOP["flag"]:
        try:
            payload, prev_cpu, prev_container_cpu = build_heartbeat(prev_cpu, prev_container_cpu)
            status, _ = client.request("POST", "/agent/heartbeat", payload)
            if status == 204:
                failures = 0
            elif status == 401:
                print("[nexusops-agent] token rejected by server; exiting", file=sys.stderr)
                return 1
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
