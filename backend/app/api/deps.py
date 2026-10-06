"""FastAPI dependencies: database session, authenticated tenant context, RBAC gate.

Authentication accepts either:

  * ``Authorization: Bearer <jwt>`` (SPA in-memory access token), or
  * ``X-API-Key: nxo_...`` (machine clients).

Authentication answers *who* is calling. It deliberately does not answer *for
which organization* — that is a second, independent question:

  * human callers select it per request with ``X-Org-Id``, validated against
    their **active** memberships. A JWT identifies a user and is never treated as
    a tenant boundary; the client's chosen organization id is never trusted on
    its own.
  * machine credentials are bound to one organization at creation
    (``api_keys.org_id``), so for API keys the header is ignored entirely — the
    key *is* the boundary and cannot be widened by a header.

The resolved organization is installed as the tenancy scope for the duration of
the request (see :mod:`app.core.tenancy`), which is what makes the session guard
and PostgreSQL RLS apply to everything the endpoint does.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import BadRequest, Forbidden, Unauthorized
from app.core.permissions import WILDCARD, scope_matches
from app.core.rate_limit import client_ip
from app.core.security import decode_access_token, hash_token
from app.core.tenancy import TenancyScopeError, org_scope
from app.models import ApiKey, Membership, Organization, User
from app.models import Session as DbSession
from app.models.enums import MembershipStatus, OrganizationStatus

DbSessionDep = Annotated[AsyncSession, Depends(get_session)]

#: Header naming the organization a human caller is acting in.
ORGANIZATION_HEADER = "X-Org-Id"


@dataclass(slots=True)
class AuthContext:
    """Resolved identity plus the organization this request acts in.

    ``org``/``membership`` are populated for every org-scoped request. They are
    ``None`` only on the deliberate exemptions (login, refresh, registration,
    ``/meta``, organization management) which must work before — or across — an
    organization is known.
    """

    user: User
    org: Organization | None = None
    membership: Membership | None = None
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

    @property
    def org_id(self) -> uuid.UUID | None:
        return self.org.id if self.org is not None else None

    def require_org_id(self) -> uuid.UUID:
        """The active organization, or raise if this request has none."""
        if self.org is None:
            raise TenancyScopeError(
                "this operation needs an active organization; use CurrentUser, not IdentityUser"
            )
        return self.org.id

    @property
    def role_name(self) -> str | None:
        role = self.membership.role if self.membership is not None else None
        return role.name if role is not None else None

    def has_permission(self, codename: str) -> bool:
        # API keys are scoped intersections: both the key scope AND the
        # owning user's membership role must allow the action. The scope check
        # comes FIRST — even a superadmin-owned key can never exceed its grant,
        # so a leaked least-privilege machine key stays least-privilege.
        if self.api_key is not None and not scope_matches(
            list(self.api_key.scopes or []), codename
        ):
            return False
        if self.user.is_superadmin:
            return True
        if self.membership is None or self.membership.status != MembershipStatus.ACTIVE:
            # No membership in the active organization means no authority in it,
            # regardless of what the user's default role would grant elsewhere.
            return False
        return (
            WILDCARD in self._permission_set
            or codename in self._permission_set
            or any(p.endswith("*") and codename.startswith(p[:-1]) for p in self._permission_set)
        )


def _load_permissions(ctx: AuthContext) -> None:
    """Effective permissions come from the **membership's** role, not the user's.

    A user is an Admin in one organization and a Viewer in another; the single
    ``User.role_id`` cannot express that, so it only survives as the default
    applied when a membership is created. ``Membership.role`` and
    ``Role.permissions`` are both ``lazy="selectin"``, so after any query-loaded
    membership these attributes are already in memory — no IO needed.
    """
    if ctx.user.is_superadmin:
        ctx._permission_set = {WILDCARD}
        return
    role = ctx.membership.role if ctx.membership is not None else None
    ctx._permission_set = {p.codename for p in role.permissions} if role is not None else set()


# --- Identity resolution -------------------------------------------------------


async def _user_from_api_key(db: AsyncSession, row: ApiKey) -> User:
    user = (await db.execute(select(User).where(User.id == row.user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise Unauthorized("API key owner is inactive")
    return user


async def _resolve_identity(request: Request, db: AsyncSession) -> AuthContext:
    """Resolve the caller's identity only (no organization)."""
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
        user = await _user_from_api_key(db, row)
        ctx = AuthContext(user=user, actor_type="API_KEY", api_key=row)
        # Throttle last_used_at writes to at most once per minute per key.
        if row.last_used_at is None or (now - row.last_used_at).total_seconds() > 60:
            row.last_used_at = now
            await db.commit()
        return ctx

    if not token:
        raise Unauthorized()

    payload = decode_access_token(token)  # raises Unauthorized on any problem
    try:
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
    except (KeyError, ValueError) as exc:
        raise Unauthorized("Malformed token claims") from exc

    token_user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if token_user is None or not token_user.is_active:
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
    return AuthContext(user=token_user, actor_type="USER", session_id=session_id)


# --- Organization resolution ---------------------------------------------------


