"""Agent-facing schemas. Payloads are data only — never executed.

Wire protocol v2
----------------
The published contract is versioned at the **hello** exchange because ``APIModel``
sets ``extra="forbid"``: any field an agent adds that the server does not know
422s the whole request, so field growth has to be negotiated rather than
discovered. The rules pinned here:

* ``AGENT_PROTOCOL_VERSION`` is what the control plane speaks now.
* ``MIN_SUPPORTED_AGENT_PROTOCOL`` is the oldest agent it still accepts (1 —
  the pre-v2 contract). Raising this floor is a deliberate, documented break.
* A v1 agent omits ``protocol_version`` entirely and keeps receiving the v1
  heartbeat contract (204, no body). A v2 agent sends ``protocol_version: 2``,
  receives the v2 heartbeat (200 + pending operations + rotation delivery) and
  reports capabilities.
* Negotiation governs *cadence and fields only, never capability*: the agent's
  operation whitelist is compile-time, so a malicious server cannot make an old
  agent accept a new operation type.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import ContainerHealth, ContainerStatus
from app.schemas.base import APIModel

#: Wire protocol the control plane speaks.
AGENT_PROTOCOL_VERSION = 2
#: Oldest agent protocol still accepted. v1 is the pre-Phase-3 contract; its
#: heartbeat is 204 with no body, so an installed agent keeps working unchanged.
MIN_SUPPORTED_AGENT_PROTOCOL = 1
#: Bumped by the control plane when a security fix requires a newer agent. The
#: agent echoes what it learned; dispatch can refuse nodes below this.
MIN_AGENT_VERSION = "1.1.0"

#: Heartbeat container statuses (REMOVED never arrives over the wire).
_ALLOWED_CONTAINER_STATUSES = frozenset(
    {"RUNNING", "EXITED", "PAUSED", "CREATED", "RESTARTING", "DEAD"}
)

#: The agent reports at most this many containers per heartbeat (its list is
#: capped before send). Absence is only trusted for reconciliation when the
#: payload is below the cap — a truncated list says nothing about what it
#: dropped, so containers must not be treated as removed.
AGENT_CONTAINER_CAP = 50

#: Upper bound on how many capability keys a node may report. The map is a JSONB
#: blob so new capabilities do not need a column, but it must not become an
#: unbounded agent-controlled store.
CAPABILITY_MAP_MAX_KEYS = 16
#: Cap on the serialized size of the open-ended ``facts`` blob a node may report.
#: Facts are telemetry, not a data plane.
FACTS_MAX_BYTES = 8192


class CapabilityReport(APIModel):
    """One node-reported capability.

    ``present`` defaults to false, and a capability absent from the map is
    *unreported*, not "available" — dispatch treats both the same way (refuse).
    """

    present: bool = False
    version: str | None = Field(default=None, max_length=64)
    api_version: str | None = Field(default=None, max_length=32)


class AgentHelloIn(APIModel):
    """First contact from an agent after enrollment; fills static host facts."""

    agent_version: str = Field(min_length=1, max_length=48)
    #: Absent for a v1 agent. ``1`` is the honest default: unreported is treated
    #: as the oldest contract, never as "supports the new one".
    protocol_version: int = Field(default=1, ge=1, le=1000)
    os_name: str = Field(default="", max_length=96)
    os_version: str = Field(default="", max_length=96)
    arch: str = Field(default="", max_length=32)
    cpu_cores: int = Field(default=0, ge=0, le=4096)
    memory_total_mb: int = Field(default=0, ge=0, le=100_000_000)
    disk_total_gb: int = Field(default=0, ge=0, le=100_000_000)
    hostname: str = Field(min_length=1, max_length=255)
    #: v2: node-reported capabilities (see :class:`CapabilityReport`).
    capabilities: dict[str, CapabilityReport] = Field(
        default_factory=dict, max_length=CAPABILITY_MAP_MAX_KEYS
    )
    #: v2: open-ended facts (disks, network interfaces, kernel) persisted into
    #: ``servers.extra`` rather than a new column per property.
    facts: dict[str, Any] = Field(default_factory=dict)

    @field_validator("facts")
    @classmethod
    def _bound_facts(cls, value: dict[str, Any]) -> dict[str, Any]:
        import json

        try:
            encoded = json.dumps(value, default=str)
        except (TypeError, ValueError):
            raise ValueError("facts must be JSON-serializable") from None
        if len(encoded.encode("utf-8")) > FACTS_MAX_BYTES:
            raise ValueError(f"facts exceeds {FACTS_MAX_BYTES} bytes")
        if len(value) > 32:
            raise ValueError("facts may not contain more than 32 keys")
        return value


class AgentHelloOut(APIModel):
    """Tells the agent how often to report and what protocol it negotiated."""

    server_id: UUID
    name: str
    heartbeat_interval_seconds: int
    offline_after_seconds: int | None
    #: The protocol the control plane will use for this node. The agent must not
    #: accept a value below its own shipped floor.
    protocol_version: int = AGENT_PROTOCOL_VERSION
    #: Security floor the agent should self-report as out of date below.
    min_agent_version: str = MIN_AGENT_VERSION


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
    """Periodic metrics + observed containers from an enrolled agent.

    Network counters are optional and nullable: ``None`` means the agent could
    not measure them (no interface, first sample, counter reset). The platform
    must render that as *unavailable*, never as zero bytes/second — a fabricated
    zero is indistinguishable from a genuinely idle interface.
    """

    cpu_percent: float = Field(ge=0, le=100)
    mem_used_mb: float = Field(ge=0)
    mem_percent: float = Field(ge=0, le=100)
    disk_used_gb: float = Field(ge=0)
    disk_percent: float = Field(ge=0, le=100)
    net_rx_kb_s: float | None = Field(default=None, ge=0)
    net_tx_kb_s: float | None = Field(default=None, ge=0)
    load1: float = Field(default=0, ge=0, le=10_000)
    uptime_seconds: int = Field(default=0, ge=0, le=10_000_000_000)
    os_name: str | None = Field(default=None, max_length=96)
    arch: str | None = Field(default=None, max_length=32)
    #: v2: the agent acknowledges it persisted the rotated token, which ends the
    #: server-side grace window and stops re-delivery. Ignored by v1 (absent).
    rotation_applied: bool = False
    containers: list[AgentContainerIn] = Field(default_factory=list, max_length=200)


class AgentTokenRotation(APIModel):
    """A pending credential rotation, delivered on the agent's next beat.

    Served **only** to a request authenticated with the previous hash. The agent
    persists ``token`` atomically (temp file + rename + fsync) and then sends
    ``rotation_applied: true`` on a following heartbeat.
    """

    token: str
    grace_expires_at: datetime


class AgentHeartbeatOut(APIModel):
    """v2 heartbeat response: cadence, work to pull, and any pending rotation.

    A v1 agent never sees this — it receives 204 from the same route — so this
    body is additive and cannot break an installed agent.
    """

    heartbeat_interval_seconds: int
    #: Operation ids awaiting claim for **this** node. The agent claims each one
    #: (a compare-and-set); ids are hints, never authority.
    pending_operations: list[UUID] = Field(default_factory=list, max_length=20)
    token_rotation: AgentTokenRotation | None = None


# --- Enrollment (v2) ---------------------------------------------------------


class AgentEnrollIn(APIModel):
    """The first request a brand-new machine makes.

    ``enrollment_token`` is an organization-scoped, single-use ``nxk_`` token.
    The node's organization is derived from that token row — never from this
    payload — so there is deliberately no ``org_id`` field to lie about.
    """

    enrollment_token: str = Field(min_length=8, max_length=200)
    hostname: str = Field(min_length=1, max_length=255)
    agent_version: str = Field(default="", max_length=48)
    os_name: str = Field(default="", max_length=96)
    os_version: str = Field(default="", max_length=96)
    arch: str = Field(default="", max_length=32)
    cpu_cores: int = Field(default=0, ge=0, le=4096)
    memory_total_mb: int = Field(default=0, ge=0, le=100_000_000)
    disk_total_gb: int = Field(default=0, ge=0, le=100_000_000)


class AgentEnrollOut(APIModel):
    """The minimum a freshly enrolled agent needs, and nothing more."""

    node_id: UUID
    name: str
    agent_token: str
    heartbeat_interval_seconds: int
    offline_after_seconds: int | None
    protocol_version: int = AGENT_PROTOCOL_VERSION
