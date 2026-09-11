"""System events API: cursor-paginated feed + canonical type catalogue."""

from __future__ import annotations

import base64
import binascii
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import literal, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.errors import BadRequest
from app.core.pagination import CursorPage, CursorParams, cursor_params
from app.models import SystemEvent
from app.models.enums import EventLevel
from app.schemas.event import EventOut, EventTypeOut
from app.services.event_registry import event_type_catalogue

events_router = APIRouter(prefix="/events", tags=["events"])

DbSession = Annotated[AsyncSession, Depends(get_session)]
CursorParamsDep = Annotated[CursorParams, Depends(cursor_params)]

MAX_TYPES_FILTER = 32


def _encode_cursor(ts: datetime, id_: uuid.UUID) -> str:
    """Opaque keyset cursor for (created_at DESC, id DESC) streams."""
    raw = f"{ts.isoformat()}|{id_}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, id_str = raw.rsplit("|", 1)
        return datetime.fromisoformat(ts_str), uuid.UUID(id_str)
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise BadRequest("Malformed pagination cursor", code="INVALID_CURSOR") from exc


@events_router.get("/types", response_model=list[EventTypeOut])
async def list_event_types(
    ctx: Annotated[AuthContext, Depends(require_permission("event.read"))],
) -> list[EventTypeOut]:
    """Canonical event types with descriptions (for UI filter dropdowns)."""
    return [EventTypeOut.model_validate(item) for item in event_type_catalogue()]


@events_router.get("", response_model=CursorPage[EventOut])
async def list_events(
    ctx: Annotated[AuthContext, Depends(require_permission("event.read"))],
    db: DbSession,
    params: CursorParamsDep,
    types: str | None = Query(None, description="Comma-separated event types"),
    level: EventLevel | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    actor_id: uuid.UUID | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
) -> CursorPage[EventOut]:
    """Newest-first system events, keyset-paginated on (created_at DESC, id DESC)."""
    stmt = select(SystemEvent).order_by(SystemEvent.created_at.desc(), SystemEvent.id.desc())

    if types:
        wanted = [t.strip() for t in types.split(",") if t.strip()][:MAX_TYPES_FILTER]
        if wanted:
            stmt = stmt.where(SystemEvent.type.in_(wanted))
    if level is not None:
        stmt = stmt.where(SystemEvent.level == level.value)
    if resource_type:
        stmt = stmt.where(SystemEvent.resource_type == resource_type)
    if resource_id:
        stmt = stmt.where(SystemEvent.resource_id == resource_id)
    if actor_id is not None:
        stmt = stmt.where(SystemEvent.actor_id == actor_id)
    if since is not None:
        stmt = stmt.where(SystemEvent.created_at >= since)
    if until is not None:
        stmt = stmt.where(SystemEvent.created_at <= until)

    if params.cursor:
        cursor_ts, cursor_id = _decode_cursor(params.cursor)
        # literal() produces the same bind params the plain-value coercion does.
        stmt = stmt.where(
            tuple_(SystemEvent.created_at, SystemEvent.id)
            < tuple_(literal(cursor_ts), literal(cursor_id))
        )

    rows = (await db.execute(stmt.limit(params.limit + 1))).scalars().all()
    has_more = len(rows) > params.limit
    items = rows[: params.limit]
    next_cursor = _encode_cursor(items[-1].created_at, items[-1].id) if has_more and items else None
    return CursorPage(
        items=[EventOut.model_validate(row, from_attributes=True) for row in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )
