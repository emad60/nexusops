"""Authentication flows: registration, login with lockout, refresh rotation, logout.

Pure async callables taking the DB session first so they can be exercised
without HTTP. Routers only parse input, delegate here and shape responses.

Session/token revocation primitives live in :mod:`app.services.user_service`;
this module imports from it (never the reverse).
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.config import Settings, get_settings
from app.core.errors import Conflict, Forbidden, Unauthorized
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import RefreshToken, Role, User
from app.models import Session as DbSession
from app.models.enums import ActorType, AuditResult, EventLevel, UserStatus
from app.services import audit_service, event_bus, user_service
from app.services.user_service import revoke_all_user_sessions, revoke_session

REFRESH_COOKIE_NAME = "nxo_rt"
REFRESH_COOKIE_PATH = "/api/v1/auth"

_INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"


async def _audit(
    db: AsyncSession,
    ctx: AuthContext | None,
    action: str,
    *,
    res: str | None = None,
    rid: Any = None,
    result: AuditResult = AuditResult.SUCCESS,
    meta: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    """Thin audit_service.record wrapper keeping call sites readable."""
    await audit_service.record(
        db,
        ctx,
        action=action,
        resource_type=res,
        resource_id=rid,
        result=result,
        metadata=meta,
        request=request,
    )


async def _event(
    db: AsyncSession,
    type_: str,
    message: str,
    *,
    level: EventLevel = EventLevel.INFO,
    actor_id: UUID | None = None,
    actor_type: ActorType = ActorType.SYSTEM,
    res: str | None = None,
    rid: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Thin event_bus.publish wrapper keeping call sites readable."""
    await event_bus.publish(
        db,
        type=type_,
        message=message,
        level=level,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type=res,
        resource_id=rid,
        data=data,
    )


def validate_password_policy(password: str) -> None:
    """Enforce the password policy; raises BadRequest(code=PASSWORD_POLICY)."""
    user_service.validate_password_policy(password)


__all__ = [  # public surface consumed by routers/other services
    "REFRESH_COOKIE_NAME",
    "REFRESH_COOKIE_PATH",
    "IssuedTokens",
    "change_own_password",
    "count_users",
    "login",
    "logout",
    "refresh",
    "register",
    "validate_password_policy",
]


@dataclass(slots=True)
class IssuedTokens:
    """Everything a token endpoint needs to render its response."""

    user: User
    session: DbSession
    access_token: str
    expires_in: int
    refresh_token: str


async def count_users(db: AsyncSession) -> int:
    """Number of existing users; zero means the next registration bootstraps."""
    return int((await db.execute(select(func.count()).select_from(User))).scalar_one())


async def register(
    db: AsyncSession,
    *,
    actor: AuthContext | None,
    email: str,
    password: str,
    full_name: str = "",
    request: Request | None = None,
) -> User:
    """Create a user account.

    Bootstrap semantics: when no users exist yet the first account becomes a
    superadmin bound to the system ``Owner`` role and may be created
    anonymously. Afterwards registration is invite-only for callers holding
    ``user.manage``.
    """
    validate_password_policy(password)
    email_norm = email.strip().lower()

    # Serialize the bootstrap decision: the count-then-act check below is only
    # safe if concurrent registrations cannot interleave between the count and
    # the insert. A transaction-scoped advisory lock (released automatically at
    # commit/rollback by the request dependency) makes exactly one concurrent
    # anonymous registration eligible to mint the initial superadmin.
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtext('nexusops-bootstrap'))"))

    existing = (
        await db.execute(select(User.id).where(User.email == email_norm))
    ).scalar_one_or_none()
    if existing is not None:
        raise Conflict("Email already registered", code="EMAIL_TAKEN")

    bootstrap = await count_users(db) == 0
    if not bootstrap and (actor is None or not actor.has_permission("user.manage")):
        raise Forbidden(
            "Registration requires an invitation from an administrator",
            code="INVITATION_REQUIRED",
        )

    now = datetime.now(UTC)
    role: Role | None = None
    if bootstrap:
        role = (await db.execute(select(Role).where(Role.name == "Owner"))).scalar_one_or_none()
    user = User(
        email=email_norm,
        password_hash=hash_password(password),
        full_name=(full_name or "").strip()[:160],
        is_active=True,
        is_superadmin=bootstrap,
        status=UserStatus.ACTIVE,
        role_id=role.id if role else None,
        created_at=now,
        updated_at=now,
    )
    # The role relationship is selectin-loaded on queries but never on flush;
    # assign it here so response serialization needs no lazy IO.
    user.role = role
    db.add(user)
    await db.flush()

    await _event(
        db,
        "USER_CREATED",
        f"User {email_norm} registered",
        actor_id=actor.user_id if actor else user.id,
        actor_type=ActorType.USER if actor else ActorType.SYSTEM,
        res="user",
        rid=str(user.id),
        data={"email": email_norm, "bootstrap": bootstrap},
    )
    await _audit(
        db,
        actor,
        "user.register",
        res="user",
        rid=user.id,
        meta={"email": email_norm, "bootstrap": bootstrap},
        request=request,
    )
    return user


