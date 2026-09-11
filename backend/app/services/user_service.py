"""User account management: listing, invites, updates, deactivation and guards.

Also hosts the account-credential plumbing shared across domains: the password
policy, session listing and session/token revocation (a session is a
credential of the user, so its lifecycle belongs here). ``auth_service``
imports from this module — never the reverse.

Object-level guards enforced here (never trusting router checks alone):
  * a caller cannot deactivate their own account;
  * the last active superadmin can neither be deactivated nor moved off the
    superadmin flag by a role change;
  * revoking another user's session requires ``user.manage``.
"""

from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.core.pagination import PageParams, paginate
from app.core.security import hash_password
from app.models import RefreshToken, Role, User
from app.models import Session as DbSession
from app.models.enums import ActorType, EventLevel, UserStatus
from app.services import api_key_service, audit_service, event_bus

PASSWORD_POLICY_MESSAGE = (
    "Password must be at least 10 characters long"  # noqa: S105 - policy text, not a credential
    " and contain both letters and digits"
)
_LETTER_RE = re.compile(r"[A-Za-z]")
_DIGIT_RE = re.compile(r"\d")


def validate_password_policy(password: str) -> None:
    """Enforce the password policy; raises BadRequest(code=PASSWORD_POLICY)."""
    if len(password) < 10 or not _LETTER_RE.search(password) or not _DIGIT_RE.search(password):
        raise BadRequest(PASSWORD_POLICY_MESSAGE, code="PASSWORD_POLICY")


# --- Users ---------------------------------------------------------------------


