"""Declarative base, shared mixins and column helpers."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Identity, Uuid, func
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
