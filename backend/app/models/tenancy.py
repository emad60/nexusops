"""Tenancy models: organizations and memberships.

These two tables are the root of every tenant boundary in the platform:

``User → Membership → Organization → tenant-scoped resources``

Neither table inherits :class:`~app.models.base.OrgScoped`, and that is
deliberate rather than an oversight:

* ``organizations`` *is* the tenant, so it cannot be scoped by itself.
* ``memberships`` must be readable **before** an organization is known —
  validating the ``X-Org-Id`` header means answering "is the caller a member of
  this org?", which is a cross-org read by construction.

Both are therefore in the pre-org credential/identity class documented in
``docs/multi-tenancy.md`` §8(a): application-layer guarded, RLS-exempt. The
residual risk is stated plainly there — this class has no database-level
tenancy net, so the carve-out allowlist in :mod:`app.core.tenancy` is the fence.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, status_check, uuid_pk
from app.models.enums import MembershipStatus, OrganizationStatus
from app.models.identity import Role

#: Reserved GUC value meaning "no tenant filter" (system/maintenance scope).
#: Real organization ids are uuid4 and can never equal this; the CHECK
#: constraint below makes that a schema guarantee rather than a probability,
#: because a collision would let one organization read every other one.
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"


class Organization(TimestampMixin, Base):
    """A tenant. Every organization-owned row points here via ``org_id``."""

    __tablename__ = "organizations"
    __table_args__ = (
        status_check("status", OrganizationStatus),
        CheckConstraint(
            f"id <> '{SYSTEM_ORG_SENTINEL}'::uuid",
            name="id_not_system_sentinel",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[OrganizationStatus] = mapped_column(
        String(16), default=OrganizationStatus.ACTIVE, nullable=False
    )
    #: True for the organization the Phase 1 migration auto-provisions for
    #: pre-existing rows. It is named after the instance creator (never after
    #: the vendor) and every surface that shows it says so, so nobody mistakes
    #: a provisional tenant for a deliberately created one.
    is_provisional: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default=text("false")
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    #: Truncated for display once the org owns real work; NULL until then.
    renamed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="organization", cascade="all, delete-orphan", lazy="selectin"
    )


class Membership(TimestampMixin, Base):
    """Binds a user to an organization with a role *inside that organization*.

    ``role_id`` is the authority for permission checks: a user is an Admin in
    one org and a Viewer in another. ``User.role_id`` survives only as the
    default role applied when a new membership is created.
    """

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_memberships_org_user"),
        Index("ix_memberships_user_status", "user_id", "status"),
        status_check("status", MembershipStatus),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable so a membership can exist without granting anything (and so the
    # bootstrap backfill never invents authority for a user who had no role).
    # Permission resolution treats NULL as the empty set.
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[MembershipStatus] = mapped_column(
        String(16), default=MembershipStatus.ACTIVE, nullable=False
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Both are ``selectin``: a membership is almost always asked about together
    # with the organization it belongs to and the role that grants authority in
    # it, and a lazy load here would be an implicit IO in a sync context (auth
    # resolves permissions from an already-loaded membership — see
    # ``app.api.deps._load_permissions``).
    organization: Mapped[Organization] = relationship(back_populates="memberships", lazy="selectin")
    role: Mapped[Role | None] = relationship(lazy="selectin")


__all__ = ["SYSTEM_ORG_SENTINEL", "Membership", "Organization"]
