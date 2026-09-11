"""Simulated docker provider for demo and test environments.

The provider is **stateless with respect to persistence**: the service layer
resolves ORM rows and registers them here (``register_container`` /
``register_log_rows``) before calling protocol methods. Mutating operations
only touch the in-memory row objects; the service commits them.

Deterministic pseudo-randomness is derived from SHA-256 of the host id so
image/volume/network listings stay stable across calls and restarts.
"""

from __future__ import annotations

import hashlib
import math
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from app.models import Container, LogEntry
from app.models.enums import ContainerStatus
from app.providers.base import (
    ContainerInfo,
    ContainerStats,
    DockerProviderError,
    LogLine,
)

_IMAGE_WORDS = ("web", "api", "worker", "cache", "queue", "proxy", "db", "cron")
_ARCHES = ("amd64", "arm64")


def _seed_int(*parts: str) -> int:
    digest = hashlib.sha256(":".join(parts).encode()).digest()
    return int.from_bytes(digest[:8], "big")


class SimulatedDockerProvider:
    """Implements :class:`DockerProvider` semantics against DB rows."""

    kind = "simulated"

    def __init__(self, host_id: str) -> None:
        self._host_id = str(host_id)
        self._rows: dict[str, Container] = {}
        self._log_rows: dict[str, list[LogEntry]] = {}

    # --- registration (called by services, never by routers) ---------------

    def register_container(self, row: Container) -> None:
        """Make a container row visible to this provider instance."""
        self._rows[row.container_id] = row

    def register_containers(self, rows: list[Container]) -> None:
        for row in rows:
            self.register_container(row)

    def register_log_rows(self, cid: str, rows: list[LogEntry]) -> None:
        """Attach already-fetched log rows so ``logs()`` can replay them."""
        self._log_rows[cid] = list(rows)

    # --- internals ---------------------------------------------------------

    def _resolve(self, cid: str) -> Container:
        if cid in self._rows:
            return self._rows[cid]
        matches = [r for key, r in self._rows.items() if key.startswith(cid)]
        if len(matches) == 1:
            return matches[0]
        raise DockerProviderError("container not found")

    def _info_from_row(self, row: Container) -> ContainerInfo:
        status = getattr(row.status, "value", str(row.status)).lower()
        health = getattr(row.health, "value", str(row.health)).lower()
        return ContainerInfo(
            id=row.container_id,
            name=row.name,
            image_ref=row.image_ref,
            command=row.command,
            status=status,
            health=health,
            ports=list(row.ports or []),
            env_keys=list(row.env_keys or []),
            labels=dict(row.labels or {}),
            mounts=list(row.mounts or []),
            started_at=row.started_at,
            restart_count=row.restart_count,
        )

    # --- protocol ---------------------------------------------------------

    def ping(self) -> bool:
        return True

    def list_containers(self, include_stopped: bool = True) -> list[ContainerInfo]:
        infos = [self._info_from_row(r) for r in self._rows.values()]
        if include_stopped:
            return infos
        return [i for i in infos if i.status == "running"]

    def inspect(self, cid: str) -> ContainerInfo:
        return self._info_from_row(self._resolve(cid))

    def start(self, cid: str) -> None:
        now = datetime.now(UTC)
        row = self._resolve(cid)
        row.status = ContainerStatus.RUNNING
        row.started_at = now
        row.finished_at = None
        row.observed_at = now

    def stop(self, cid: str, timeout: int = 10) -> None:
        now = datetime.now(UTC)
        row = self._resolve(cid)
        row.status = ContainerStatus.EXITED
        row.finished_at = now
        row.observed_at = now

    def restart(self, cid: str, timeout: int = 10) -> None:
        now = datetime.now(UTC)
        row = self._resolve(cid)
        row.status = ContainerStatus.RUNNING
        row.restart_count = (row.restart_count or 0) + 1
        row.started_at = now
        row.finished_at = None
        row.observed_at = now

    def pause(self, cid: str) -> None:
        row = self._resolve(cid)
        row.status = ContainerStatus.PAUSED
        row.observed_at = datetime.now(UTC)

    def unpause(self, cid: str) -> None:
        row = self._resolve(cid)
        row.status = ContainerStatus.RUNNING
        row.observed_at = datetime.now(UTC)

    def remove(self, cid: str, force: bool = False) -> None:
        row = self._resolve(cid)
        status = getattr(row.status, "value", str(row.status))
        if not force and status == "RUNNING":
            raise DockerProviderError("cannot remove running container without force")
        row.status = ContainerStatus.REMOVED
        row.finished_at = datetime.now(UTC)
        row.observed_at = datetime.now(UTC)

    def stats(self, cid: str) -> ContainerStats:
        """Plausible numbers derived from the row plus time-based sine noise."""
        row = self._resolve(cid)
        status = getattr(row.status, "value", str(row.status))
        seed = _seed_int(self._host_id, str(row.id))
        t = time.time()
        active = 0.0 if status != "RUNNING" else 1.0

        cpu = round(active * (6.0 + 5.0 * abs(math.sin(t / 41 + (seed % 100) / 15))), 2)
        mem_limit_mb = float(row.mem_limit_mb or 512.0)
        base_frac = 0.25 + 0.15 * abs(math.sin(t / 97 + (seed % 53) / 17))
        mem_used_mb = round(mem_limit_mb * min(base_frac + 0.05 * active, 0.95), 2)
        net_rx = round(active * abs(math.sin(t / 23 + (seed % 71) / 11)) * 120.0, 2)
        net_tx = round(active * abs(math.sin(t / 19 + (seed % 89) / 13)) * 80.0, 2)
        return ContainerStats(
            cpu_percent=cpu,
            mem_used_mb=mem_used_mb,
            mem_limit_mb=round(mem_limit_mb, 2),
            net_rx_kb_s=net_rx,
            net_tx_kb_s=net_tx,
        )

    def images(self) -> list[dict[str, Any]]:
        count = 4 + _seed_int(self._host_id, "images") % 5
        result: list[dict[str, Any]] = []
        for i in range(count):
            sub_seed = _seed_int(self._host_id, "images", str(i))
            name = f"nexus/{_IMAGE_WORDS[sub_seed % len(_IMAGE_WORDS)]}-{i}:1.{sub_seed % 9}"
            result.append(
                {
                    "id": f"sha256:{sub_seed:016x}{i:016x}",
                    "repo_tags": [name],
                    "size_bytes": (50 + sub_seed % 900) * 1024 * 1024,
                    "architecture": _ARCHES[sub_seed % len(_ARCHES)],
                }
            )
        return result

    def volumes(self) -> list[dict[str, Any]]:
        count = 2 + _seed_int(self._host_id, "volumes") % 4
        result: list[dict[str, Any]] = []
        for i in range(count):
            sub_seed = _seed_int(self._host_id, "volumes", str(i))
            name = f"{_IMAGE_WORDS[sub_seed % len(_IMAGE_WORDS)]}_data_{i}"
            result.append(
                {
                    "name": name,
                    "driver": "local",
                    "mountpoint": f"/var/lib/docker/volumes/{name}/_data",
                }
            )
        return result

    def networks(self) -> list[dict[str, Any]]:
        result = [
            {"name": "bridge", "driver": "bridge", "scope": "local"},
            {"name": "host", "driver": "host", "scope": "local"},
            {"name": "none", "driver": "null", "scope": "local"},
        ]
        extra_seed = _seed_int(self._host_id, "networks")
        result.append(
            {
                "name": f"nexus_net_{extra_seed % 7}",
                "driver": "bridge",
                "scope": "local",
            }
        )
        return result

    def logs(
        self,
        cid: str,
        tail: int = 500,
        follow: bool = False,
        since: datetime | None = None,
    ) -> Iterator[LogLine]:
        """Replay registered LogEntry rows ordered by ts (tail N).

        ``follow`` is ignored here — live tailing for simulated containers is
        handled by the service via Redis pub/sub.
        """
        rows = sorted(self._log_rows.get(cid, []), key=lambda r: (r.ts, r.id))
        if since is not None:
            since_utc = since if since.tzinfo else since.replace(tzinfo=UTC)
            rows = [r for r in rows if r.ts >= since_utc]
        replay = rows[-tail:] if tail and tail > 0 else rows
        return iter(
            [
                LogLine(
                    ts=r.ts,
                    stream=r.stream or "stdout",
                    message=r.message,
                )
                for r in replay
            ]
        )
