"""Metrics pipeline: timeseries queries, rollup aggregation, retention, dashboard."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from statistics import fmean
from typing import Any, cast

from sqlalchemy import Select, String, delete, extract, func, literal, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.config import get_settings
from app.core.errors import BadRequest, NotFound
from app.core.logging import get_logger
from app.models import (
    Alert,
    Container,
    Deployment,
    Incident,
    MetricSnapshot,
    Monitor,
    Server,
    SystemEvent,
)
from app.models.enums import (
    ContainerStatus,
    DeploymentStatus,
    IncidentStatus,
    MetricGranularity,
    ServerStatus,
)

log = get_logger("nexusops.metrics")

#: Queryable metric columns on :class:`MetricSnapshot` (all Float gauges).
METRIC_COLUMNS: tuple[str, ...] = (
    "cpu_percent",
    "mem_percent",
    "mem_used_mb",
    "disk_percent",
    "disk_used_gb",
    "net_rx_kb_s",
    "net_tx_kb_s",
    "load1",
)

#: Supported query windows.
RANGE_MAP: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

#: Raw-granularity bucket widths (seconds) chosen to keep points <= 400.
_RAW_BUCKET_SECONDS: dict[str, int] = {"1h": 60, "6h": 300}


def granularity_for_range(range_key: str) -> MetricGranularity:
    """Map a range key to the storage granularity served for it."""
    delta = RANGE_MAP.get(range_key)
    if delta is None:
        raise BadRequest(
            f"Unknown range '{range_key}'. Valid ranges: {', '.join(RANGE_MAP)}",
            code="INVALID_RANGE",
        )
    if delta <= timedelta(hours=6):
        return MetricGranularity.RAW
    if delta <= timedelta(days=7):
        return MetricGranularity.HOURLY
    return MetricGranularity.DAILY


# --- Queries ------------------------------------------------------------------


async def ensure_server(db: AsyncSession, server_id: uuid.UUID) -> None:
    """Raise NotFound when *server_id* does not exist."""
    exists = (
        await db.execute(select(Server.id).where(Server.id == server_id))
    ).scalar_one_or_none()
    if exists is None:
        raise NotFound("Server not found")


def _raw_bucket_expression(seconds: int) -> Any:
    """``to_timestamp(floor(epoch / N) * N)`` fixed-width bucketing."""
    epoch = extract("epoch", MetricSnapshot.recorded_at)
    return func.to_timestamp(func.floor(epoch / float(seconds)) * float(seconds)).label("ts")


async def timeseries(
    db: AsyncSession,
    server_id: uuid.UUID,
    range_key: str = "24h",
    metrics: tuple[str, ...] = ("cpu_percent", "mem_percent"),
) -> dict[str, Any]:
    """Return ``{range, granularity, points}`` for one server.

    A single grouped query buckets ``recorded_at`` ascending: raw ranges use
    fixed-width ``to_timestamp(floor(epoch/N)*N)`` buckets; hourly/daily use
    ``date_trunc``. Rollup rows carry ``<metric>_avg`` (primary column) plus
    ``_min``/``_max`` from the JSONB extra map; raw rows expose only averages.
    """
    delta = RANGE_MAP.get(range_key)
    if delta is None:
        raise BadRequest(
            f"Unknown range '{range_key}'. Valid ranges: {', '.join(RANGE_MAP)}",
            code="INVALID_RANGE",
        )
    unknown = [m for m in metrics if m not in METRIC_COLUMNS]
    if unknown or not metrics:
        raise BadRequest(
            f"Unknown metrics: {', '.join(unknown)}. Valid metrics: {', '.join(METRIC_COLUMNS)}",
            code="INVALID_METRIC",
        )

    granularity = granularity_for_range(range_key)
    end = datetime.now(UTC)
    start = end - delta

    rollup = granularity is not MetricGranularity.RAW
    if rollup:
        unit = "hour" if granularity is MetricGranularity.HOURLY else "day"
        bucket = func.date_trunc(unit, MetricSnapshot.recorded_at).label("ts")
    else:
        bucket = _raw_bucket_expression(_RAW_BUCKET_SECONDS[range_key])

    columns: list[Any] = [bucket]
    for metric in metrics:
        col = getattr(MetricSnapshot, metric)
        columns.append(func.avg(col).label(f"{metric}_avg"))
        if rollup:
            extra_min = MetricSnapshot.extra[metric]["min"].as_float()
            extra_max = MetricSnapshot.extra[metric]["max"].as_float()
            columns.append(func.min(extra_min).label(f"{metric}_min"))
            columns.append(func.max(extra_max).label(f"{metric}_max"))

    stmt: Select[tuple] = (
        select(*columns)
        .where(
            MetricSnapshot.server_id == server_id,
            MetricSnapshot.granularity == granularity.value,
            MetricSnapshot.recorded_at >= start,
            MetricSnapshot.recorded_at <= end,
        )
        .group_by(bucket)
        .order_by(bucket.asc())
    )
    rows = (await db.execute(stmt)).mappings().all()

    points: list[dict[str, Any]] = []
    for row in rows:
        point: dict[str, Any] = {"ts": row["ts"]}
        for key, value in row.items():
            if key != "ts":
                point[key] = round(float(value), 3) if value is not None else None
        points.append(point)
    return {"range": range_key, "granularity": granularity.value, "points": points}


async def latest_for_servers(
    db: AsyncSession, server_ids: list[uuid.UUID]
) -> dict[uuid.UUID, MetricSnapshot]:
    """Most recent RAW snapshot per server via ``DISTINCT ON``."""
    if not server_ids:
        return {}
    stmt = (
        select(MetricSnapshot)
        .where(
            MetricSnapshot.server_id.in_(server_ids),
            MetricSnapshot.granularity == MetricGranularity.RAW.value,
        )
        .distinct(MetricSnapshot.server_id)
        .order_by(
            MetricSnapshot.server_id.asc(),
            MetricSnapshot.recorded_at.desc(),
            MetricSnapshot.id.desc(),
        )
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {row.server_id: row for row in rows}


# --- Rollups & retention --------------------------------------------------------


def _extra_object() -> Any:
    """JSONB object mapping every metric to its min/max aggregate."""
    parts: list[Any] = []
    for metric in METRIC_COLUMNS:
        col = getattr(MetricSnapshot, metric)
        parts.extend((metric, func.jsonb_build_object("min", func.min(col), "max", func.max(col))))
    return func.jsonb_build_object(*parts)


async def _rollup(
    db: AsyncSession,
    *,
    source: MetricGranularity,
    target: MetricGranularity,
    cutoff: datetime,
    horizon: datetime,
    unit: str,
    prefix: str,
) -> dict[str, int]:
    """Aggregate *source* rows older than *cutoff* into *target* buckets.

    Deletes pre-existing target rows covering affected buckets, then performs a
    set-based INSERT SELECT (avg into primary columns, min/max into the JSONB
    extra map). No row loops; caller commits.
    """
    src = MetricSnapshot
    bucket = func.date_trunc(unit, src.recorded_at)
    source_where = (
        src.granularity == source.value,
        src.recorded_at < cutoff,
        src.recorded_at >= horizon,
    )

    affected_buckets = select(bucket.label("b")).where(*source_where)
    deleted_res = await db.execute(
        delete(MetricSnapshot).where(
            MetricSnapshot.granularity == target.value,
            MetricSnapshot.recorded_at.in_(affected_buckets),
        )
    )

    select_columns: list[Any] = [
        src.server_id,
        literal(target.value, String),
        bucket,
        *(func.avg(getattr(src, m)) for m in METRIC_COLUMNS),
        _extra_object(),
    ]
    insert_stmt = pg_insert(MetricSnapshot).from_select(
        ["server_id", "granularity", "recorded_at", *METRIC_COLUMNS, "extra"],
        select(*select_columns).where(*source_where).group_by(src.server_id, bucket),
    )
    inserted_res = await db.execute(insert_stmt)
    return {
        f"{prefix}_replaced": max(cast(CursorResult[Any], deleted_res).rowcount or 0, 0),
        f"{prefix}_inserted": max(cast(CursorResult[Any], inserted_res).rowcount or 0, 0),
    }


async def _prune(db: AsyncSession, granularity: MetricGranularity, older_than: timedelta) -> int:
    """Delete one granularity's rows past their retention window."""
    threshold = datetime.now(UTC) - older_than
    res = await db.execute(
        delete(MetricSnapshot).where(
            MetricSnapshot.granularity == granularity.value,
            MetricSnapshot.recorded_at < threshold,
        )
    )
    return max(cast(CursorResult[Any], res).rowcount or 0, 0)


