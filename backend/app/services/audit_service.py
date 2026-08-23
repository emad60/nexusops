"""Audit trail writer. Append-only; the DB blocks UPDATE/DELETE via trigger."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.logging import get_logger, redact_mapping
from app.models import AuditLog
from app.models.enums import AuditResult

log = get_logger("nexusops.audit")


async def record(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | str | None = None,
    result: AuditResult = AuditResult.SUCCESS,
    metadata: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Append an audit row using the caller's transaction (no commit here).

    Sensitive keys in *metadata* are redacted before persistence.
    """
    ip = ""
    user_agent = ""
    if request is not None:
        ip = getattr(request.state, "client_ip", "") or (
            request.client.host if request.client else ""
        )
        user_agent = (request.headers.get("user-agent") or "")[:400]

    entry = AuditLog(
        actor_id=ctx.user_id if ctx else None,
        actor_email=ctx.email if ctx else "system",
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=ip,
        user_agent=user_agent,
        result=result,
        metadata_=redact_mapping(metadata or {}),
    )
    db.add(entry)
    await db.flush()
    log.info(
        "audit",
        action=action,
        actor=entry.actor_email,
        resource=f"{resource_type}:{resource_id}" if resource_type else None,
        result=result.value,
    )
    return entry
