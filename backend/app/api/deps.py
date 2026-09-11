"""FastAPI dependencies: database session, authentication context, RBAC gate.

Authentication accepts either:
  * ``Authorization: Bearer <jwt>`` (SPA in-memory access token), or
  * ``X-API-Key: nxo_...`` (machine clients).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import Forbidden, Unauthorized
from app.core.permissions import WILDCARD, scope_matches
from app.core.rate_limit import client_ip
from app.core.security import decode_access_token, hash_token
from app.models import ApiKey, User
from app.models import Session as DbSession

DbSessionDep = Annotated[AsyncSession, Depends(get_session)]


@dataclass(slots=True)
class AuthContext:
    """Resolved identity attached to every authenticated request."""

    user: User
    actor_type: str = "USER"  # USER | API_KEY
    api_key: ApiKey | None = None
    session_id: uuid.UUID | None = None
    _permission_set: set[str] = field(default_factory=set, repr=False)

    @property
    def user_id(self) -> uuid.UUID:
        return self.user.id

    @property
    def email(self) -> str:
        return self.user.email

    def has_permission(self, codename: str) -> bool:
        # API keys are scoped intersections: both the key scope AND the
        # owning user's role must allow the action. The scope check comes
        # FIRST — even a superadmin-owned key can never exceed its grant,
        # so a leaked least-privilege machine key stays least-privilege.
        if self.api_key is not None and not scope_matches(
            list(self.api_key.scopes or []), codename
        ):
            return False
        if self.user.is_superadmin:
            return True
        return (
            WILDCARD in self._permission_set
            or codename in self._permission_set
            or any(p.endswith("*") and codename.startswith(p[:-1]) for p in self._permission_set)
        )


async def _load_permissions(db: AsyncSession, ctx: AuthContext) -> None:
    if ctx.user.is_superadmin:
        ctx._permission_set = {WILDCARD}
        return
    # User.role and Role.permissions are both lazy="selectin", so after any
    # query-loaded user these attributes are already in memory — no IO needed.
    role = ctx.user.role
    if role is None:
        return
    ctx._permission_set = {p.codename for p in role.permissions}


async def resolve_auth(request: Request, db: AsyncSession) -> AuthContext:
    """Resolve Bearer JWT or X-API-Key into an :class:`AuthContext`."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header[7:].strip() if auth_header.lower().startswith("bearer ") else ""
    api_key_raw = request.headers.get("x-api-key", "")

    if api_key_raw:
        key_hash = hash_token(api_key_raw)
        row = (
            await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        ).scalar_one_or_none()
        if row is None or row.revoked_at is not None:
            raise Unauthorized("Invalid API key")
        now = datetime.now(UTC)
        if row.expires_at is not None and row.expires_at < now:
            raise Unauthorized("API key expired")
        user = (await db.execute(select(User).where(User.id == row.user_id))).scalar_one_or_none()
        if user is None or not user.is_active:
            raise Unauthorized("API key owner is inactive")
        ctx = AuthContext(user=user, actor_type="API_KEY", api_key=row)
        # Throttle last_used_at writes to at most once per minute per key.
        if row.last_used_at is None or (now - row.last_used_at).total_seconds() > 60:
            row.last_used_at = now
            await db.commit()
        await _load_permissions(db, ctx)
        return ctx

    if not token:
        raise Unauthorized()

    payload = decode_access_token(token)  # raises Unauthorized on any problem
    try:
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
    except (KeyError, ValueError) as exc:
        raise Unauthorized("Malformed token claims") from exc

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise Unauthorized("Account is inactive")

    sess = (
        await db.execute(select(DbSession).where(DbSession.id == session_id))
    ).scalar_one_or_none()
    if sess is None or sess.revoked_at is not None:
        raise Unauthorized("Session revoked")
    now = datetime.now(UTC)
    if sess.expires_at < now:
        raise Unauthorized("Session expired")
    sess.last_seen_at = now

    request.state.user_id = str(user_id)
    ctx = AuthContext(user=user, actor_type="USER", session_id=session_id)
    await _load_permissions(db, ctx)
    return ctx


async def get_current_user(request: Request, db: DbSessionDep) -> AuthContext:
    """Standard authentication dependency. Also records client IP for logs/audit."""
    request.state.client_ip = client_ip(request)
    return await resolve_auth(request, db)


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]


async def get_optional_user(request: Request, db: DbSessionDep) -> AuthContext | None:
    """Like :func:`get_current_user` but returns ``None`` for anonymous callers."""
    try:
        request.state.client_ip = client_ip(request)
        return await resolve_auth(request, db)
    except Unauthorized:
        return None


OptionalUser = Annotated[AuthContext | None, Depends(get_optional_user)]


def require_permission(codename: str) -> Callable[[AuthContext], Awaitable[AuthContext]]:
    """Dependency factory enforcing a permission; returns 403 when denied."""

    async def _check(ctx: CurrentUser) -> AuthContext:
        if not ctx.has_permission(codename):
            raise Forbidden(f"Missing required permission: {codename}", code="PERMISSION_DENIED")
        return ctx

    return _check


def permission_dep(codename: str) -> Any:  # convenience alias for readability
    return Depends(require_permission(codename))
