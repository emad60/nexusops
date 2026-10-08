"""Secrets manager models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
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
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, OrgScoped, TimestampMixin, uuid_pk


class Secret(OrgScoped, TimestampMixin, Base):
    """An encrypted configuration value, scoped to org, project or environment.

    Layered scope (Phase 2): ``project_id`` NULL → organization-wide; set with
    ``environment_id`` NULL → project; ``environment_id`` set → that environment
    only. Resolution prefers the most specific level that defines the key.

    ``ciphertext``/``version``/``digest`` are the **denormalized current** value
    and a pointer to the live :class:`SecretVersion`. The plaintext is never
    returned by the API; consumers (the deployment engine) resolve values
    server-side in the service layer. Rotation appends a version and moves the
    pointer — it never overwrites history.
    """

    __tablename__ = "secrets"
    __table_args__ = (
        # An environment-scoped secret is always inside a project (there is no
        # such thing as an environment outside a project).
        CheckConstraint(
            "project_id IS NOT NULL OR environment_id IS NULL",
            name="environment_requires_project",
        ),
        # One key namespace per scope level, per organization. Key uniqueness is
        # per organization: two tenants both naming a secret DATABASE_URL must
        # not collide (an instance-wide index would make one org's key name both
        # a creation failure and an existence oracle for the others). NULLs are
        # distinct in a plain UNIQUE, so each level needs a partial index.
        Index(
            "ux_secrets_org_scope_key",
            "org_id",
            "key",
            unique=True,
            postgresql_where=text("project_id IS NULL"),
        ),
        Index(
            "ux_secrets_project_scope_key",
            "org_id",
            "project_id",
            "key",
            unique=True,
            postgresql_where=text("project_id IS NOT NULL AND environment_id IS NULL"),
        ),
        Index(
            "ux_secrets_environment_scope_key",
            "org_id",
            "environment_id",
            "key",
            unique=True,
            postgresql_where=text("environment_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    environment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deployment_environments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(160), nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    digest: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    description: Mapped[str] = mapped_column(String(300), default="", nullable=False)

    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class SecretVersion(OrgScoped, TimestampMixin, Base):
    """One immutable value of a :class:`Secret` — append-only history.

    A row is written exactly once, when its value becomes current (create,
    rotate or rollback). Nothing in the service layer UPDATEs or DELETEs a
    version; the parent's pointer moves instead. Rollback therefore appends a
    *new* version rather than resurrecting an old one, so history is never
    rewritten and a bad rotation stays recoverable.

    ``org_id`` is part of the row (not merely inherited through the parent) so
    the table takes part in the same three nets as every other tenant table:
    the ORM guard, ``before_flush`` ownership stamping, and PostgreSQL RLS.
    """

    __tablename__ = "secret_versions"
    __table_args__ = (
        UniqueConstraint("secret_id", "version", name="uq_secret_versions_secret_version"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    secret_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("secrets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    digest: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
