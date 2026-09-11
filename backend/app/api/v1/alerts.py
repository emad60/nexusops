"""Alert inbox endpoints. Authenticated users see the shared operator feed."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSessionDep
from app.core.pagination import Page, PageParams, page_params
from app.models import Alert
from app.schemas.alert import AlertOut, UnreadCountOut
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])

DbDep = DbSessionDep


@router.get("", response_model=Page[AlertOut])
async def list_alerts(
    db: DbDep,
    ctx: CurrentUser,
    params: Annotated[PageParams, Depends(page_params)],
) -> Page[AlertOut]:
    """Unread alerts first, then newest first."""
    stmt = select(Alert).order_by(Alert.read_at.asc().nulls_first(), Alert.created_at.desc())
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    rows = (await db.execute(stmt.limit(params.limit).offset(params.offset))).scalars().all()
    return Page(
        items=[AlertOut.model_validate(r) for r in rows],
        total=int(total),
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/unread-count", response_model=UnreadCountOut)
async def unread_count(db: DbDep, ctx: CurrentUser) -> UnreadCountOut:
    return UnreadCountOut(count=await alert_service.unread_count(db))


@router.post("/{alert_id}/read", response_model=AlertOut)
async def mark_read(db: DbDep, ctx: CurrentUser, alert_id: uuid.UUID) -> AlertOut:
    alert = await alert_service.mark_read(db, alert_id)
    return AlertOut.model_validate(alert)


@router.post("/read-all", response_model=UnreadCountOut)
async def mark_all_read(db: DbDep, ctx: CurrentUser) -> UnreadCountOut:
    """Mark every unread alert read; returns how many rows changed."""
    marked = await alert_service.mark_all_read(db)
    return UnreadCountOut(count=marked)
