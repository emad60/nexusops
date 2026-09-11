"""Container schemas: list/detail read models, log entries, action results."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import APIModel, OutModel


class HostRef(APIModel):
    """Summary of the docker host a container runs on."""

    id: UUID
    name: str
    status: str


class ServerRef(APIModel):
    """Summary of the server associated with a container."""

    id: UUID
    name: str
    status: str


class ContainerOut(APIModel):
    """Container row as exposed on list endpoints.

    ``env_keys`` carries environment variable NAMES only — values never leave
    the database.
    """

    id: UUID
    container_id: str
    name: str
    image_ref: str
    status: str
    health: str
    env_keys: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    ports: list[dict[str, Any]] = Field(default_factory=list)
    restart_count: int = 0

    cpu_percent: float | None = None
    mem_used_mb: float | None = None
    mem_limit_mb: float | None = None
    net_rx_kb_s: float | None = None
    net_tx_kb_s: float | None = None

    started_at: datetime | None = None
    finished_at: datetime | None = None
    observed_at: datetime | None = None
    simulated: bool = False

    host: HostRef | None = None
    server: ServerRef | None = None


class ContainerDetailOut(ContainerOut):
    """Full view: adds command line and mount table."""

    command: str = ""
    mounts: list[dict[str, Any]] = Field(default_factory=list)


class LogEntryOut(APIModel):
    """One persisted log record (keyset-paginated)."""

    id: int
    ts: datetime
    stream: str
    level: str
    message: str


class ContainerRemoveOut(APIModel):
    """Acknowledgement of a destructive removal."""

    id: UUID
    removed: bool = True


def host_ref(row_id: UUID | None, name: str | None, status: str | None) -> HostRef | None:
    if row_id is None:
        return None
    return HostRef(id=row_id, name=name or "", status=status or "UNKNOWN")


def server_ref(row_id: UUID | None, name: str | None, status: str | None) -> ServerRef | None:
    if row_id is None:
        return None
    return ServerRef(id=row_id, name=name or "", status=status or "UNKNOWN")


# OutModel kept available for future timestamped container sub-resources.
__all__ = [
    "ContainerDetailOut",
    "ContainerOut",
    "ContainerRemoveOut",
    "HostRef",
    "LogEntryOut",
    "OutModel",
    "ServerRef",
    "host_ref",
    "server_ref",
]
