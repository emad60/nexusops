"""Provider abstraction for docker hosts (real daemon or simulated).

Providers are deliberately **synchronous** — the docker SDK blocks. Services
offload every call with ``asyncio.to_thread`` so the event loop never stalls.

Errors raised towards services are always :class:`DockerProviderError` with a
sanitized message: HTTP status/reason only, never response bodies, env values,
labels, or the endpoint URL itself.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol

#: Actions supported on a running container.
ContainerAction = Literal["start", "stop", "restart", "pause", "unpause"]

_ERROR_SNIPPET = 160
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class DockerProviderError(Exception):
    """A provider operation failed. ``str()`` is safe to show/log."""


def sanitize_error(exc: Exception) -> str:
    """Build a compact, secret-free description of a provider failure.

    Only the exception class name, HTTP status code and reason phrase are
    kept — response bodies may contain environment values or label contents
    and are therefore dropped.
    """
    status_code = getattr(exc, "status_code", None)
    reason = getattr(getattr(exc, "response", None), "reason", None)
    parts = [type(exc).__name__]
    if isinstance(status_code, int):
        parts.append(f"HTTP {status_code}")
    if reason:
        parts.append(str(reason)[:80])
    return _CONTROL_CHARS.sub(" ", " ".join(parts))[:_ERROR_SNIPPET]


def clip(text: str, limit: int = 480) -> str:
    """Truncate *text* to *limit* characters, stripping control chars."""
    return _CONTROL_CHARS.sub(" ", text or "")[:limit]


@dataclass(slots=True)
class ContainerInfo:
    """Normalized view of a container as reported by any provider."""

    id: str
    name: str
    image_ref: str
    command: str
    status: str
    health: str
    ports: list[dict[str, Any]]
    env_keys: list[str]
    labels: dict[str, str]
    mounts: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime | None = None
    restart_count: int = 0


@dataclass(slots=True)
class ContainerStats:
    """Point-in-time resource usage snapshot."""

    cpu_percent: float
    mem_used_mb: float
    mem_limit_mb: float
    net_rx_kb_s: float
    net_tx_kb_s: float


@dataclass(slots=True)
class LogLine:
    """One parsed log record from a container log stream."""

    ts: datetime
    stream: str = "stdout"
    message: str = ""


class DockerProvider(Protocol):
    """Structural interface implemented by real and simulated providers."""

    kind: str

    def ping(self) -> bool:
        """Return True when the remote daemon answers."""
        ...

    def list_containers(self, include_stopped: bool = True) -> list[ContainerInfo]:
        """List containers visible to the provider."""
        ...

    def inspect(self, cid: str) -> ContainerInfo:  # pragma: no cover - protocol
        """Inspect a single container by id (short ids allowed)."""
        ...

    def start(self, cid: str) -> None:  # pragma: no cover - protocol
        ...

    def stop(self, cid: str, timeout: int = 10) -> None:  # pragma: no cover - protocol
        ...

    def restart(self, cid: str, timeout: int = 10) -> None:  # pragma: no cover - protocol
        ...

    def pause(self, cid: str) -> None:  # pragma: no cover - protocol
        ...

    def unpause(self, cid: str) -> None:  # pragma: no cover - protocol
        ...

    def remove(self, cid: str, force: bool = False) -> None:  # pragma: no cover - protocol
        ...

    def stats(self, cid: str) -> ContainerStats:  # pragma: no cover - protocol
        ...

    def images(self) -> list[dict[str, Any]]:
        """List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``."""
        ...

    def volumes(self) -> list[dict[str, Any]]:
        """List volumes: keys ``name``, ``driver``, ``mountpoint``."""
        ...

    def networks(self) -> list[dict[str, Any]]:
        """List networks: keys ``name``, ``driver``, ``scope``."""
        ...

    def logs(
        self,
        cid: str,
        tail: int = 500,
        follow: bool = False,
        since: datetime | None = None,
    ) -> Iterator[LogLine]:
        """Yield parsed log lines. With ``follow=True`` the stream never ends."""
        ...
