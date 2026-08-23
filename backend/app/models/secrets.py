"""Secrets manager models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
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

from app.models.base import Base, TimestampMixin, uuid_pk


class Secret(TimestampMixin, Base):
    """An encrypted configuration value.

    The plaintext is never returned by the API after creation; consumers
    (deployment engine) resolve values server-side via the service layer.
    Rotation bumps ``version`` and re-encrypts.
    """

    __tablename__ = "secrets"
    __table_args__ = (
        # Global secrets have NULL project_id — partial unique index covers them.
        UniqueConstraint("project_id", "key", name="uq_secrets_project_key"),
        Index(
            "ux_secrets_global_key",
            "key",
            unique=True,
            postgresql_where=text("project_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
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
