"""Observability: monitors, checks, incidents, metrics, logs, events, audit."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    TimestampMixin,
    big_serial_pk,
    json_column,
    status_check,
    uuid_pk,
)
from app.models.enums import (
    ActorType,
    AlertSeverity,
    AuditResult,
    CheckResult,
    EventLevel,
    IncidentEventKind,
    IncidentSeverity,
    IncidentStatus,
    LogLevel,
    LogSource,
    MetricGranularity,
    MonitorStatus,
)


class Monitor(TimestampMixin, Base):
    __tablename__ = "monitors"
    __table_args__ = (
        status_check("status", MonitorStatus),
        CheckConstraint("interval_seconds >= 10", name="interval_min"),
        CheckConstraint("timeout_seconds > 0 AND timeout_seconds <= 60", name="timeout_bounds"),
        Index("ix_monitors_next_check", "enabled", "next_check_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    method: Mapped[str] = mapped_column(String(10), default="GET", nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    timeout_seconds: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    expected_status: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    expected_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    headers: Mapped[dict] = json_column()
    skip_tls_verify: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_redirects: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[MonitorStatus] = mapped_column(
        String(16), default=MonitorStatus.PENDING, nullable=False, index=True
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consecutive_successes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_check_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    failure_threshold: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    success_threshold: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class MonitorCheck(Base):
    __tablename__ = "monitor_checks"
    __table_args__ = (
        Index("ix_checks_monitor_time", "monitor_id", "checked_at"),
        status_check("result", CheckResult),
    )

    id: Mapped[int] = big_serial_pk()
    monitor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    result: Mapped[CheckResult] = mapped_column(String(12), nullable=False, index=True)
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str] = mapped_column(String(500), default="", nullable=False)


class Incident(TimestampMixin, Base):
    __tablename__ = "incidents"
    __table_args__ = (
        status_check("status", IncidentStatus),
        status_check("severity", IncidentSeverity),
        Index("ix_incidents_monitor_status", "monitor_id", "status"),
        Index("ix_incidents_status_opened", "status", "opened_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    monitor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        String(12), default=IncidentSeverity.MAJOR, nullable=False
    )
    status: Mapped[IncidentStatus] = mapped_column(
        String(16), default=IncidentStatus.OPEN, nullable=False
    )
    failure_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[str] = mapped_column(Text, default="", nullable=False)

    timeline: Mapped[list[IncidentEvent]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentEvent.occurred_at",
        lazy="selectin",
    )


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    __table_args__ = (Index("ix_incident_events_incident_time", "incident_id", "occurred_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    incident_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[IncidentEventKind] = mapped_column(String(24), nullable=False)
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    data: Mapped[dict[str, Any]] = json_column()
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        Index("ix_metrics_server_gran_time", "server_id", "granularity", "recorded_at"),
        status_check("granularity", MetricGranularity),
    )

    id: Mapped[int] = big_serial_pk()
    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False
    )
    granularity: Mapped[MetricGranularity] = mapped_column(String(8), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    cpu_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    mem_used_mb: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    mem_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    disk_used_gb: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    disk_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    net_rx_kb_s: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    net_tx_kb_s: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    load1: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    uptime_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    extra: Mapped[dict[str, Any]] = json_column()


class LogEntry(Base):
    __tablename__ = "log_entries"
    __table_args__ = (
        Index("ix_logs_container_ts", "container_id", "ts"),
        Index("ix_logs_deployment", "deployment_id", "id"),
    )

    id: Mapped[int] = big_serial_pk()
    source: Mapped[LogSource] = mapped_column(String(16), nullable=False)
    container_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("containers.id", ondelete="CASCADE"), nullable=True
    )
    deployment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deployments.id", ondelete="CASCADE"), nullable=True
    )
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=True
    )
    stream: Mapped[str] = mapped_column(String(8), default="stdout", nullable=False)
    level: Mapped[LogLevel] = mapped_column(String(8), default=LogLevel.UNKNOWN, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SystemEvent(Base):
    __tablename__ = "system_events"
    __table_args__ = (
        Index("ix_events_created_desc", "created_at"),
        Index("ix_events_type_created", "type", "created_at"),
        UniqueConstraint("dedup_key", name="uq_system_events_dedup_key"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    level: Mapped[EventLevel] = mapped_column(String(12), default=EventLevel.INFO, nullable=False)
    message: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_type: Mapped[ActorType] = mapped_column(
        String(12), default=ActorType.SYSTEM, nullable=False
    )
    resource_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(72), nullable=True)
    data: Mapped[dict[str, Any]] = json_column()
    dedup_key: Mapped[str | None] = mapped_column(String(160), nullable=True)


class AuditLog(Base):
    """Append-only audit trail. UPDATE/DELETE are blocked by a DB trigger."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_created_desc", "created_at"),
        status_check("result", AuditResult),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_email: Mapped[str] = mapped_column(String(320), default="system", nullable=False)
    action: Mapped[str] = mapped_column(String(96), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(72), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    user_agent: Mapped[str] = mapped_column(String(400), default="", nullable=False)
    result: Mapped[AuditResult] = mapped_column(
        String(12), default=AuditResult.SUCCESS, nullable=False
    )
    # Column is `metadata` in SQL; attribute avoids Base.metadata clash.
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"
    __table_args__ = (
        status_check("severity", AlertSeverity),
        Index("ix_alerts_read_created", "read_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    severity: Mapped[AlertSeverity] = mapped_column(
        String(12), default=AlertSeverity.WARNING, nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="system", nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(72), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
