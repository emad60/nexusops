"""Real docker provider backed by the docker SDK against a live daemon.

Every SDK call is retried once (short wait) via tenacity and converted to
:class:`DockerProviderError` with a sanitized message. The endpoint URL and
any response body content never appear in errors.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import Any, TypeVar

import docker
import requests
from docker.tls import TLSConfig
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.providers.base import (
    ContainerInfo,
    ContainerStats,
    DockerProviderError,
    LogLine,
    sanitize_error,
)

T = TypeVar("T")

# RFC3339 timestamp as emitted by the docker daemon with timestamps=True,
# e.g. 2026-08-23T10:11:12.123456789Z (nanosecond precision).
_LOG_LINE_RE = re.compile(r"^(?P<ts>\S+)\s?(?P<msg>.*)$", re.DOTALL)
_TS_RE = re.compile(
    r"^(?P<d>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(?P<frac>\d+))?"
    r"(?P<tz>Z|[+-]\d{2}:?\d{2})?$"
)


def parse_rfc3339(raw: str) -> datetime | None:
    """Parse a daemon RFC3339 timestamp; naive values are assumed UTC."""
    match = _TS_RE.match(raw.strip())
    if match is None:
        return None
    frac = (match.group("frac") or "")[:6].ljust(6, "0")
    tz = match.group("tz") or "Z"
    if tz == "Z":
        tz = "+00:00"
    try:
        parsed = datetime.fromisoformat(f"{match.group('d')}.{frac}{tz}")
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_log_line(raw: bytes | str) -> LogLine | None:
    """Split one raw log record into a :class:`LogLine`."""
    text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
    text = text.rstrip("\r\n")
    if not text.strip():
        return None
    match = _LOG_LINE_RE.match(text)
    if match is None:
        return LogLine(ts=datetime.now(UTC), message=text[:8000])
    ts = parse_rfc3339(match.group("ts"))
    if ts is None:
        return LogLine(ts=datetime.now(UTC), message=text[:8000])
    return LogLine(ts=ts, message=match.group("msg")[:8000])


class RealDockerProvider:
    """Talks to a real docker daemon over ``unix://`` or ``tcp://``."""

    kind = "real"

    def __init__(
        self,
        endpoint_url: str,
        *,
        tls_verify: bool = True,
        timeout: float = 10.0,
    ) -> None:
        # Pin the API version so constructing the client performs NO network
        # I/O (docker-py would otherwise negotiate /version eagerly); reachability
        # is surfaced by ping()/first call as a DockerProviderError instead.
        kwargs: dict[str, Any] = {
            "base_url": endpoint_url,
            "timeout": timeout,
            "version": docker.constants.DEFAULT_DOCKER_API_VERSION,
        }
        if not tls_verify:
            # Skip certificate verification for self-managed daemons.
            kwargs["tls"] = TLSConfig(verify=False)
        try:
            self._client = docker.DockerClient(**kwargs)
        except DockerProviderError:
            raise
        except Exception as exc:  # malformed TLS config and friends
            raise DockerProviderError(sanitize_error(exc)) from exc
        self._retrying = Retrying(
            retry=retry_if_exception_type((docker.errors.APIError, requests.RequestException)),
            stop=stop_after_attempt(2),
            wait=wait_fixed(0.25),
            reraise=True,
        )

    # --- plumbing ---------------------------------------------------------

    def _run(self, op: Callable[[], T]) -> T:
        """Execute an SDK call with one short retry, normalizing failures."""
        try:
            return self._retrying(op)
        except DockerProviderError:
            raise
        except (docker.errors.APIError, docker.errors.DockerException) as exc:
            raise DockerProviderError(sanitize_error(exc)) from exc
        except (requests.RequestException, OSError) as exc:
            raise DockerProviderError("Docker daemon unreachable") from exc

    @staticmethod
    def _info(attrs: dict[str, Any]) -> ContainerInfo:
        config = attrs.get("Config") or {}
        state = attrs.get("State") or {}
        health = ((state.get("Health") or {}).get("Status")) or "none"
        env_keys = [entry.partition("=")[0] for entry in (config.get("Env") or []) if entry]
        command = " ".join(config.get("Cmd") or config.get("Entrypoint") or [])
        started_raw = state.get("StartedAt")
        ports_raw = (attrs.get("NetworkSettings") or {}).get("Ports") or {}
        ports = []
        for container_port, bindings in ports_raw.items():
            for binding in bindings or [None]:
                ports.append(
                    {
                        "private_port": container_port,
                        "public_port": (binding or {}).get("HostPort"),
                        "public_ip": (binding or {}).get("HostIp"),
                        "type": container_port.rpartition("/")[2],
                    }
                )
        mounts = [
            {
                "source": m.get("Source") or "",
                "destination": m.get("Destination") or "",
                "mode": m.get("Mode") or "",
                "rw": bool(m.get("RW", True)),
                "type": m.get("Type") or "",
            }
            for m in (attrs.get("Mounts") or [])
        ]
        return ContainerInfo(
            id=str(attrs.get("Id", "")),
            name=str((attrs.get("Name") or "").lstrip("/")),
            image_ref=str(config.get("Image") or ""),
            command=command[:500],
            status=str(state.get("Status") or "created").lower(),
            health=str(health).lower(),
            ports=ports,
            env_keys=env_keys,
            labels={str(k): str(v) for k, v in (config.get("Labels") or {}).items()},
            mounts=mounts,
            started_at=parse_rfc3339(started_raw) if started_raw else None,
            restart_count=int(state.get("RestartCount") or 0),
        )

    # --- protocol ---------------------------------------------------------

    def ping(self) -> bool:
        return bool(self._run(self._client.ping))

    def list_containers(self, include_stopped: bool = True) -> list[ContainerInfo]:
        containers = self._run(lambda: self._client.containers.list(all=include_stopped))
        return [self._info(c.attrs) for c in containers]

    def inspect(self, cid: str) -> ContainerInfo:
        container = self._run(lambda: self._client.containers.get(cid))
        attrs = self._run(lambda: container.attrs)
        return self._info(attrs)

    def start(self, cid: str) -> None:
        container = self._run(lambda: self._client.containers.get(cid))
        self._run(container.start)

    def stop(self, cid: str, timeout: int = 10) -> None:
        container = self._run(lambda: self._client.containers.get(cid))
        self._run(lambda: container.stop(timeout=timeout))

    def restart(self, cid: str, timeout: int = 10) -> None:
        container = self._run(lambda: self._client.containers.get(cid))
        self._run(lambda: container.restart(timeout=timeout))

    def pause(self, cid: str) -> None:
        container = self._run(lambda: self._client.containers.get(cid))
        self._run(container.pause)

    def unpause(self, cid: str) -> None:
        container = self._run(lambda: self._client.containers.get(cid))
        self._run(container.unpause)

    def remove(self, cid: str, force: bool = False) -> None:
        container = self._run(lambda: self._client.containers.get(cid))
        self._run(lambda: container.remove(force=force))

    def stats(self, cid: str) -> ContainerStats:
        """Two short samples give real cpu/net deltas without streaming."""
        container = self._run(lambda: self._client.containers.get(cid))
        first = self._run(lambda: container.stats(stream=False))
        time.sleep(0.3)
        second = self._run(lambda: container.stats(stream=False))
        return _compute_stats(first, second)

    def images(self) -> list[dict[str, Any]]:
        images = self._run(self._client.images.list)
        result = []
        for image in images:
            attrs = image.attrs or {}
            result.append(
                {
                    "id": str(attrs.get("Id", "")),
                    "repo_tags": list(attrs.get("RepoTags") or []),
                    "size_bytes": int(attrs.get("Size") or 0),
                    "architecture": str(attrs.get("Architecture") or ""),
                }
            )
        return result

    def volumes(self) -> list[dict[str, Any]]:
        volumes = self._run(lambda: self._client.volumes.list())
        return [
            {
                "name": str(v.attrs.get("Name", "")),
                "driver": str(v.attrs.get("Driver", "")),
                "mountpoint": str(v.attrs.get("Mountpoint", "")),
            }
            for v in volumes
        ]

    def networks(self) -> list[dict[str, Any]]:
        networks = self._run(self._client.networks.list)
        return [
            {
                "name": str(n.attrs.get("Name", "")),
                "driver": str(n.attrs.get("Driver", "")),
                "scope": str(n.attrs.get("Scope", "")),
            }
            for n in networks
        ]

    def logs(
        self,
        cid: str,
        tail: int = 500,
        follow: bool = False,
        since: datetime | None = None,
    ) -> Iterator[LogLine]:
        container = self._run(lambda: self._client.containers.get(cid))
        params: dict[str, Any] = {
            "stream": True,
            "follow": follow,
            "tail": tail,
            "timestamps": True,
        }
        if since is not None:
            params["since"] = int(since.timestamp())
        stream = container.logs(**params)

        def _iterate() -> Iterator[LogLine]:
            try:
                for raw in stream:
                    line = parse_log_line(raw)
                    if line is not None:
                        yield line
            except docker.errors.APIError as exc:
                raise DockerProviderError(sanitize_error(exc)) from exc
            except (requests.RequestException, OSError) as exc:
                raise DockerProviderError("Docker log stream interrupted") from exc

        return _iterate()


