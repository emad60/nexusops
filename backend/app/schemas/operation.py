"""Operation schemas plus the whitelist registry that defines the exec surface.

``OPERATION_SPECS`` is the whole dispatch contract. Adding an operation type is a
registry change with its own contract test — never a params pass-through — and
every entry names the *existing* permission codename it reuses. The architecture
deliberately does not introduce a generic ``node.execute`` grant, so a container
action is authorised by ``container.lifecycle`` and a log tail by
``container.logs``.

Params are validated by a per-type model with ``extra="forbid"`` (the ``APIModel``
default), so an unknown field is a 422 rather than something the agent has to
defend against.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, ValidationError

from app.core.errors import UnprocessableEntity
from app.models.enums import OperationStatus, OperationType
from app.schemas.base import APIModel, OutModel

#: Container ids are docker's 64-hex (or a 12-char short id). Anchored and
#: character-limited at the boundary so nothing exotic reaches the node.
_CONTAINER_ID = r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,71}$"

#: The most log lines one operation may ask for. Bounded at the schema so the
#: node cannot be asked to stream an unbounded amount across a poll cycle.
LOGS_TAIL_MAX = 500


class ContainerActionParams(APIModel):
    """Params for the container lifecycle/removal operations."""

    container_id: str = Field(min_length=1, max_length=72, pattern=_CONTAINER_ID)
    force: bool = Field(default=False, description="Only meaningful for remove")


class LogsTailParams(APIModel):
    """Params for ``logs.tail`` — a bounded batch, never a stream."""

    container_id: str = Field(min_length=1, max_length=72, pattern=_CONTAINER_ID)
    tail: int = Field(default=100, ge=1, le=LOGS_TAIL_MAX)
    since: str | None = Field(default=None, max_length=64)


@dataclass(frozen=True)
class OperationSpec:
    """Everything the control plane needs to know about one operation type.

    ``capability`` is the node-side ability an operation needs. Per-node
    capability advertisement belongs to the agent enrollment negotiation, which
    is **not built** (``servers`` has no capabilities column), so dispatch cannot
    yet ask "does *this* node have it?". It can, however, refuse a type whose
    capability is not guaranteed for every enrolled agent of the current
    contract — see :data:`UNIVERSAL_CAPABILITIES` and
    ``operation_service.create_operation``. What is otherwise enforced is that
    the node exists in the caller's organization, is enrolled, and is not
    OFFLINE.
    """

    permission: str
    capability: str
    timeout_seconds: int
    params_model: type[APIModel]


#: Capabilities every enrolled agent is known to provide under the current
#: agent contract. The reference agent is a Docker observer/controller and
#: heartbeats containers, so ``docker`` is a property of enrollment itself, not
#: something a node has to advertise.
#:
#: This set is the **Phase 2 boundary**. A new operation type whose capability is
#: not listed here cannot be dispatched: the negotiation that would let the
#: control plane confirm that a *specific* node has it does not exist yet, and
#: assuming it would hand a node work it cannot perform. Widening this set is a
#: deliberate decision that must come with either that negotiation or a written
#: argument that the capability is universal.
UNIVERSAL_CAPABILITIES: frozenset[str] = frozenset({"docker"})


OPERATION_SPECS: dict[OperationType, OperationSpec] = {
    OperationType.CONTAINER_START: OperationSpec(
        "container.lifecycle", "docker", 60, ContainerActionParams
    ),
    OperationType.CONTAINER_STOP: OperationSpec(
        "container.lifecycle", "docker", 60, ContainerActionParams
    ),
    OperationType.CONTAINER_RESTART: OperationSpec(
        "container.lifecycle", "docker", 60, ContainerActionParams
    ),
    OperationType.CONTAINER_REMOVE: OperationSpec(
        "container.remove", "docker", 60, ContainerActionParams
    ),
    OperationType.LOGS_TAIL: OperationSpec("container.logs", "docker", 30, LogsTailParams),
}


def validate_params(op_type: OperationType, params: dict[str, Any]) -> dict[str, Any]:
    """Validate *params* against the type's model and return the stored form.

    ``model_dump`` (not ``model_dump(exclude_unset=True)``) so the row carries a
    complete, self-describing parameter set for the agent — defaults included —
    rather than relying on the agent to re-apply them.

    A validation failure is a **422**, not a 500: the type is whitelisted but the
    params are wrong, which is a client error. The message names the field so an
    operator can fix it, and no part of the raw payload is echoed back.
    """
    spec = OPERATION_SPECS[op_type]
    try:
        return spec.params_model.model_validate(params).model_dump()
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(part) for part in first.get("loc", ())) or "params"
        raise UnprocessableEntity(
            f"Invalid {op_type} params: {field} — {first.get('msg', 'invalid')}",
            code="OPERATION_PARAMS_INVALID",
        ) from exc


class OperationCreate(APIModel):
    """Request one whitelisted action on one node."""

    node_id: UUID
    type: OperationType
    params: dict[str, Any] = Field(default_factory=dict)


class OperationOut(OutModel):
    """Operation state as the dashboard sees it."""

    id: UUID
    node_id: UUID
    type: OperationType
    status: OperationStatus
    params: dict[str, Any]
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    requested_by_id: UUID | None = None
    attempts: int
    claimed_at: datetime | None = None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class AgentOperationClaimOut(APIModel):
    """What the agent receives on a successful claim — and nothing more.

    The row's organization is not echoed: the token it arrived with already
    defines it, and repeating it would invite the agent to reason about tenants.
    """

    id: UUID
    type: OperationType
    params: dict[str, Any]
    expires_at: datetime


class AgentOperationResultOut(APIModel):
    """The operation's state after a result, so the agent can confirm the write.

    ``status`` may be the state the agent just asserted *or* a terminal state it
    was too late to change (a duplicate report is a no-op, not an error), so the
    agent reads the truth rather than assuming its report won.
    """

    id: UUID
    type: OperationType
    status: OperationStatus
    error_code: str | None = None


class AgentOperationResultIn(APIModel):
    """The agent's report for one operation.

    ``ok`` is agent-asserted, never verified. ``output`` is bounded and
    shape-checked server-side; failures must carry a stable ``error_code`` so
    operators see a categorised reason rather than a raw daemon body.
    """

    ok: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = Field(default=None, max_length=64)
    error_message: str | None = Field(default=None, max_length=2000)