async def aggregate_rollups(db: AsyncSession) -> dict[str, int]:
    """Build HOURLY/DAILY rollups and enforce retention. Caller commits.

    - HOURLY from RAW older than 90 minutes, bucketed by hour.
    - DAILY from HOURLY older than 48 hours, bucketed by day.
    - Prune RAW / HOURLY / DAILY per configured retention (DAILY keeps 365d).
    """
    settings = get_settings()
    now = datetime.now(UTC)
    counts: dict[str, int] = {}

    counts.update(
        await _rollup(
            db,
            source=MetricGranularity.RAW,
            target=MetricGranularity.HOURLY,
            cutoff=now - timedelta(minutes=90),
            horizon=now - timedelta(hours=settings.raw_metric_retention_hours + 1),
            unit="hour",
            prefix="hourly",
        )
    )
    counts.update(
        await _rollup(
            db,
            source=MetricGranularity.HOURLY,
            target=MetricGranularity.DAILY,
            cutoff=now - timedelta(hours=48),
            horizon=now - timedelta(days=settings.hourly_metric_retention_days + 1),
            unit="day",
            prefix="daily",
        )
    )

    counts["pruned_raw"] = await _prune(
        db, MetricGranularity.RAW, timedelta(hours=settings.raw_metric_retention_hours)
    )
    counts["pruned_hourly"] = await _prune(
        db, MetricGranularity.HOURLY, timedelta(days=settings.hourly_metric_retention_days)
    )
    counts["pruned_daily"] = await _prune(db, MetricGranularity.DAILY, timedelta(days=365))
    log.debug("rollups_aggregated", **counts)
    return counts