def _compute_stats(first: dict[str, Any], second: dict[str, Any]) -> ContainerStats:
    """Derive cpu percent and network rates from two cumulative samples."""
    elapsed = max(_sample_elapsed(first, second), 0.05)
    cpu_percent = _cpu_percent(first, second)
    rx_b, tx_b = _network_bytes(second)
    prev_rx, prev_tx = _network_bytes(first)
    mem = second.get("memory_stats") or {}
    mem_limit_mb = _as_float(mem.get("limit")) / (1024 * 1024)
    stats = mem.get("stats") or {}
    cache = _as_float(stats.get("cache")) or _as_float(stats.get("inactive_file"))
    mem_used_mb = max(_as_float(mem.get("usage")) - cache, 0.0) / (1024 * 1024)
    return ContainerStats(
        cpu_percent=round(cpu_percent, 2),
        mem_used_mb=round(mem_used_mb, 2),
        mem_limit_mb=round(mem_limit_mb, 2),
        net_rx_kb_s=round(max(rx_b - prev_rx, 0) / 1024 / elapsed, 2),
        net_tx_kb_s=round(max(tx_b - prev_tx, 0) / 1024 / elapsed, 2),
    )


def _sample_elapsed(first: dict[str, Any], second: dict[str, Any]) -> float:
    """Seconds between two samples based on daemon ``read`` epochs if present."""
    start = first.get("read") or first.get("preread")
    end = second.get("read")
    if isinstance(start, str) and isinstance(end, str):
        t0, t1 = parse_rfc3339(start), parse_rfc3339(end)
        if t0 is not None and t1 is not None:
            return max((t1 - t0).total_seconds(), 0.05)
    return 0.3


