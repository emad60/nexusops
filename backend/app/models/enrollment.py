"""Organization-scoped enrollment tokens — the credential that mints node identities.

An enrollment token (wire prefix ``nxk_``) is the *only* credential an operator
hands to a machine that is not yet a node. It is deliberately distinct in kind
from a node credential (``nxa_``): an ``nxk_`` token is single-use, short-lived
and revocable, so it can safely travel through an install command line; an
``nxa_`` token is a long-lived per-node write credential and never leaves the
machine.

The row is the security boundary, and the control plane derives the node's
organization from it — never from anything the agent sends (see
docs/node-agent-architecture.md §3.2, docs/multi-tenancy.md §2). Consumption is
a single compare-and-set on ``used_at``, so two concurrent attempts to redeem the
same token cannot both succeed even under a race.

The table is organization-owned and carries the same two RLS policies as every
other tenant table. The by-hash lookup happens *before* an organization is known,
so it runs inside a system scope in the enrollment service (the same documented
carve-out ``api_keys`` and ``agent_credentials`` rely on).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, OrgScoped, TimestampMixin, uuid_pk


class EnrollmentToken(OrgScoped, TimestampMixin, Base):
    """One single-use credential that enrolls (or claims) exactly one node."""

    __tablename__ = "enrollment_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()

    #: Operator-facing label so a fleet wave is distinguishable in the UI.
    name: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    #: SHA-256 hex of the raw ``nxk_`` token. The raw value is shown once at
    #: creation and is never stored, logged or retrievable again.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    #: Always true in v1. Kept as a column so the single-use rule is explicit in
    #: the schema and in the consume CAS, rather than an unstated assumption.
    single_use: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    #: Short TTL (default 1h, max 7d — enforced in the schema layer).
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    #: Kill switch, independent of expiry. Revoking is immediate.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    #: Set atomically by the consume CAS. The node might still be created after
    #: this within the same transaction; ``used_by_node_id`` records the outcome.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used_by_node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True
    )

    #: Optional claim target: a placeholder Node that already exists in this
    #: organization. When set, enrollment claims it instead of creating a new
    #: node. The token's org must match the placeholder's org.
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True
    )

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    #: Free-form operator note; bounded by the schema, never a secret.
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)

    @property
    def is_usable(self) -> bool:
        """Whether the row could still be redeemed (not a race-safe check)."""
        return self.used_at is None and self.revoked_at is None