# --- Dashboard ------------------------------------------------------------------


def _utc_midnight(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def dashboard_summary(db: AsyncSession, ctx: AuthContext) -> dict[str, Any]:
    """Fleet-wide counters for the operator landing page (read-only).

    CPU/memory averages are omitted (None) when the caller lacks
    ``metric.read``; every other counter is plain status data.
    """
    by_status = {
        status: count
        for status, count in (
            await db.execute(select(Server.status, func.count()).group_by(Server.status))
        ).all()
    }
    monitors = {
        status: count
        for status, count in (
            await db.execute(select(Monitor.status, func.count()).group_by(Monitor.status))
        ).all()
    }
    midnight = _utc_midnight(datetime.now(UTC))

    avg_cpu: float | None = None
    avg_mem: float | None = None
    if ctx.has_permission("metric.read"):
        online_ids = list(
            (
                await db.execute(
                    select(Server.id).where(Server.status == ServerStatus.ONLINE.value)
                )
            ).scalars()
        )
        snapshots = await latest_for_servers(db, online_ids)
        if snapshots:
            avg_cpu = round(fmean(s.cpu_percent for s in snapshots.values()), 2)
            avg_mem = round(fmean(s.mem_percent for s in snapshots.values()), 2)

    events = (
        (
            await db.execute(
                select(SystemEvent)
                .order_by(SystemEvent.created_at.desc(), SystemEvent.id.desc())
                .limit(12)
            )
        )
        .scalars()
        .all()
    )

    async def scalar_count(stmt: Select[tuple]) -> int:
        return int((await db.execute(stmt)).scalar_one())

    containers_running = await scalar_count(
        select(func.count())
        .select_from(Container)
        .where(Container.status == ContainerStatus.RUNNING.value)
    )
    incidents_open = await scalar_count(
        select(func.count())
        .select_from(Incident)
        .where(Incident.status == IncidentStatus.OPEN.value)
    )
    deployments_today = await scalar_count(
        select(func.count()).select_from(Deployment).where(Deployment.created_at >= midnight)
    )
    deployments_failed_today = await scalar_count(
        select(func.count())
        .select_from(Deployment)
        .where(
            Deployment.created_at >= midnight, Deployment.status == DeploymentStatus.FAILED.value
        )
    )
    unread_alerts = await scalar_count(
        select(func.count()).select_from(Alert).where(Alert.read_at.is_(None))
    )

    return {
        "servers_total": sum(by_status.values()),
        "servers_online": by_status.get(ServerStatus.ONLINE.value, 0),
        "servers_offline": by_status.get(ServerStatus.OFFLINE.value, 0),
        "servers_degraded": by_status.get(ServerStatus.DEGRADED.value, 0),
        "containers_running": containers_running,
        "monitors_up": monitors.get("UP", 0),
        "monitors_down": monitors.get("DOWN", 0),
        "monitors_paused": monitors.get("PAUSED", 0),
        "incidents_open": incidents_open,
        "deployments_today": deployments_today,
        "deployments_failed_today": deployments_failed_today,
        "avg_cpu_percent": avg_cpu,
        "avg_mem_percent": avg_mem,
        "unread_alerts": unread_alerts,
        "recent_events": [
            {
                "id": event.id,
                "type": event.type,
                "level": event.level.value if hasattr(event.level, "value") else str(event.level),
                "message": event.message,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "created_at": event.created_at,
            }
            for event in events
        ],
    }