def _cpu_percent(first: dict[str, Any], second: dict[str, Any]) -> float:
    cpu_now = (second.get("cpu_stats") or {}).get("cpu_usage") or {}
    cpu_pre = (first.get("cpu_stats") or {}).get("cpu_usage") or {}
    system_now = (second.get("cpu_stats") or {}).get("system_cpu_usage") or 0
    system_pre = (first.get("cpu_stats") or {}).get("system_cpu_usage") or 0
    cpu_delta = _as_float(cpu_now.get("total_usage")) - _as_float(cpu_pre.get("total_usage"))
    system_delta = _as_float(system_now) - _as_float(system_pre)
    if system_delta <= 0 or cpu_delta < 0:
        return 0.0
    online = (second.get("cpu_stats") or {}).get("online_cpus")
    if not online:
        percpu = cpu_now.get("percpu_usage") or [1]
        online = len(percpu) or 1
    return min((cpu_delta / system_delta) * float(online) * 100.0, 100.0 * float(online))


def _network_bytes(sample: dict[str, Any]) -> tuple[float, float]:
    networks = (sample.get("networks") or {}) or {}
    rx = sum(_as_float(v.get("rx_bytes")) for v in networks.values())
    tx = sum(_as_float(v.get("tx_bytes")) for v in networks.values())
    return rx, tx


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
