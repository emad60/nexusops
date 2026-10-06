"""User account management: listing, invites, updates, deactivation and guards.

Also hosts the account-credential plumbing shared across domains: the password
policy, session listing and session/token revocation (a session is a
credential of the user, so its lifecycle belongs here). ``auth_service``
imports from this module — never the reverse.

Object-level guards enforced here (never trusting router checks alone):
  * a caller cannot deactivate their own account;
  * the last active member of an organization cannot be suspended;
  * revoking another user's session requires ``user.manage``.

Tenancy: ``users`` is an **instance-level identity** — a person can be a member
of several organizations — so the tenancy boundary of every user-facing
operation is the ``memberships`` row, not the user. Every read and write below
therefore takes the active ``org_id`` and joins it: without that join the
directory is an instance-wide dump of names and emails, and a role change or
removal silently reconfigures a user's access in *another* tenant. Role and
membership status in the directory are the membership's, never the account's.
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
from app.models import Membership, RefreshToken, Role, User
from app.models import Session as DbSession
from app.models.enums import ActorType, EventLevel, MembershipStatus, UserStatus
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


def _membership_join(org_id: UUID):
    """Inner join restricting a ``users`` query to one organization's members.

    Inner (not outer) on purpose: a user with no membership in the active
    organization is not addressable through the directory at all, so the join is
    both the filter and the authorization boundary. It is also what makes
    :func:`get_member` return *not found* — rather than *forbidden* — for a user
    the caller knows the id of but shares no tenant with, which keeps the
    endpoint from confirming the existence of foreign accounts.
    """
    return select(User, Membership).join(
        Membership, (Membership.user_id == User.id) & (Membership.org_id == org_id)
    )


async def list_users(
    db: AsyncSession,
    *,
    org_id: UUID,
    params: PageParams,
    q: str | None = None,
    is_active: bool | None = None,
    role_id: UUID | None = None,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[tuple[User, Membership]], int]:
    """Paginated directory of *this organization's* members, newest first.

    ``is_active``/``role_id`` filter the **membership** (suspended or active in
    this org; the role held in this org), not the account: the same user can be
    suspended in one tenant and active in another, and the two filters must
    agree with the representation they were applied to.

    The rows are ``(User, Membership)`` pairs rather than bare users so the
    caller serialises the membership's role, and pagination is spelled out here
    because :func:`~app.core.pagination.paginate` returns a single entity per
    row and would drop the membership.
    """
    stmt = _membership_join(org_id)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    if is_active is not None:
        stmt = stmt.where(
            Membership.status
            == (MembershipStatus.ACTIVE if is_active else MembershipStatus.SUSPENDED)
        )
    if role_id is not None:
        stmt = stmt.where(Membership.role_id == role_id)

    total = int(
        (
            await db.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))
        ).scalar_one()
    )
    sort_column: Any = {"created_at": User.created_at, "email": User.email}[sort]
    stmt = stmt.order_by(sort_column.desc() if order == "desc" else sort_column.asc())
    rows = (await db.execute(stmt.limit(params.limit).offset(params.offset))).all()
    return [(user, membership) for user, membership in rows], total


async def get_member(db: AsyncSession, *, user_id: UUID, org_id: UUID) -> tuple[User, Membership]:
    """Fetch a member of *org_id* or raise NotFound.

    A user outside the active organization is indistinguishable from a
    non-existent one: the joiner returns nothing for both, so a caller cannot
    probe for accounts in other tenants by id.
    """
    row = (await db.execute(_membership_join(org_id).where(User.id == user_id))).one_or_none()
    if row is None:
        raise NotFound("User not found", code="USER_NOT_FOUND")
    return row[0], row[1]


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

    # An invited account is invited *into the organization the inviter is acting
    # in*. Without the membership the account could authenticate but act nowhere:
    # the login response would list no organizations and every org-scoped call
    # would be refused. The role belongs to the membership, so the same person
    # can hold a different role in another tenant.
    if actor.org_id is not None:
        db.add(
            Membership(
                org_id=actor.org_id,
                user_id=user.id,
                role_id=role.id,
                status=MembershipStatus.ACTIVE,
                created_by_id=actor.user_id,
                created_at=now,
                updated_at=now,
            )
        )
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
    org_id: UUID,
    user_id: UUID,
    full_name: str | None = None,
    role_id: UUID | None = None,
    is_active: bool | None = None,
    request: Request | None = None,
) -> tuple[User, Membership]:
    """Update a member **of the active organization**, guarded against self-suspension.

    Everything authority-bearing is written to the membership, not the account:

    * ``role_id`` changes the role the user holds *here*. Writing it to
      ``User.role_id`` (as the single-tenant version did) would silently
      re-grant access in every other organization the person belongs to — one
      tenant editing another tenant's privileges.
    * ``is_active=False`` suspends this membership. It deliberately does **not**
      disable the account or revoke its sessions and API keys: those are
      instance-wide credentials, and a tenant administrator revoking them would
      be a cross-tenant denial of service. Account deactivation is an
      operator action, not a member-management one.
    * ``full_name`` stays on the account — a display name is a property of the
      person, identical wherever they appear.
    """
    user, membership = await get_member(db, user_id=user_id, org_id=org_id)

    suspending = bool(is_active is False and membership.status == MembershipStatus.ACTIVE)
    if suspending:
        if user.id == actor.user_id:
            raise BadRequest("You cannot suspend your own membership", code="SELF_DEACTIVATION")
        await _assert_not_last_active_member(db, org_id=org_id, membership=membership)

    changing_role = role_id is not None and role_id != membership.role_id
    new_role: Role | None = None
    if changing_role:
        new_role = await db.get(Role, role_id)
        if new_role is None:
            raise NotFound("Role not found", code="ROLE_NOT_FOUND")

    changes: dict[str, Any] = {}
    if changing_role and new_role is not None:
        changes["role"] = {
            "from": membership.role.name if membership.role else None,
            "to": new_role.name,
        }
        membership.role_id = new_role.id
        membership.role = new_role  # keep the selectin-loaded relationship consistent
    if full_name is not None and full_name != user.full_name:
        changes["full_name"] = True
        user.full_name = full_name.strip()[:160]
    if suspending:
        changes["membership_status"] = {
            "from": MembershipStatus.ACTIVE.value,
            "to": MembershipStatus.SUSPENDED.value,
        }
        membership.status = MembershipStatus.SUSPENDED
    elif is_active is True and membership.status == MembershipStatus.SUSPENDED:
        changes["membership_status"] = {
            "from": MembershipStatus.SUSPENDED.value,
            "to": MembershipStatus.ACTIVE.value,
        }
        membership.status = MembershipStatus.ACTIVE

    if not changes:
        return user, membership

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
    return user, membership


async def deactivate_user(
    db: AsyncSession,
    *,
    actor: AuthContext,
    org_id: UUID,
    user_id: UUID,
    request: Request | None = None,
) -> tuple[User, Membership]:
    """Remove a member from the active organization (soft: membership suspended).

    Scoped to the membership for the same reason as :func:`update_user`: the
    account and its credentials are shared across tenants, so a tenant
    administrator may end someone's access *here* and nowhere else. The row is
    kept — a removal is part of the organization's history, and re-adding the
    person should not have to recreate their audit trail.
    """
    user, membership = await get_member(db, user_id=user_id, org_id=org_id)
    if user.id == actor.user_id:
        raise BadRequest("You cannot remove your own membership", code="SELF_DEACTIVATION")
    if membership.status != MembershipStatus.ACTIVE:
        return user, membership
    await _assert_not_last_active_member(db, org_id=org_id, membership=membership)

    membership.status = MembershipStatus.SUSPENDED
    await db.flush()
    await audit_service.record(
        db,
        actor,
        action="user.deactivate",
        resource_type="user",
        resource_id=user.id,
        metadata={
            "at": datetime.now(UTC).isoformat(),
            "scope": "membership",
            "org_id": str(org_id),
        },
        request=request,
    )
    await event_bus.publish(
        db,
        type="USER_DEACTIVATED",
        message=f"User {user.email} removed from the organization",
        level=EventLevel.WARNING,
        actor_id=actor.user_id,
        actor_type=ActorType.USER,
        resource_type="user",
        resource_id=str(user.id),
    )
    return user, membership


async def _assert_not_last_active_member(
    db: AsyncSession, *, org_id: UUID, membership: Membership
) -> None:
    """Conflict when *membership* is the last active member of its organization.

    The multi-tenant successor to the last-superadmin guard: an organization
    whose last member is removed becomes administratively unreachable — nobody
    left to invite anyone — so the final removal is refused rather than
    silently orphaning the tenant.
    """
    if membership.status != MembershipStatus.ACTIVE:
        return
    active = int(
        (
            await db.execute(
                select(func.count())
                .select_from(Membership)
                .where(
                    Membership.org_id == org_id,
                    Membership.status == MembershipStatus.ACTIVE,
                )
            )
        ).scalar_one()
    )
    if active <= 1:
        raise Conflict(
            "Cannot remove the last active member of the organization",
            code="LAST_MEMBER_PROTECTED",
        )


async def _apply_deactivation(db: AsyncSession, user: User) -> None:
    """Disable an account and revoke every live credential it owns.

    Instance-level only (a whole-account action) and therefore unreachable from
    the tenant-scoped member endpoints; kept for operator tooling and future
    account management, and used by tests to assert that tenant suspension does
    *not* reach it.
    """
    user.is_active = False
    user.status = UserStatus.DISABLED
    await revoke_all_user_sessions(db, user.id, reason="user_deactivated")
    await api_key_service.revoke_all_for_user(db, user_id=user.id)


async def _assert_not_last_active_superadmin(db: AsyncSession, target: User) -> None:
    """Conflict when *target* is the only active superadmin left.

    Instance-level guard, kept beside the account-level operations it protects
    (``_apply_deactivation`` and operator tooling). Tenant-scoped member changes
    use :func:`_assert_not_last_active_member` instead, because a membership
    change cannot lock the instance out.
    """
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
    db: AsyncSession, *, org_id: UUID, params: PageParams, user_id: UUID | None = None
) -> tuple[list[DbSession], int]:
    """Active sessions belonging to **members of the active organization**.

    Sessions are credentials of the *account*, so ``sessions`` carries no tenant
    column and cannot be filtered directly. The boundary is the owner: a session
    is visible here only if its user holds a membership in the active
    organization. Without that join, ``?all=true`` — which any ``user.manage``
    holder can ask for — becomes an instance-wide feed of IP addresses, device
    labels and user agents.

    *user_id* narrows to one member (the caller having verified they are one);
    ``None`` means every member.
    """
    stmt = select(DbSession).where(
        DbSession.user_id.in_(select(Membership.user_id).where(Membership.org_id == org_id)),
        DbSession.revoked_at.is_(None),
        DbSession.expires_at > datetime.now(UTC),
    )
    if user_id is not None:
        stmt = stmt.where(DbSession.user_id == user_id)
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
    """Revoke with object-level authorization: own always; another user's needs user.manage.

    Both conditions are tenant-bound. ``user.manage`` is a permission *inside the
    active organization*, so it authorizes revoking a session of a member of
    that organization and nothing else: the target's membership is looked up
    first, and a session belonging to someone outside the tenant is reported as
    not found (a foreign session id is indistinguishable from a bogus one).
    Revoking it would otherwise be a cross-tenant denial of service available to
    any organization administrator.
    """
    session = await db.get(DbSession, session_id)
    if session is None:
        raise NotFound("Session not found", code="SESSION_NOT_FOUND")
    is_owner = session.user_id == ctx.user_id
    if not is_owner and not ctx.has_permission("user.manage"):
        raise Forbidden("You may only revoke your own sessions", code="PERMISSION_DENIED")
    if not is_owner:
        await get_member(db, user_id=session.user_id, org_id=ctx.require_org_id())
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
