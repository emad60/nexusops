"""Notification channels and delivery records."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, status_check, uuid_pk
from app.models.enums import ChannelType, DeliveryStatus


class NotificationChannel(TimestampMixin, Base):
    """A delivery target (email address / webhook endpoint).

    ``config_ciphertext`` holds the Fernet-encrypted provider configuration
    (recipient addresses, webhook URL, secret headers). ``display_target`` is a
    pre-masked human-readable form safe to show in the UI.
    """

    __tablename__ = "notification_channels"
    __table_args__ = (status_check("type", ChannelType),)

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[ChannelType] = mapped_column(String(16), nullable=False)
    config_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    display_target: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    # Empty list means "subscribe to all event types".
    events: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        status_check("status", DeliveryStatus),
        Index("ix_deliveries_status_retry", "status", "next_retry_at"),
        # One delivery per channel per event: every API worker runs the
        # dispatcher and Redis pubsub broadcasts each frame to ALL of them —
        # without this, every notification was queued (and emailed) once per
        # worker. NULL event_id (manual/test sends) stays exempt: Postgres
        # treats NULLs as distinct.
        UniqueConstraint("channel_id", "event_id", name="uq_deliveries_channel_event"),
        CheckConstraint("attempts >= 0", name="attempts_nonneg"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notification_channels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("system_events.id", ondelete="SET NULL"), nullable=True
    )
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)

    status: Mapped[DeliveryStatus] = mapped_column(
        String(12), default=DeliveryStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Python-side default keeps the value in object state at flush so sync
    # serialization never triggers a lazy refresh (see TimestampMixin).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
