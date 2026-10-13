"""Tenancy models: organizations, memberships, and the organization DEK envelope.

The first two tables are the root of every tenant boundary in the platform:

``User → Membership → Organization → tenant-scoped resources``

Neither of them inherits :class:`~app.models.base.OrgScoped`, and that is
deliberate rather than an oversight:

* ``organizations`` *is* the tenant, so it cannot be scoped by itself.
* ``memberships`` must be readable **before** an organization is known —
  validating the ``X-Org-Id`` header means answering "is the caller a member of
  this org?", which is a cross-org read by construction.

Both are therefore in the pre-org credential/identity class documented in
``docs/multi-tenancy.md`` §8(a): application-layer guarded, RLS-exempt. The
residual risk is stated plainly there — this class has no database-level
tenancy net, so the carve-out allowlist in :mod:`app.core.tenancy` is the fence.

:class:`OrganizationDekEnvelope` is the counter-example that keeps that class
small: it holds per-organization key material, so it is **not** exempt. It is a
normal ``OrgScoped`` tenant table with RLS policies of its own (Phase 5.2.1.2,
audit finding F1), which is what stops a plain organization read from being a
cross-tenant envelope read.
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
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, OrgScoped, TimestampMixin, status_check, uuid_pk
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

    # NOTE: the organization's wrapped DEK deliberately does **not** live here.
    # This table is RLS-exempt (it *is* the tenant), so key material stored on it
    # would be readable by every code path that can read an organization row.
    # Phase 5.2.1.2 (audit finding F1) moved it to
    # :class:`OrganizationDekEnvelope`, an ordinary tenant table.

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="organization", cascade="all, delete-orphan", lazy="selectin"
    )


class OrganizationDekEnvelope(TimestampMixin, OrgScoped, Base):
    """The organization's Fernet DEK, **wrapped** by the configured KEK provider.

    The plaintext key never reaches this table and never leaves the operation
    that unwrapped it. The stored value is the self-describing envelope
    (``v1:provider:key_id:key_version:base64``), so a row states which provider
    can unwrap it and a KEK rotation knows what it is looking at.

    **Why a table of its own** (Phase 5.2.1.2, audit finding F1). Until this
    revision the two columns below sat on ``organizations``, which is one of the
    documented RLS-exempt tables — it *is* the tenant and cannot be scoped by its
    own id. The consequence was that the confidentiality of every organization's
    key material rested on the KEK provider alone: any read path that could reach
    an organization row (a listing, a join, a bulk export, a future report) could
    read another tenant's envelope, and PostgreSQL would not have refused. Here
    the envelope is an ordinary tenant table: ``org_id`` is stamped by the
    tenancy guard, the RLS policies scope every read and write to the acting
    organization, and a cross-tenant envelope read is a thing the database
    refuses rather than a thing this codebase remembers not to write.

    **One row per organization**, enforced by ``uq_organization_dek_envelopes_org_id``
    rather than by a convention: "the authoritative current envelope and
    generation" is then a property of the schema, and the row is what a
    compare-and-set rotates. The row is created **lazily and only by the
    key-management service** (``app/services/dek_envelope.py``) — organization
    creation does not write here, so no other module gains a write path to key
    material. An organization with no row has no DEK; a row with
    ``dek_generation = 0`` says the same thing explicitly.

    The pair invariant survives the move unchanged, and is joined by the explicit
    non-negative generation bound the 5.2.1 migration documented but did not
    create: generation 0 means "no DEK yet" (so a ciphertext with it would be an
    orphan) and a nonzero generation without a ciphertext would promise key
    material that does not exist.
    """

    __tablename__ = "organization_dek_envelopes"
    __table_args__ = (
        UniqueConstraint("org_id", name="uq_organization_dek_envelopes_org_id"),
        # Audit finding F3: the documented bound, made a database guarantee.
        # ``dek_generation`` is a counter, so a negative value is not a state this
        # model can produce — it is only reachable by a writer that bypassed it,
        # which is exactly what a CHECK is for.
        CheckConstraint("dek_generation >= 0", name="dek_generation_non_negative"),
        CheckConstraint(
            "(dek_ciphertext IS NULL) = (dek_generation = 0)",
            name="dek_pair_valid",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()

    #: The wrapped DEK of the organization this row belongs to. NULL until that
    #: organization's first key-management write.
    dek_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Which DEK generation is wrapped above: 0 means "no DEK yet", the first real
    #: DEK is 1, and a *DEK* rotation increments it. A KEK rotation does not (the
    #: KEK version lives inside the envelope, not in this column) — see
    #: :func:`app.services.dek_envelope.rewrap_org_deks`.
    dek_generation: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default=text("0")
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


__all__ = [
    "SYSTEM_ORG_SENTINEL",
    "Membership",
    "Organization",
    "OrganizationDekEnvelope",
]