async def _record_login_failure(
    db: AsyncSession,
    ctx: AuthContext | None,
    email: str,
    request: Request | None,
    *,
    reason: str,
    extra_meta: dict[str, Any] | None = None,
) -> None:
    """Audit + event for a failed login attempt (never reveals which part failed).

    Commits before returning: callers raise ``Unauthorized`` right after, and
    the request-scoped session dependency rolls back on exceptions — without
    this commit the lockout counters and the audit row would be discarded.
    """
    await _audit(
        db,
        ctx,
        "auth.login",
        res="user",
        result=AuditResult.DENIED,
        meta={"email": email, "reason": reason, **(extra_meta or {})},
        request=request,
    )
    await _event(
        db,
        "LOGIN_FAILED",
        f"Failed login for {email}",
        level=EventLevel.WARNING,
        actor_id=ctx.user_id if ctx else None,
        actor_type=ActorType.USER if ctx else ActorType.SYSTEM,
        res="user",
        data={"email": email},
    )
    await db.commit()


async def login(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    ip: str = "",
    user_agent: str = "",
    request: Request | None = None,
) -> IssuedTokens:
    """Authenticate credentials, creating a session + refresh token on success."""
    settings = get_settings()
    now = datetime.now(UTC)
    email_norm = email.strip().lower()
    user = (await db.execute(select(User).where(User.email == email_norm))).scalar_one_or_none()

    if user is None or not user.is_active:
        await _record_login_failure(db, None, email_norm, request, reason="unknown_or_inactive")
        raise Unauthorized(_INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")

    ctx = AuthContext(user=user)
    if user.locked_until is not None and user.locked_until > now:
        minutes = max(1, math.ceil((user.locked_until - now).total_seconds() / 60))
        # Answer with the SAME generic envelope as unknown/bad-password
        # attempts: a distinct "account locked" response would let an
        # attacker enumerate registered emails by watching for the state
        # change. The lock detail (code, countdown) stays server-side in the
        # audit/event trail only.
        await _record_login_failure(
            db,
            ctx,
            email_norm,
            request,
            reason="account_locked",
            extra_meta={"code": "ACCOUNT_LOCKED", "locked_minutes": minutes},
        )
        raise Unauthorized(_INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")

    if not verify_password(user.password_hash, password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.login_max_attempts:
            user.locked_until = now + timedelta(seconds=settings.login_lockout_seconds)
            user.status = UserStatus.LOCKED
        await _record_login_failure(db, ctx, email_norm, request, reason="bad_password")
        raise Unauthorized(_INVALID_CREDENTIALS_MESSAGE, code="INVALID_CREDENTIALS")

    # Success: reset lockout state and open the session.
    user.failed_login_attempts = 0
    user.locked_until = None
    user.status = UserStatus.ACTIVE
    user.last_login_at = now

    session = DbSession(
        id=uuid.uuid4(),  # column defaults apply at flush; the refresh token and
        # the access-token claim both need this id now
        user_id=user.id,
        ip_address=(ip or "")[:64],
        user_agent=(user_agent or "")[:400],
        device_label="",
        expires_at=now + timedelta(days=settings.session_idle_timeout_days),
        last_seen_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    # Persist the session first: without a relationship edge between the two
    # mappers the unit of work has no dependency ordering (refresh_tokens sorts
    # before sessions), so the token row would violate its FK.
    await db.flush()
    raw_refresh, refresh_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            session_id=session.id,
            token_hash=refresh_hash,
            expires_at=now + timedelta(seconds=settings.refresh_token_ttl),
            created_at=now,
            updated_at=now,
        )
    )
    await db.flush()

    await _audit(
        db, ctx, "auth.login", res="user", rid=user.id, meta={"email": email_norm}, request=request
    )
    await _event(
        db,
        "USER_LOGIN",
        f"User {email_norm} logged in",
        actor_id=user.id,
        actor_type=ActorType.USER,
        res="session",
        rid=str(session.id),
        data={"ip": ip},
    )
    return _issue_access(user, session, raw_refresh)


def _issue_access(user: User, session: DbSession, raw_refresh: str) -> IssuedTokens:
    token, _ = create_access_token(user_id=user.id, session_id=session.id, email=user.email)
    return IssuedTokens(
        user=user,
        session=session,
        access_token=token,
        expires_in=get_settings().access_token_ttl,
        refresh_token=raw_refresh,
    )


async def _grace_successor(
    db: AsyncSession, row: RefreshToken, *, now: datetime, settings: Settings
) -> RefreshToken | None:
    """Return the successor token if this replay qualifies for the grace rescue.

    Qualification is deliberately tight — every condition must hold:

    * the token was consumed by a *rotation* (superseded_by_id set — a logout
      or admin revocation leaves no live successor to rescue into),
    * the consumption happened within ``refresh_grace_seconds``,
    * the one-shot ``grace_used`` flag is still clear (a second replay of the
      same token cannot keep rescuing itself, so a stolen token buys at most
      one audited rotation inside the window),
    * the successor is unused, unrevoked and unexpired (exactly one live
      branch exists to fold back into).
    """
    if settings.refresh_grace_seconds <= 0 or row.superseded_by_id is None:
        return None
    if row.grace_used:
        return None
    consumed_at = row.updated_at
    if consumed_at is None or (now - consumed_at) > timedelta(
        seconds=settings.refresh_grace_seconds
    ):
        return None
    successor = await db.get(RefreshToken, row.superseded_by_id)
    if (
        successor is None
        or successor.revoked_at is not None
        or successor.superseded_by_id is not None
        or successor.expires_at <= now
    ):
        return None
    return successor


async def refresh(
    db: AsyncSession, *, raw_token: str, request: Request | None = None
) -> IssuedTokens:
    """Rotate a refresh token, detecting reuse of already-consumed tokens as theft."""
    settings = get_settings()
    now = datetime.now(UTC)
    # FOR UPDATE serializes concurrent rotations of the same token: a second
    # request carrying the copied token blocks here until the first commit,
    # then observes superseded_by_id set and takes the theft (TOKEN_REUSE)
    # path instead of minting a parallel session. Without the lock two
    # concurrent uses could both read "still valid" and both rotate.
    row = (
        await db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(raw_token))
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        raise Unauthorized("Refresh token not recognised", code="REFRESH_INVALID")

    # Set only on the replay path (below); the normal rotation must not touch it.
    grace_successor: RefreshToken | None = None

    if row.revoked_at is not None or row.superseded_by_id is not None:
        # Token replay. One bounded exception: if THIS token was consumed by
        # the immediately preceding rotation, inside the grace window, and its
        # successor is still unused, the likely story is a lost response — a
        # browser navigation or dropped connection aborted the client's
        # in-flight refresh after the server committed the rotation, so the
        # rotated cookie never reached the jar. Rescue once (re-rotate from
        # this token, collapse the orphaned successor), loudly audited; a
        # second replay of the same token is theft again.
        grace_successor = await _grace_successor(db, row, now=now, settings=settings)
        if grace_successor is None:
            # Token replay → assume theft: kill every token and the session itself.
            await revoke_session(db, row.session_id, reason="token_reuse_detected")
            await _audit(
                db,
                None,
                "auth.token_reuse_detected",
                res="session",
                rid=row.session_id,
                result=AuditResult.DENIED,
                meta={"refresh_token_id": str(row.id)},
                request=request,
            )
            # The request dependency rolls back on exceptions; commit so the
            # revocation (and the audit trail) actually survive the raised 401.
            await db.commit()
            raise Unauthorized("Refresh token reuse detected; session revoked", code="TOKEN_REUSE")
        row.grace_used = True
        await _audit(
            db,
            None,
            "auth.token_grace_reuse",
            res="session",
            rid=row.session_id,
            meta={
                "refresh_token_id": str(row.id),
                "grace_seconds": settings.refresh_grace_seconds,
            },
            request=request,
        )

    if row.expires_at <= now:
        raise Unauthorized("Refresh token expired", code="REFRESH_EXPIRED")

    session = await db.get(DbSession, row.session_id, with_for_update=True)
    if session is None or session.revoked_at is not None:
        raise Unauthorized("Session is no longer active", code="SESSION_INVALID")
    if session.expires_at <= now:
        raise Unauthorized("Session expired", code="SESSION_EXPIRED")
    user = await db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise Unauthorized("Account is inactive", code="ACCOUNT_DISABLED")

    raw_new, new_hash = generate_refresh_token()
    new_row = RefreshToken(
        session_id=session.id,
        token_hash=new_hash,
        expires_at=now + timedelta(seconds=settings.refresh_token_ttl),
        created_at=now,
        updated_at=now,
    )
    db.add(new_row)
    await db.flush()  # need new_row.id for the supersession pointer
    row.superseded_by_id = new_row.id
    row.revoked_at = now
    if grace_successor is not None:
        # The rotation whose response was lost mid-flight minted this token and
        # nobody ever received it; fold it into the new chain so exactly one
        # live branch remains (presenting it later is ordinary reuse).
        grace_successor.superseded_by_id = new_row.id
        grace_successor.revoked_at = now
    session.last_seen_at = now

    await _audit(
        db,
        AuthContext(user=user),
        "auth.token_rotated",
        res="session",
        rid=session.id,
        meta={"rotated_from": str(row.id), "rotated_to": str(new_row.id)},
        request=request,
    )
    return _issue_access(user, session, raw_new)


# --- Logout & password change -------------------------------------------------------


async def logout(db: AsyncSession, *, ctx: AuthContext, request: Request | None = None) -> None:
    """Revoke the caller's current session (if any) and record the logout."""
    if ctx.session_id is not None:
        await revoke_session(db, ctx.session_id, reason="logout")
    await _audit(
        db,
        ctx,
        "auth.logout",
        res="session",
        rid=str(ctx.session_id) if ctx.session_id else None,
        request=request,
    )
    await _event(
        db,
        "USER_LOGOUT",
        f"User {ctx.email} logged out",
        actor_id=ctx.user_id,
        actor_type=ActorType.USER,
        res="user",
        rid=str(ctx.user_id),
    )


async def change_own_password(
    db: AsyncSession,
    *,
    ctx: AuthContext,
    current_password: str,
    new_password: str,
    request: Request | None = None,
) -> User:
    """Change the caller's password, revoking all of their other sessions."""
    user = ctx.user
    if not verify_password(user.password_hash, current_password):
        await _audit(
            db,
            ctx,
            "user.password.change",
            res="user",
            rid=user.id,
            result=AuditResult.DENIED,
            request=request,
        )
        raise Unauthorized("Current password is incorrect", code="INVALID_CREDENTIALS")

    validate_password_policy(new_password)
    user.password_hash = hash_password(new_password)
    revoked = await revoke_all_user_sessions(
        db, user.id, reason="password_changed", exclude_session_id=ctx.session_id
    )
    await _audit(
        db,
        ctx,
        "user.password.change",
        res="user",
        rid=user.id,
        meta={"revoked_other_sessions": revoked},
        request=request,
    )
    await _event(
        db,
        "USER_PASSWORD_CHANGED",
        f"Password changed for {user.email}",
        level=EventLevel.WARNING,
        actor_id=user.id,
        actor_type=ActorType.USER,
        res="user",
        rid=str(user.id),
    )
    return user
