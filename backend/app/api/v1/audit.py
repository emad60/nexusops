"""Audit log API. Strictly read-only: the table is append-only by design."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params, paginate
from app.models import AuditLog
from app.models.enums import AuditResult
from app.schemas.audit import AuditOut

audit_router = APIRouter(prefix="/audit-logs", tags=["audit"])

DbSession = Annotated[AsyncSession, Depends(get_session)]
PageParamsDep = Annotated[PageParams, Depends(page_params)]


@audit_router.get("", response_model=Page[AuditOut])
async def list_audit_logs(
    ctx: Annotated[AuthContext, Depends(require_permission("audit.read"))],
    db: DbSession,
    params: PageParamsDep,
    actor_email: str | None = Query(None, description="Case-insensitive substring match"),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    result: AuditResult | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
) -> Page[AuditOut]:
    """Newest-first audit trail with optional filters.

    No write routes exist for this resource — the audit table is immutable.
    """
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if actor_email:
        stmt = stmt.where(AuditLog.actor_email.ilike(f"%{actor_email}%"))
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if resource_id:
        stmt = stmt.where(AuditLog.resource_id == resource_id)
    if result is not None:
        stmt = stmt.where(AuditLog.result == result.value)
    if since is not None:
        stmt = stmt.where(AuditLog.created_at >= since)
    if until is not None:
        stmt = stmt.where(AuditLog.created_at <= until)

    rows, total = await paginate(db, stmt, params)
    return Page(
        items=[AuditOut.model_validate(row, from_attributes=True) for row in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )
