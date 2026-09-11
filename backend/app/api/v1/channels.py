"""Notification channel endpoints. Config is write-only; never echoed back."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import func, select

from app.api.deps import AuthContext, DbSessionDep, require_permission
from app.core.pagination import (
    CursorPage,
    CursorParams,
    Page,
    PageParams,
    cursor_params,
    page_params,
)
from app.models import NotificationChannel
from app.models.enums import DeliveryStatus
from app.schemas.channel import (
    ChannelCreate,
    ChannelOut,
    ChannelUpdate,
    DeliveryOut,
    TestNotificationOut,
)
from app.services import notification_service

router = APIRouter(prefix="/notification-channels", tags=["notification-channels"])

DbDep = DbSessionDep
ReadCtx = Annotated[AuthContext, Depends(require_permission("channel.read"))]
ManageCtx = Annotated[AuthContext, Depends(require_permission("channel.manage"))]


@router.get("", response_model=Page[ChannelOut])
async def list_channels(
    db: DbDep, ctx: ReadCtx, params: Annotated[PageParams, Depends(page_params)]
) -> Page[ChannelOut]:
    stmt = select(NotificationChannel).order_by(NotificationChannel.created_at.desc())
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    rows = (await db.execute(stmt.limit(params.limit).offset(params.offset))).scalars().all()
    return Page(
        items=[ChannelOut.model_validate(r) for r in rows],
        total=int(total),
        limit=params.limit,
        offset=params.offset,
    )


@router.post("", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: ChannelCreate, request: Request, db: DbDep, ctx: ManageCtx
) -> ChannelOut:
    """Create a channel; webhook URLs pass the SSRF guard before storage."""
    channel = await notification_service.create_channel(db, ctx, data, request=request)
    return ChannelOut.model_validate(channel)


# NOTE: /deliveries is declared before /{channel_id} so the literal wins.
@router.get("/deliveries", response_model=CursorPage[DeliveryOut])
async def list_deliveries(
    db: DbDep,
    ctx: ReadCtx,
    params: Annotated[CursorParams, Depends(cursor_params)],
    channel_id: uuid.UUID | None = Query(None),
    status_filter: DeliveryStatus | None = Query(None, alias="status"),
) -> CursorPage[DeliveryOut]:
    """Keyset-paged delivery log (most recently scheduled first)."""
    rows, next_cursor, has_more = await notification_service.list_deliveries(
        db, channel_id=channel_id, status=status_filter, params=params
    )
    return CursorPage(
        items=[DeliveryOut.model_validate(r) for r in rows],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/{channel_id}", response_model=ChannelOut)
async def get_channel(db: DbDep, ctx: ReadCtx, channel_id: uuid.UUID) -> ChannelOut:
    channel = await notification_service.require_channel(db, channel_id)
    return ChannelOut.model_validate(channel)


@router.patch("/{channel_id}", response_model=ChannelOut)
async def update_channel(
    data: ChannelUpdate, request: Request, db: DbDep, ctx: ManageCtx, channel_id: uuid.UUID
) -> ChannelOut:
    channel = await notification_service.require_channel(db, channel_id)
    updated = await notification_service.update_channel(db, ctx, channel, data, request=request)
    return ChannelOut.model_validate(updated)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    request: Request, db: DbDep, ctx: ManageCtx, channel_id: uuid.UUID
) -> Response:
    channel = await notification_service.require_channel(db, channel_id)
    await notification_service.delete_channel(db, ctx, channel, request=request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{channel_id}/test", response_model=TestNotificationOut)
async def test_channel(
    request: Request, db: DbDep, ctx: ManageCtx, channel_id: uuid.UUID
) -> TestNotificationOut:
    """Send a test notification through the channel's real transport."""
    channel = await notification_service.require_channel(db, channel_id)
    result_status, error = await notification_service.send_test_notification(
        db, ctx, channel, request=request
    )
    return TestNotificationOut(status=result_status, error=error or None)