async def get_user(db: AsyncSession, user_id: UUID) -> User:
    """Fetch a user or raise NotFound."""
    user = await db.get(User, user_id)
    if user is None:
        raise NotFound("User not found", code="USER_NOT_FOUND")
    return user


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Case-insensitive lookup by email."""
    return (
        await db.execute(select(User).where(User.email == email.strip().lower()))
    ).scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    *,
    params: PageParams,
    q: str | None = None,
    is_active: bool | None = None,
    role_id: UUID | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[User], int]:
    """Paginated user listing with optional text/status/role filters."""
    stmt = select(User)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    if role_id is not None:
        stmt = stmt.where(User.role_id == role_id)

    sort_column: Any = {"created_at": User.created_at, "email": User.email}[sort]
    stmt = stmt.order_by(sort_column.desc() if order == "desc" else sort_column.asc())
    return await paginate(db, stmt, params)


async def create_user(
    db: AsyncSession,
    *,
    actor: AuthContext,
    email: str,
    password: str | None,
    full_name: str = "",
    role_id: UUID,
    request: Request | None = None,
) -> tuple[User, str | None]:
    """Invite a user. When *password* is None one is generated and returned once.

    The generated password never enters audit metadata.
    """
    email_norm = email.strip().lower()
    if await get_by_email(db, email_norm) is not None:
        raise Conflict("Email already registered", code="EMAIL_TAKEN")
    role = await db.get(Role, role_id)
    if role is None:
        raise NotFound("Role not found", code="ROLE_NOT_FOUND")

    initial_password: str | None = None
    effective_password = password
    if password is None:
        initial_password = secrets.token_urlsafe(12)
        effective_password = initial_password
    else:
        validate_password_policy(password)

    now = datetime.now(UTC)
    user = User(
        email=email_norm,
        password_hash=hash_password(cast(str, effective_password)),
        full_name=(full_name or "").strip()[:160],
        is_active=True,
        status=UserStatus.ACTIVE,
        role_id=role.id,
        created_at=now,
        updated_at=now,
    )
    # selectin loading never fires on flush; keep the relationship populated
    # for immediate serialization.
    user.role = role
    db.add(user)
    await db.flush()

    await audit_service.record(
        db,
        actor,
        action="user.create",
        resource_type="user",
        resource_id=user.id,
        metadata={
            "email": email_norm,
            "role_id": str(role.id),
            "generated_password": initial_password is not None,
        },
        request=request,
    )
    await event_bus.publish(
        db,
        type="USER_CREATED",
        message=f"User {email_norm} invited",
        actor_id=actor.user_id,
        actor_type=ActorType.USER,
        resource_type="user",
        resource_id=str(user.id),
        data={"email": email_norm},
    )
    return user, initial_password


async def update_user(
    db: AsyncSession,
    *,
    actor: AuthContext,
    user_id: UUID,
    full_name: str | None = None,
    role_id: UUID | None = None,
    is_active: bool | None = None,
    request: Request | None = None,
) -> User:
    """Apply partial updates guarded against self-deactivation and last-superadmin lockout."""
    user = await get_user(db, user_id)

    deactivating = bool(is_active is False and user.is_active)
    if deactivating:
        if user.id == actor.user_id:
            raise BadRequest("You cannot deactivate your own account", code="SELF_DEACTIVATION")
        await _assert_not_last_active_superadmin(db, user)

    changing_role = role_id is not None and role_id != user.role_id
    new_role: Role | None = None
    if changing_role:
        await _assert_not_last_active_superadmin(db, user)
        new_role = await db.get(Role, role_id)
        if new_role is None:
            raise NotFound("Role not found", code="ROLE_NOT_FOUND")

    changes: dict[str, Any] = {}
    if changing_role and new_role is not None:
        changes["role"] = {"from": user.role.name if user.role else None, "to": new_role.name}
        user.role_id = new_role.id
        user.role = new_role  # keep the selectin-loaded relationship consistent
    if full_name is not None and full_name != user.full_name:
        changes["full_name"] = True
        user.full_name = full_name.strip()[:160]
    if deactivating:
        changes["is_active"] = {"from": True, "to": False}

    if not changes:
        return user

    if deactivating:
        await _apply_deactivation(db, user)
    else:
        await db.flush()

    if changing_role:
        await event_bus.publish(
            db,
            type="PERMISSION_CHANGED",
            message=f"Role changed for {user.email}",
            level=EventLevel.WARNING,
            actor_id=actor.user_id,
            actor_type=ActorType.USER,
            resource_type="user",
            resource_id=str(user.id),
            data={"changes": changes},
        )
    await audit_service.record(
        db,
        actor,
        action="user.update",
        resource_type="user",
        resource_id=user.id,
        metadata={"changes": changes},
        request=request,
    )
    return user


async def deactivate_user(
    db: AsyncSession,
    *,
    actor: AuthContext,
    user_id: UUID,
    request: Request | None = None,
) -> User:
    """Deactivate a user: revoke sessions + API keys. Never a hard delete."""
    user = await get_user(db, user_id)
    if user.id == actor.user_id:
        raise BadRequest("You cannot deactivate your own account", code="SELF_DEACTIVATION")
    await _assert_not_last_active_superadmin(db, user)
    if not user.is_active:
        return user

    await _apply_deactivation(db, user)
    await audit_service.record(
        db,
        actor,
        action="user.deactivate",
        resource_type="user",
        resource_id=user.id,
        metadata={"at": datetime.now(UTC).isoformat()},
        request=request,
    )
    await event_bus.publish(
        db,
        type="USER_DEACTIVATED",
        message=f"User {user.email} deactivated",
        level=EventLevel.WARNING,
        actor_id=actor.user_id,
        actor_type=ActorType.USER,
        resource_type="user",
        resource_id=str(user.id),
    )
    return user


async def _apply_deactivation(db: AsyncSession, user: User) -> None:
    """Flip status and revoke every live credential belonging to the user."""
    user.is_active = False
    user.status = UserStatus.DISABLED
    await revoke_all_user_sessions(db, user.id, reason="user_deactivated")
    await api_key_service.revoke_all_for_user(db, user_id=user.id)


async def _assert_not_last_active_superadmin(db: AsyncSession, target: User) -> None:
    """Conflict when *target* is the only active superadmin left."""
    if not target.is_superadmin or not target.is_active:
        return
    active_superadmins = int(
        (
            await db.execute(
                select(func.count())
                .select_from(User)
                .where(User.is_superadmin.is_(True), User.is_active.is_(True))
            )
        ).scalar_one()
    )
    if active_superadmins <= 1:
        raise Conflict(
            "Cannot modify the last active superadmin account",
            code="LAST_SUPERADMIN_PROTECTED",
        )


# --- Sessions ------------------------------------------------------------------


async def list_sessions(
    db: AsyncSession, *, user_id: UUID, params: PageParams
) -> tuple[list[DbSession], int]:
    """Active sessions for a user (not revoked, not expired), newest activity first."""
    stmt = select(DbSession).where(
        DbSession.user_id == user_id,
        DbSession.revoked_at.is_(None),
        DbSession.expires_at > datetime.now(UTC),
    )
    stmt = stmt.order_by(DbSession.last_seen_at.desc().nulls_last(), DbSession.created_at.desc())
    return await paginate(db, stmt, params)


async def revoke_session(db: AsyncSession, session_id: UUID, *, reason: str) -> DbSession | None:
    """Revoke a session and all of its refresh tokens. Returns None if missing."""
    now = datetime.now(UTC)
    session = await db.get(DbSession, session_id)
    if session is None:
        return None
    if session.revoked_at is None:
        session.revoked_at = now
        session.revoked_reason = reason[:120]
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    return session


async def revoke_all_user_sessions(
    db: AsyncSession, user_id: UUID, *, reason: str, exclude_session_id: UUID | None = None
) -> int:
    """Revoke every active session (and their tokens) of a user; returns the count."""
    now = datetime.now(UTC)
    rows = (
        (
            await db.execute(
                select(DbSession).where(
                    DbSession.user_id == user_id, DbSession.revoked_at.is_(None)
                )
            )
        )
        .scalars()
        .all()
    )
    target_ids: list[UUID] = []
    for sess in rows:
        if exclude_session_id is not None and sess.id == exclude_session_id:
            continue
        sess.revoked_at = now
        sess.revoked_reason = reason[:120]
        target_ids.append(sess.id)
    if target_ids:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id.in_(target_ids), RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
    return len(target_ids)


async def revoke_session_as(
    db: AsyncSession, *, ctx: AuthContext, session_id: UUID, request: Request | None = None
) -> None:
    """Revoke with object-level authorization: own always; another user's needs user.manage."""
    session = await db.get(DbSession, session_id)
    if session is None:
        raise NotFound("Session not found", code="SESSION_NOT_FOUND")
    is_owner = session.user_id == ctx.user_id
    if not is_owner and not ctx.has_permission("user.manage"):
        raise Forbidden("You may only revoke your own sessions", code="PERMISSION_DENIED")
    await revoke_session(db, session_id, reason="revoked_by_user")
    await audit_service.record(
        db,
        ctx,
        action="session.revoke",
        resource_type="session",
        resource_id=session_id,
        metadata={"owner_id": str(session.user_id), "own_session": is_owner},
        request=request,
    )
