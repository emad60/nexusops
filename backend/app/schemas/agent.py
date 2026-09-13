"""Agent-facing schemas. Payloads are data only — never executed."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import ContainerHealth, ContainerStatus
from app.schemas.base import APIModel

#: Heartbeat container statuses (REMOVED never arrives over the wire).
_ALLOWED_CONTAINER_STATUSES = frozenset(
    {"RUNNING", "EXITED", "PAUSED", "CREATED", "RESTARTING", "DEAD"}
)


class AgentHelloIn(APIModel):
    """First contact from an agent after enrollment; fills static host facts."""

    agent_version: str = Field(min_length=1, max_length=48)
    os_name: str = Field(default="", max_length=96)
    os_version: str = Field(default="", max_length=96)
    arch: str = Field(default="", max_length=32)
    cpu_cores: int = Field(default=0, ge=0, le=4096)
    memory_total_mb: int = Field(default=0, ge=0, le=100_000_000)
    disk_total_gb: int = Field(default=0, ge=0, le=100_000_000)
    hostname: str = Field(min_length=1, max_length=255)


class AgentHelloOut(APIModel):
    """Tells the agent how often to report."""

    server_id: UUID
    name: str
    heartbeat_interval_seconds: int
    offline_after_seconds: int | None


class AgentContainerIn(APIModel):
    """Observed container state reported by an agent."""

    container_id: str = Field(
        min_length=1,
        max_length=72,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$",
    )
    name: str = Field(min_length=1, max_length=200)
    status: ContainerStatus
    health: ContainerHealth | None = None
    image_ref: str = Field(default="", max_length=300)
    restart_count: int = Field(default=0, ge=0, le=1_000_000)
    cpu_percent: float | None = Field(default=None, ge=0, le=10_000)
    mem_used_mb: float | None = Field(default=None, ge=0)
    mem_limit_mb: float | None = Field(default=None, ge=0)

    @field_validator("status")
    @classmethod
    def _check_status(cls, value: ContainerStatus) -> ContainerStatus:
        if value.value not in _ALLOWED_CONTAINER_STATUSES:
            raise ValueError(f"Unsupported container status: {value.value}")
        return value


class AgentHeartbeatIn(APIModel):
    """Periodic metrics + observed containers from an enrolled agent."""

    cpu_percent: float = Field(ge=0, le=100)
    mem_used_mb: float = Field(ge=0)
    mem_percent: float = Field(ge=0, le=100)
    disk_used_gb: float = Field(ge=0)
    disk_percent: float = Field(ge=0, le=100)
    net_rx_kb_s: float = Field(default=0, ge=0)
    net_tx_kb_s: float = Field(default=0, ge=0)
    load1: float = Field(default=0, ge=0, le=10_000)
    uptime_seconds: int = Field(default=0, ge=0, le=10_000_000_000)
    os_name: str | None = Field(default=None, max_length=96)
    arch: str | None = Field(default=None, max_length=32)
    containers: list[AgentContainerIn] = Field(default_factory=list, max_length=200)
