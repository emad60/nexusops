"""Uptime monitor endpoints: CRUD, checks, incidents, uptime aggregates."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import AuthContext, DbSessionDep, require_permission
from app.core.errors import NotFound
from app.core.pagination import (
    CursorPage,
    CursorParams,
    Page,
    PageParams,
    cursor_params,
    page_params,
)
from app.models.enums import MonitorStatus
from app.schemas.incident import IncidentOut
from app.schemas.monitor import (
    MonitorCheckOut,
    MonitorCreate,
    MonitorOut,
    MonitorUpdate,
    UptimeSummary,
)
from app.services import incident_service, monitor_service

router = APIRouter(prefix="/monitors", tags=["monitors"])

DbDep = DbSessionDep
ReadCtx = Annotated[AuthContext, Depends(require_permission("monitor.read"))]
ManageCtx = Annotated[AuthContext, Depends(require_permission("monitor.manage"))]


def _to_out(monitor, deco: dict) -> MonitorOut:
    out = MonitorOut.model_validate(monitor)
    if monitor.project_id is not None:
        out.project_name = deco["projects"].get(monitor.project_id)
    out.current_open_incident_id = deco["incidents"].get(monitor.id)
    out.uptime_pct_24h = deco["uptime"].get(monitor.id)
    return out


@router.get("", response_model=Page[MonitorOut])
async def list_monitors(
    db: DbDep,
    ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: MonitorStatus | None = Query(None, alias="status"),
    project_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None, max_length=200),
    sort: str = Query("created_at", pattern="^-?(created_at|name|status|next_check_at)$"),
) -> Page[MonitorOut]:
    """List monitors with filters and cheap per-row aggregates."""
    rows, total = await monitor_service.list_monitors(
        db,
        status_filter=status_filter,
        project_id=project_id,
        q=q,
        sort=sort,
        limit=params.limit,
        offset=params.offset,
    )
    deco = await monitor_service.page_decorations(db, rows)
    return Page(
        items=[_to_out(m, deco) for m in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.post("", response_model=MonitorOut, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    data: MonitorCreate, request: Request, db: DbDep, ctx: ManageCtx
) -> MonitorOut:
    """Create a monitor; the URL is validated by the SSRF guard."""
    monitor = await monitor_service.create_monitor(db, ctx, data, request=request)
    return _to_out(monitor, {"projects": {}, "incidents": {}, "uptime": {}})


@router.get("/{monitor_id}", response_model=MonitorOut)
async def get_monitor(db: DbDep, ctx: ReadCtx, monitor_id: uuid.UUID) -> MonitorOut:
    monitor = await monitor_service.require_monitor(db, monitor_id)
    deco = await monitor_service.page_decorations(db, [monitor])
    return _to_out(monitor, deco)


@router.patch("/{monitor_id}", response_model=MonitorOut)
async def update_monitor(
    data: MonitorUpdate, request: Request, db: DbDep, ctx: ManageCtx, monitor_id: uuid.UUID
) -> MonitorOut:
    monitor = await monitor_service.require_monitor(db, monitor_id)
    updated = await monitor_service.update_monitor(db, ctx, monitor, data, request=request)
    deco = await monitor_service.page_decorations(db, [updated])
    return _to_out(updated, deco)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    request: Request, db: DbDep, ctx: ManageCtx, monitor_id: uuid.UUID
) -> Response:
    monitor = await monitor_service.require_monitor(db, monitor_id)
    await monitor_service.delete_monitor(db, ctx, monitor, request=request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{monitor_id}/pause", response_model=MonitorOut)
async def pause_monitor(
    request: Request, db: DbDep, ctx: ManageCtx, monitor_id: uuid.UUID
) -> MonitorOut:
    monitor = await monitor_service.require_monitor(db, monitor_id)
    paused = await monitor_service.pause_monitor(db, ctx, monitor, request=request)
    return MonitorOut.model_validate(paused)


@router.post("/{monitor_id}/resume", response_model=MonitorOut)
async def resume_monitor(
    request: Request, db: DbDep, ctx: ManageCtx, monitor_id: uuid.UUID
) -> MonitorOut:
    monitor = await monitor_service.require_monitor(db, monitor_id)
    resumed = await monitor_service.resume_monitor(db, ctx, monitor, request=request)
    return MonitorOut.model_validate(resumed)


@router.post("/{monitor_id}/check-now", response_model=MonitorCheckOut)
async def check_now(db: DbDep, ctx: ManageCtx, monitor_id: uuid.UUID) -> MonitorCheckOut:
    """Run one check inline and return its result."""
    await monitor_service.require_monitor(db, monitor_id)
    check = await monitor_service.run_check(db, monitor_id)
    if check is None:
        raise NotFound("Monitor is paused or already being checked by another runner")
    return MonitorCheckOut.model_validate(check)


@router.get("/{monitor_id}/checks", response_model=CursorPage[MonitorCheckOut])
async def list_checks(
    db: DbDep,
    ctx: ReadCtx,
    monitor_id: uuid.UUID,
    params: Annotated[CursorParams, Depends(cursor_params)],
) -> CursorPage[MonitorCheckOut]:
    """Keyset-paged check history for one monitor (newest first)."""
    await monitor_service.require_monitor(db, monitor_id)
    rows, next_cursor, has_more = await monitor_service.list_checks(db, monitor_id, params)
    return CursorPage(
        items=[MonitorCheckOut.model_validate(r) for r in rows],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/{monitor_id}/incidents", response_model=Page[IncidentOut])
async def list_monitor_incidents(
    db: DbDep,
    ctx: ReadCtx,
    monitor_id: uuid.UUID,
    params: Annotated[PageParams, Depends(page_params)],
) -> Page[IncidentOut]:
    await monitor_service.require_monitor(db, monitor_id)
    rows, total = await incident_service.list_incidents(
        db, monitor_id=monitor_id, limit=params.limit, offset=params.offset
    )
    names = await incident_service.monitor_names(db, rows)
    items = []
    for incident in rows:
        out = IncidentOut.model_validate(incident)
        out.monitor_name = names.get(incident.monitor_id)
        items.append(out)
    return Page(items=items, total=total, limit=params.limit, offset=params.offset)


@router.get("/{monitor_id}/uptime", response_model=UptimeSummary)
async def uptime(
    db: DbDep, ctx: ReadCtx, monitor_id: uuid.UUID, hours: int = Query(24, ge=1, le=720)
) -> UptimeSummary:
    await monitor_service.require_monitor(db, monitor_id)
    summary = await monitor_service.uptime_summary(db, monitor_id, hours)
    return UptimeSummary.model_validate(summary)
