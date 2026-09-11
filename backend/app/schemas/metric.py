"""Schemas for metric timeseries, snapshots and the dashboard summary."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.base import APIModel


class MetricPoint(APIModel):
    """A single timeseries bucket.

    Always carries ``ts``. Raw-granularity series expose ``<metric>_avg``;
    rollup series additionally carry ``<metric>_min`` / ``<metric>_max``
    produced by the aggregation query (dynamic keys, hence extra=allow).
    """

    model_config = ConfigDict(from_attributes=True, extra="allow", populate_by_name=True)

    ts: datetime


class Timeseries(APIModel):
    """Aggregated metric series for one server."""

    range: str
    granularity: str
    points: list[MetricPoint] = Field(default_factory=list)


class MetricSnapshotOut(APIModel):
    """Most recent raw agent sample for a server."""

    server_id: UUID
    recorded_at: datetime
    cpu_percent: float
    mem_used_mb: float
    mem_percent: float
    disk_used_gb: float
    disk_percent: float
    net_rx_kb_s: float
    net_tx_kb_s: float
    load1: float
    uptime_seconds: int


class RecentEvent(APIModel):
    """Minimal system-event frame embedded in the dashboard summary."""

    id: UUID
    type: str
    level: str
    message: str = ""
    resource_type: str | None = None
    resource_id: str | None = None
    created_at: datetime


class DashboardSummary(APIModel):
    """Single-call payload powering the operator landing page."""

    servers_total: int
    servers_online: int
    servers_offline: int
    servers_degraded: int
    containers_running: int
    monitors_up: int
    monitors_down: int
    monitors_paused: int
    incidents_open: int
    deployments_today: int
    deployments_failed_today: int
    avg_cpu_percent: float | None = None
    avg_mem_percent: float | None = None
    unread_alerts: int
    recent_events: list[RecentEvent] = Field(default_factory=list)
