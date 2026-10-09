"""Operation lifecycle: dispatch, the compare-and-set claim, results and expiry.

Every state transition here is a **single conditional UPDATE** whose WHERE clause
carries the precondition. That is the whole concurrency story: two claimants (or
a claim racing the expiry sweep) cannot both win, because the loser's statement
matches zero rows. Reading the row first and then updating it would be a
check-then-act race, so it is not done anywhere in this module.

The two transitions that matter for security are:

* **Claim** — ``PENDING → CLAIMED`` only while ``expires_at`` is in the future and
  the row belongs to the calling node's organization. The agent's identity comes
  from its token (``api/v1/agent.py``), never from the path or the body, so a
  foreign operation id is not "forbidden" — it is absent, which is why the
  response cannot be used as an existence oracle.
* **Result** — ``CLAIMED|RUNNING → SUCCEEDED|FAILED`` under the same expiry and
  ownership guards. A duplicate report against an already-terminal row is a
  200 no-op rather than an error, so an agent retrying a delivery it is unsure
  about cannot be told it did something wrong; a report against a *non-terminal*
  row it never claimed (``PENDING``) is a protocol violation and is refused.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.config import get_settings
from app.core.errors import BadRequest, Conflict, NotFound
from app.core.logging import get_logger
from app.models import Operation, Server
from app.models.enums import OperationStatus, ServerStatus
from app.schemas.operation import (
    KNOWN_CAPABILITIES,
    OPERATION_SPECS,
    OperationCreate,
    validate_params,
)

log = get_logger("nexusops.operations")

#: States an operation can still move out of. Everything else is terminal.
LIVE_STATUSES = (
    OperationStatus.PENDING,
    OperationStatus.CLAIMED,
    OperationStatus.RUNNING,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def spec_for(op_type: Any) -> Any:
    """The registry entry for *op_type* (KeyError is a programming error)."""
    return OPERATION_SPECS[op_type]


def ensure_dispatchable(op_type: Any) -> Any:
    """Refuse a type whose capability is outside the known vocabulary.

    This is the registry-level check (a programming error, not a node property).
    The per-node gate is :func:`ensure_node_can_run`, which reads the capability
    map the node reported at hello.
    """
    spec = spec_for(op_type)
    if spec.capability not in KNOWN_CAPABILITIES:
        raise Conflict(
            f"Operation type '{op_type}' requires node capability "
            f"'{spec.capability}', which is not a known capability; add it to "
            "KNOWN_CAPABILITIES and have the agent report it before dispatch",
            code="NODE_CAPABILITY_UNVERIFIED",
        )
    return spec


def ensure_node_can_run(node: Server, op_type: Any) -> Any:
    """Per-node capability gate. Refuses unless the node reported the capability.

    Fail-closed on both axes, and they are different failures:

    * **Unreported** (``capabilities`` empty — a v1 agent or a node that has not
      completed a v2 hello) is ``NODE_CAPABILITY_UNVERIFIED``. Absence of data is
      never read as "has the capability".
    * **Reported absent** (``docker: {present: false}``) or malformed is
      ``NODE_CAPABILITY_MISSING``.

    A stale or falsely-reported capability is not a safety hole on the agent
    side: the agent re-checks its own registry and local capability before
    executing, so a lie fails the operation rather than running something unsafe.
    """
    spec = spec_for(op_type)
    reported = node.capabilities or {}
    if not reported:
        raise Conflict(
            f"Node '{node.name}' has not reported capabilities, so it cannot be "
            f"sent a {op_type} operation; upgrade its agent to protocol 2",
            code="NODE_CAPABILITY_UNVERIFIED",
        )
    report = reported.get(spec.capability)
    if not isinstance(report, dict) or not report.get("present"):
        raise Conflict(
            f"Node '{node.name}' does not report capability '{spec.capability}'; "
            f"refusing {op_type}",
            code="NODE_CAPABILITY_MISSING",
        )
    return spec


# --- operator-facing ---------------------------------------------------------


async def create_operation(
    db: AsyncSession,
    ctx: AuthContext,
    payload: OperationCreate,
    *,
    request: Request | None = None,
) -> Operation:
    """Queue one whitelisted action for one node in the caller's organization.

    Permission is enforced by the caller (``api/v1/operations.py``), because the
    codename is a property of the operation *type* — a container lifecycle op
    needs ``container.lifecycle``, a log tail needs ``container.logs`` — and a
    static route dependency cannot express that.

    The node must be enrolled and not OFFLINE: dispatching into a node that cannot
    answer would only produce an expired row and a confused operator.
    """
    node = await db.get(Server, payload.node_id)
    if node is None:
        raise NotFound("Node not found", code="NODE_NOT_FOUND")

    if node.agent_enrolled_at is None:
        raise BadRequest(
            "Node has no enrolled agent; enroll it before dispatching operations",
            code="NODE_NOT_ENROLLED",
        )
    if node.status == ServerStatus.OFFLINE:
        raise Conflict(
            "Node is OFFLINE; operations cannot be dispatched to it",
            code="NODE_OFFLINE",
        )

    spec = ensure_dispatchable(payload.type)
    ensure_node_can_run(node, payload.type)
    params = validate_params(payload.type, payload.params)

    now = _utcnow()
    # The queue deadline is deliberately *not* the operation's execution timeout.
    # Delivery rides the heartbeat, so an operation created immediately after a
    # beat must survive at least until the next one (plus jitter). The window is
    # the largest of: the type's own timeout, three heartbeat intervals, and a
    # configured floor.
    window = max(
        spec.timeout_seconds,
        3 * max(node.heartbeat_interval_seconds, 5),
        get_settings().agent_delivery_min_seconds,
    )
    available_until = now + timedelta(seconds=window)

    operation = Operation(
        node_id=node.id,
        type=payload.type,
        status=OperationStatus.PENDING,
        params=params,
        requested_by_id=ctx.user_id,
        available_until=available_until,
        # While pending, the hard deadline is the queue deadline; claiming moves
        # it to the execution deadline plus the result-reporting grace.
        expires_at=available_until,
    )
    db.add(operation)
    await db.flush()
    log.info(
        "operation_created",
        operation=str(operation.id),
        node=str(node.id),
        type=str(payload.type),
    )
    return operation


async def list_operations(
    db: AsyncSession,
    *,
    node_id: uuid.UUID | None = None,
    status: OperationStatus | None = None,
    limit: int,
    offset: int,
) -> tuple[list[Operation], int]:
    """Operations visible in the active scope, newest first."""
    conditions = []
    if node_id is not None:
        conditions.append(Operation.node_id == node_id)
    if status is not None:
        conditions.append(Operation.status == status)

    total = int(
        (await db.execute(select(func.count()).select_from(Operation).where(*conditions))).scalar()
        or 0
    )
    rows = (
        (
            await db.execute(
                select(Operation)
                .where(*conditions)
                .order_by(Operation.created_at.desc(), Operation.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total


async def get_operation(db: AsyncSession, operation_id: uuid.UUID) -> Operation:
    """One operation, or a 404 indistinguishable from a foreign one."""
    operation = await db.get(Operation, operation_id)
    if operation is None:
        raise NotFound("Operation not found", code="OPERATION_NOT_FOUND")
    return operation


async def cancel_operation(db: AsyncSession, operation_id: uuid.UUID) -> Operation:
    """``PENDING → CANCELLED`` only. A claimed op is already in the node's hands.

    Cancelling a claimed/running operation would require the control plane to
    reach the node — which is exactly the connection this design refuses to open
    — so it is refused rather than half-done.
    """
    now = _utcnow()
    result = await db.execute(
        update(Operation)
        .where(
            Operation.id == operation_id,
            Operation.org_id == _active_org(),
            Operation.status == OperationStatus.PENDING,
        )
        .values(status=OperationStatus.CANCELLED, updated_at=now)
        .returning(Operation.id)
    )
    if result.first() is None:
        # Either it does not exist here, or it was no longer pending. Report the
        # distinction honestly: a foreign/absent id is a 404, a claimed op is a
        # conflict the operator can understand.
        operation = await db.get(Operation, operation_id)
        if operation is None:
            raise NotFound("Operation not found", code="OPERATION_NOT_FOUND")
        raise Conflict(
            f"Operation is {operation.status} and can no longer be cancelled",
            code="OPERATION_NOT_CANCELLABLE",
        )
    await db.flush()
    return await get_operation(db, operation_id)


def _active_org() -> uuid.UUID:
    """The organization of the current scope (the guard already requires one)."""
    from app.core.tenancy import require_org

    return require_org()


# --- agent-facing ------------------------------------------------------------


async def pending_ids_for_node(db: AsyncSession, server: Server, *, limit: int = 20) -> list[str]:
    """Ids the agent may claim for this node — oldest and most urgent first.

    Read-only and node-scoped. Since Phase 3 this is the **delivery path**: the
    protocol-2 heartbeat response carries these ids as ``pending_operations``,
    and the agent then claims each one (the claim is the compare-and-set that
    actually moves the row). Ids are hints, never authority — a claim for a row
    that another beat already took, or that has passed its queue deadline, loses
    the CAS and is refused. A protocol-1 agent never sees this list and keeps the
    original 204 heartbeat contract (``api/v1/agent.py``).
    """
    now = _utcnow()
    rows = (
        (
            await db.execute(
                select(Operation.id)
                .where(
                    Operation.node_id == server.id,
                    Operation.status == OperationStatus.PENDING,
                    Operation.available_until > now,
                )
                .order_by(Operation.available_until.asc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [str(row) for row in rows]


async def claim_operation(
    db: AsyncSession, *, server: Server, operation_id: uuid.UUID
) -> Operation:
    """The compare-and-set: ``PENDING → CLAIMED``, once.

    ``attempts`` is incremented inside the same statement, so the counter cannot
    drift from the number of successful claims. A second claimant sees zero rows
    matched and is told the current state rather than silently losing.

    The claim is gated on ``available_until`` (the queue deadline) and opens the
    execution clock: ``execution_deadline = now + type timeout``, with
    ``expires_at`` moved out to ``execution_deadline + result grace`` so a slow
    node can still report a result for one heartbeat after its deadline. The
    operation never becomes executable indefinitely: the agent enforces its own
    deadline, and the sweep expires the row at the hard deadline regardless.
    """
    now = _utcnow()
    # Read the type to size the execution deadline. This read is not the
    # authority — the CAS below is — and it cannot go stale in a way that
    # matters because a row's ``type`` is immutable once written (nothing in the
    # system updates it). It also answers a foreign id with a 404 before any
    # write is attempted.
    op_type = (
        await db.execute(
            select(Operation.type).where(
                Operation.id == operation_id,
                Operation.org_id == server.org_id,
                Operation.node_id == server.id,
            )
        )
    ).scalar_one_or_none()
    if op_type is None:
        raise NotFound("Operation not found", code="OPERATION_NOT_FOUND")
    spec = spec_for(op_type)
    execution_deadline = now + timedelta(seconds=spec.timeout_seconds)
    expires_at = execution_deadline + timedelta(seconds=get_settings().agent_result_grace_seconds)
    result = await db.execute(
        update(Operation)
        .where(
            Operation.id == operation_id,
            Operation.org_id == server.org_id,
            Operation.node_id == server.id,
            Operation.status == OperationStatus.PENDING,
            Operation.available_until > now,
        )
        .values(
            status=OperationStatus.CLAIMED,
            claimed_at=now,
            execution_deadline=execution_deadline,
            expires_at=expires_at,
            attempts=Operation.attempts + 1,
            updated_at=now,
        )
        .returning(Operation.id)
    )
    if result.first() is None:
        await _explain_failed_claim(db, server=server, operation_id=operation_id, now=now)
    await db.flush()
    return await get_operation(db, operation_id)


async def _explain_failed_claim(
    db: AsyncSession, *, server: Server, operation_id: uuid.UUID, now: datetime
) -> None:
    """Turn a lost CAS into the most specific true statement about the row."""
    operation = await db.get(Operation, operation_id)
    if operation is None or operation.node_id != server.id:
        # A foreign id is indistinguishable from a bogus one — no oracle.
        raise NotFound("Operation not found", code="OPERATION_NOT_FOUND")
    if operation.status != OperationStatus.PENDING:
        raise Conflict(
            f"Operation is already {operation.status}",
            code="OPERATION_ALREADY_CLAIMED",
        )
    raise Conflict("Operation is past its queue deadline", code="OPERATION_EXPIRED")


async def record_result(
    db: AsyncSession,
    *,
    server: Server,
    operation_id: uuid.UUID,
    ok: bool,
    output: dict[str, Any],
    error_code: str | None,
    error_message: str | None,
) -> Operation:
    """``CLAIMED|RUNNING → SUCCEEDED|FAILED``, guarded by ownership and expiry.

    Terminal rows are returned unchanged (a duplicate delivery is a no-op, not an
    error). A report against a still-``PENDING`` row means the agent reported on
    something it never claimed, which is refused.
    """
    now = _utcnow()
    target = OperationStatus.SUCCEEDED if ok else OperationStatus.FAILED
    result = await db.execute(
        update(Operation)
        .where(
            Operation.id == operation_id,
            Operation.org_id == server.org_id,
            Operation.node_id == server.id,
            Operation.status.in_((OperationStatus.CLAIMED, OperationStatus.RUNNING)),
            Operation.expires_at > now,
        )
        .values(
            status=target,
            result=_bounded(output),
            error_code=error_code,
            error_message=error_message,
            updated_at=now,
        )
        .returning(Operation.id)
    )
    if result.first() is None:
        operation = await db.get(Operation, operation_id)
        if operation is None or operation.node_id != server.id:
            raise NotFound("Operation not found", code="OPERATION_NOT_FOUND")
        if operation.status not in OperationStatus.terminal():
            raise Conflict(
                f"Operation is {operation.status}; a result is only accepted "
                "for a claimed or running operation",
                code="OPERATION_NOT_CLAIMABLE",
            )
        # Terminal (succeeded/failed/expired/cancelled): the report arrived too
        # late to matter and that is not the agent's fault to fix.
        log.info(
            "operation_result_ignored",
            operation=str(operation_id),
            status=str(operation.status),
        )
        return operation
    await db.flush()
    return await get_operation(db, operation_id)


def _bounded(output: dict[str, Any]) -> dict[str, Any]:
    """Keep one agent report from becoming an unbounded row.

    The agent is authenticated but not trusted with our storage: a huge or deeply
    nested ``output`` is truncated to a shallow, size-capped copy. Results are
    reports for humans, not a data plane.
    """
    from app.core.logging import redact_mapping

    redacted = redact_mapping(output)
    return {k: v for k, v in list(redacted.items())[:50]}


async def expire_one(db: AsyncSession, operation_id: uuid.UUID) -> bool:
    """``PENDING|CLAIMED|RUNNING → EXPIRED`` if the deadline has passed.

    Returns whether this call performed the transition, so the caller only audits
    real state changes. Claimed and running rows are covered deliberately: an op
    whose agent died mid-execution must not sit live forever, and the
    architecture's decision is to expire it rather than re-queue a possibly
    already-executed action.
    """
    now = _utcnow()
    result = await db.execute(
        update(Operation)
        .where(
            Operation.id == operation_id,
            # Required: the session guard refuses an org-scope UPDATE without an
            # explicit org_id predicate (loader criteria do not apply to DML).
            Operation.org_id == _active_org(),
            Operation.status.in_(LIVE_STATUSES),
            Operation.expires_at <= now,
        )
        .values(status=OperationStatus.EXPIRED, updated_at=now)
        .returning(Operation.id)
    )
    return result.first() is not None
