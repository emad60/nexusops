"""Audit trail writer. Append-only; the DB blocks UPDATE/DELETE via trigger."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.client_ip import resolve_client_ip
from app.core.logging import get_logger, redact_mapping
from app.core.tenancy import current_org
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
    org_id: uuid.UUID | None = None,
    actor_email: str | None = None,
) -> AuditLog:
    """Append an audit row using the caller's transaction (no commit here).

    The organization comes from the caller's **membership** (never from the
    request body or a path parameter), falling back to the active tenancy scope
    for worker-initiated rows. ``org_id`` stays NULL only for genuinely
    instance-level events — a failed login for an address that has no account,
    a refresh-token replay — which are written from ``system_write_scope`` and
    are consequently invisible to every tenant.

    Sensitive keys in *metadata* are redacted before persistence.

    ``actor_email`` overrides the derived actor for callers that have no
    ``AuthContext`` — a node agent reporting an operation result is the one case,
    and it records itself as ``agent:<node>`` rather than the anonymous
    "system" it would otherwise fall back to. ``ctx`` still wins when present.
    """
    if org_id is None:
        org_id = ctx.org_id if ctx is not None else None
    if org_id is None:
        org_id = current_org()

    ip = ""
    user_agent = ""
    if request is not None:
        # state.client_ip is set by the auth dependencies; anonymous routes
        # (login, register, refresh) never pass through them, so fall back to
        # the chain-aware resolver. request.client.host would record the edge
        # proxy's docker-network address, not the real client.
        ip = getattr(request.state, "client_ip", "") or resolve_client_ip(request)
        user_agent = (request.headers.get("user-agent") or "")[:400]

    entry = AuditLog(
        org_id=org_id,
        actor_id=ctx.user_id if ctx else None,
        actor_email=ctx.email if ctx else (actor_email or "system"),
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