def _org_id_from_header(request: Request) -> uuid.UUID | None:
    """Parse ``X-Org-Id``; a malformed value is a client error, never a guess."""
    raw = (request.headers.get(ORGANIZATION_HEADER) or "").strip()
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise BadRequest(
            f"{ORGANIZATION_HEADER} must be a UUID",
            code="INVALID_ORG_HEADER",
        ) from exc


async def active_memberships(db: AsyncSession, user_id: uuid.UUID) -> list[Membership]:
    """The user's memberships in non-suspended organizations, oldest first.

    Reads only the pre-org credential/identity tables (memberships,
    organizations), which is why this works before a scope is entered.
    """
    rows = (
        (
            await db.execute(
                select(Membership)
                .join(Organization, Organization.id == Membership.org_id)
                .where(
                    Membership.user_id == user_id,
                    Membership.status == MembershipStatus.ACTIVE,
                    Organization.status == OrganizationStatus.ACTIVE,
                )
                .order_by(Membership.created_at, Membership.id)
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


async def membership_for_org(
    db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID
) -> Membership | None:
    """The user's active membership in *org_id*, if any.

    This single indexed read is the whole authorization decision for tenant
    selection: knowing an organization id grants nothing without a membership
    row to match it.
    """
    return (
        await db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.org_id == org_id,
                Membership.status == MembershipStatus.ACTIVE,
            )
        )
    ).scalar_one_or_none()


async def _load_organization(db: AsyncSession, org_id: uuid.UUID) -> Organization:
    org = await db.get(Organization, org_id)
    if org is None or org.status != OrganizationStatus.ACTIVE:
        # A withheld organization is indistinguishable from a non-existent one
        # from the caller's side.
        raise Forbidden("Organization is not available", code="ORGANIZATION_FORBIDDEN")
    return org


async def _attach_organization(
    ctx: AuthContext, db: AsyncSession, request: Request, *, required: bool
) -> None:
    """Resolve and attach the active organization for this request."""
    header_org = _org_id_from_header(request)

    if ctx.api_key is not None:
        # Machine credential: its own organization is the boundary. The header
        # is ignored rather than rejected, so a client cannot accidentally
        # reinterpret a key as belonging to a different tenant.
        org_id: uuid.UUID | None = ctx.api_key.org_id
    else:
        org_id = header_org

    if org_id is None:
        if not required:
            return
        memberships = await active_memberships(db, ctx.user_id)
        if not memberships:
            raise Forbidden(
                "Your account is not a member of any organization",
                code="ORGANIZATION_REQUIRED",
            )
        raise Forbidden(
            f"{ORGANIZATION_HEADER} header is required: this account belongs to "
            f"{len(memberships)} organization(s), and the platform never guesses "
            f"which one a request is for",
            code="ORGANIZATION_HEADER_REQUIRED",
        )

    membership = await membership_for_org(db, ctx.user_id, org_id)
    if membership is None:
        raise Forbidden(
            "You are not a member of that organization",
            code="ORGANIZATION_FORBIDDEN",
        )
    ctx.org = await _load_organization(db, org_id)
    ctx.membership = membership
    _load_permissions(ctx)


async def resolve_auth(
    request: Request, db: AsyncSession, *, require_org: bool = True
) -> AuthContext:
    """Resolve credentials **and** the active organization.

    ``require_org=False`` is reserved for the endpoints that must work before an
    organization is known: login, refresh, registration, ``/meta``, the
    organization list/creation routes and the agent ingest path. Those
    endpoints still get a full context when the header is present and valid.
    """
    ctx = await _resolve_identity(request, db)
    await _attach_organization(ctx, db, request, required=require_org)
    return ctx


# --- Dependencies ---------------------------------------------------------------


async def get_current_user(request: Request, db: DbSessionDep) -> AsyncIterator[AuthContext]:
    """Org-scoped authentication: identity + validated active organization.

    Also installs the tenancy scope for the rest of the request. The commit
    before entering the scope matters: identity resolution reads run outside any
    organization (they must — that is how the caller is found at all), and
    PostgreSQL's ``SET LOCAL``-style GUC is re-issued per transaction, so the
    scope change needs a transaction boundary to take effect.
    """
    request.state.client_ip = client_ip(request)
    ctx = await resolve_auth(request, db, require_org=True)
    await db.commit()
    with org_scope(ctx.require_org_id()):
        try:
            yield ctx
        finally:
            # Flush while the scope is still active. The session dependency
            # commits *after* this generator is closed, and a pending
            # organization-owned row would be written by that commit with no
            # scope at all — un-stamped and rejected by RLS. Flushing here keeps
            # every write inside the tenant it was made for.
            await db.flush()


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]


async def get_identity(request: Request, db: DbSessionDep) -> AuthContext:
    """Identity-only authentication for the pre-org exemptions (no scope)."""
    request.state.client_ip = client_ip(request)
    return await resolve_auth(request, db, require_org=False)


IdentityUser = Annotated[AuthContext, Depends(get_identity)]


async def get_optional_user(request: Request, db: DbSessionDep) -> AuthContext | None:
    """Like :func:`get_identity` but returns ``None`` for anonymous callers."""
    try:
        request.state.client_ip = client_ip(request)
        return await resolve_auth(request, db, require_org=False)
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
