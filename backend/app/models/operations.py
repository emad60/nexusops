"""Node operations — the pull-based, compare-and-set work queue an agent drains.

An Operation asks exactly one node to do exactly one thing from a closed
whitelist (:class:`~app.models.enums.OperationType`). The control plane never
opens a connection to a node: the agent polls, claims, executes and reports
back, and the control plane's whole job is to make those transitions safe.

Three properties carry the security weight:

* **Tenant ownership.** The row inherits :class:`~app.models.base.OrgScoped`, so
  the session guard filters it, ``before_flush`` stamps it, and PostgreSQL RLS
  backs both up. A node's operations are its organization's operations.
* **One node, one organization.** Claim and result resolve the node from the
  agent token and then act *inside that node's organization scope*
  (``api/v1/agent.py``). A token that names a foreign operation id therefore
  finds nothing — the id is not merely forbidden, it does not exist in that
  scope, which is what keeps the response from being an existence oracle.
* **Expiry gates every transition.** ``expires_at`` is checked by both claim and
  result, so a replayed row or a backup-restored ``PENDING`` is inert after its
  timeout with no extra infrastructure.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    OrgScoped,
    TimestampMixin,
    json_column,
    status_check,
    uuid_pk,
)
from app.models.enums import OperationStatus, OperationType


class Operation(OrgScoped, TimestampMixin, Base):
    """One whitelisted action for one node, with a CAS lifecycle.

    ``attempts`` is incremented by the claim itself and is deliberately *not* a
    re-queue counter: the architecture's decision is that a claimed op whose
    agent dies is left to expire rather than re-delivered, because re-running a
    possibly-executed non-idempotent action is worse than making the operator
    re-issue it. The counter stays so a claim-retry storm is visible and so a
    future re-queue protocol has a place to start.
    """

    __tablename__ = "operations"
    __table_args__ = (
        status_check("status", OperationStatus),
        status_check("type", OperationType),
        # The sweep and the agent's poll both filter on these together.
        Index("ix_operations_node_status", "node_id", "status"),
        Index("ix_operations_expires_at", "expires_at"),
        Index("ix_operations_available_until", "available_until"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()

    node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Named `type` to match the architecture doc and the wire format (the same
    # choice `notification_channels.type` already makes).
    type: Mapped[OperationType] = mapped_column(String(32), nullable=False)

    status: Mapped[OperationStatus] = mapped_column(
        String(16), default=OperationStatus.PENDING, nullable=False, index=True
    )

    params: Mapped[dict] = json_column()

    #: Agent-asserted outcome. Never treated as proof of execution — the platform
    #: guarantees attribution and bounded blast radius, not verification.
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    #: The operator who asked. NULL for a system-issued op; SET NULL on user
    #: deletion so the operation itself survives its requester.
    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # --- timing semantics (docs/node-agent-architecture.md §7) --------------
    # Three separate deadlines, because one value cannot express both "you must
    # collect this before the next heartbeat" and "do not run past the type's
    # timeout":
    #
    # * ``available_until`` — queue/claim deadline. A pending op stays claimable
    #   until this, which is sized to outlast a heartbeat interval plus jitter so
    #   an op created immediately *after* a beat is never dead before the next
    #   one. Claiming after it is refused.
    # * ``execution_deadline`` — set at claim as ``claimed_at + type timeout``.
    #   The agent enforces it locally and reports a timeout failure rather than
    #   hanging; it is NULL while the row is still pending.
    # * ``expires_at`` — the hard terminal deadline the sweep enforces. It equals
    #   ``available_until`` while pending, and is moved to
    #   ``execution_deadline + result grace`` when claimed, so a slow node can
    #   still report a result for a bounded window after its execution deadline.
    available_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    execution_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
