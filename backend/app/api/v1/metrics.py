"""Metrics query API: server timeseries, latest snapshot, dashboard summary."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, CurrentUser, require_permission
from app.core.db import get_session
from app.core.errors import NotFound
from app.schemas.metric import DashboardSummary, MetricSnapshotOut, Timeseries
from app.services import metrics_service

DbDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="", tags=["metrics"])

METRIC_CSV_DEFAULT = "cpu_percent,mem_percent"


@router.get("/servers/{server_id}/metrics", response_model=Timeseries)
async def get_server_metrics(
    server_id: UUID,
    ctx: Annotated[AuthContext, Depends(require_permission("metric.read"))],
    db: DbDep,
    range: str = Query("24h", description=f"One of {', '.join(metrics_service.RANGE_MAP)}"),
    metrics: str = Query(
        METRIC_CSV_DEFAULT,
        description=f"Comma-separated subset of {', '.join(metrics_service.METRIC_COLUMNS)}",
    ),
) -> Timeseries:
    """Aggregated metric series for one server (bucket count kept <= 400)."""
    await metrics_service.ensure_server(db, server_id)
    requested = tuple(m.strip() for m in metrics.split(",") if m.strip()) or (
        "cpu_percent",
        "mem_percent",
    )
    data = await metrics_service.timeseries(db, server_id, range_key=range, metrics=requested)
    return Timeseries.model_validate(data)


@router.get("/servers/{server_id}/metrics/latest", response_model=MetricSnapshotOut)
async def get_latest_server_metrics(
    server_id: UUID,
    ctx: Annotated[AuthContext, Depends(require_permission("metric.read"))],
    db: DbDep,
) -> MetricSnapshotOut:
    """Most recent raw agent sample for one server."""
    await metrics_service.ensure_server(db, server_id)
    snapshots = await metrics_service.latest_for_servers(db, [server_id])
    snapshot = snapshots.get(server_id)
    if snapshot is None:
        raise NotFound("No metrics recorded for this server yet")
    return MetricSnapshotOut.model_validate(snapshot, from_attributes=True)


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(ctx: CurrentUser, db: DbDep) -> DashboardSummary:
    """Fleet counters for the landing page.

    CPU/memory averages are omitted when the caller lacks ``metric.read``.
    """
    return DashboardSummary.model_validate(await metrics_service.dashboard_summary(db, ctx))
