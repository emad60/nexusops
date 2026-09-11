"""Pagination primitives: offset pages and keyset cursor pages."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

MAX_LIMIT = 100
DEFAULT_LIMIT = 25


@dataclass(frozen=True, slots=True)
class PageParams:
    limit: int = DEFAULT_LIMIT
    offset: int = 0


def page_params(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


class Page(BaseModel, Generic[T]):  # noqa: UP046 - pydantic v2 generic model
    items: list[T]
    total: int
    limit: int
    offset: int


async def paginate(session: AsyncSession, stmt: Select, params: PageParams) -> tuple[list, int]:
    """Execute *stmt* with limit/offset and return ``(rows, total)``."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await session.execute(count_stmt)).scalar_one()
    rows = (await session.execute(stmt.limit(params.limit).offset(params.offset))).scalars().all()
    return list(rows), total


# --- Cursor (keyset) pagination for high-volume streams -----------------------


@dataclass(frozen=True, slots=True)
class CursorParams:
    limit: int = DEFAULT_LIMIT
    cursor: str | None = None


@dataclass(frozen=True, slots=True)
class Cursor:
    ts: datetime
    id: int


def encode_cursor(ts: datetime, id_: int) -> str:
    raw = f"{ts.isoformat()}|{id_}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str | None) -> Cursor | None:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, id_str = raw.rsplit("|", 1)
        return Cursor(ts=datetime.fromisoformat(ts_str), id=int(id_str))
    except (ValueError, binascii.Error, UnicodeDecodeError):
        return None


def cursor_params(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    cursor: str | None = Query(None),
) -> CursorParams:
    return CursorParams(limit=limit, cursor=cursor)


class CursorPage(BaseModel, Generic[T]):  # noqa: UP046 - pydantic v2 generic model
    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
