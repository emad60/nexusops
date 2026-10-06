"""Declarative base, shared mixins and column helpers."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base for all ORM models with stable constraint naming for Alembic."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Pluralised snake_case table name derived from the class name."""
        name = cls.__name__
        snake = "".join(f"_{c.lower()}" if c.isupper() else c for c in name).lstrip("_")
        return snake + "s"


Base.metadata.naming_convention = NAMING_CONVENTION


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def big_serial_pk() -> Mapped[int]:
    """Identity PK for very high-volume tables (metrics, logs)."""
    return mapped_column(BigInteger, Identity(always=True), primary_key=True)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def org_id_column(*, nullable: bool = False, index: bool = True):
    """A plain ``org_id`` column for the few tables that carry one without
    taking part in the ORM tenant guard (see :class:`OrgScoped`).

    Used by the pre-org credential/identity tables (``api_keys``, ``roles``)
    whose rows must be findable *before* an organization is known — auth has to
    locate the caller first. Those tables are RLS-exempt by design; the
    exemption list and its rationale live in ``app.core.tenancy``.
    """
    return mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=nullable,
        index=index,
    )


class OrgScoped:
    """Mixin marking a table as **organization-owned** (Phase 1 tenancy).

    Set the plain class attribute ``org_id_nullable = True`` on a table where a
    NULL ``org_id`` is meaningful — currently only ``audit_logs`` and
    ``system_events``, which record events that happen before (or without) any
    organization: a failed login for an address that has no account at all, or
    instance bootstrap. Such rows are **invisible under organization scope**
    (the guard and RLS both drop them) and readable only through
    ``system_scope()``, which is exactly the boundary this mixin exists to
    enforce. Every tenant security event carries its organization.

    Two things follow from inheriting this mixin, and both matter:

    1. The table gets an ``org_id`` column (NOT NULL unless the table opts into
       nullable per above), so ownership is explicit in the schema rather than
       implied by a chain of foreign keys.
    2. The session guard in :mod:`app.core.tenancy` filters **every** ORM SELECT
       that touches an ``OrgScoped`` mapper (SQLAlchemy applies
       ``with_loader_criteria`` to all mapped classes inheriting this mixin).

    The guard is one of three independent nets: the guard (SELECTs), explicit
    ``org_id`` predicates in write paths (DML), and PostgreSQL RLS (the backstop
    that catches bulk DML, Core statements, identity-map hits and raw SQL).

    Tables that must be readable before an org is known (users, sessions,
    api_keys, memberships, roles, and the agent credential-routing table) do
    **not** inherit this mixin — they use :func:`org_id_column` or have no
    ``org_id`` at all.
    """

    @declared_attr
    def org_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=bool(getattr(cls, "org_id_nullable", False)),
            index=True,
        )


class TimestampMixin:
    # Python-side defaults: values land in object state at flush so sync
    # serialization never triggers a lazy refresh (MissingGreenlet in async
    # SQLAlchemy). The DB-level server_default stays as a fallback for writers
    # outside the ORM.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )


def json_column(**kwargs):
    return mapped_column(JSONB, nullable=False, default=dict, **kwargs)


def status_check(column_name: str, enum_cls: type[enum.Enum]) -> CheckConstraint:
    values = ", ".join(f"'{member.value}'" for member in enum_cls)
    return CheckConstraint(f"{column_name} IN ({values})", name=f"{column_name}_valid")
