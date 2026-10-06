"""Authentication routes: register, login, refresh rotation, logout, me, password."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    AuthContext,
    DbSessionDep,
    IdentityUser,
    active_memberships,
    resolve_auth,
)
from app.core.config import get_settings
from app.core.errors import Unauthorized
from app.core.rate_limit import auth_limiter, client_ip, register_limiter, token_refresh_limiter
from app.schemas.auth import (
    LoginRequest,
    MembershipOut,
    MeOut,
    PasswordChangeRequest,
    RefreshRequest,
    RegisterRequest,
    TokenOut,
    UserEnvelope,
)
from app.schemas.organization import OrganizationOut
from app.schemas.user import UserOut
from app.services import auth_service, role_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _transport_is_https(forwarded_proto: str | None, url_scheme: str) -> bool:
    """Whether this request's cookie will travel over https.

    The edge always overwrites ``X-Forwarded-Proto`` with its own ``$scheme``
    (nginx/default.conf.template), so the header is authoritative and not
    client-spoofable; without it (direct ASGI access) fall back to the request
    scheme. This must NOT be derived from ``ENVIRONMENT``: tying ``Secure`` to
    production mode made production-over-plain-http silently drop every auth
    cookie — browsers refuse Secure cookies over http — so login "succeeded"
    and every reload bounced back to /login.
    """
    scheme = (forwarded_proto or url_scheme).split(",")[0].strip().lower()
    return scheme == "https"


def _cookies_secure(request: Request) -> bool:
    return _transport_is_https(request.headers.get("x-forwarded-proto"), request.url.scheme)


def _set_refresh_cookie(request: Request, response: Response, raw_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=auth_service.REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="strict",
        secure=_cookies_secure(request),
        path=auth_service.REFRESH_COOKIE_PATH,
        max_age=settings.refresh_token_ttl,
    )


def _clear_refresh_cookie(request: Request, response: Response) -> None:
    response.delete_cookie(
        key=auth_service.REFRESH_COOKIE_NAME,
        path=auth_service.REFRESH_COOKIE_PATH,
        httponly=True,
        samesite="strict",
        secure=_cookies_secure(request),
    )


def _request_ip(request: Request) -> str:
    """client_ip for anonymous endpoints (no auth dependency has run yet)."""
    return client_ip(request)


def _user_agent(request: Request) -> str:
    return (request.headers.get("user-agent") or "")[:400]


async def _optional_actor(request: Request, db: AsyncSession) -> AuthContext | None:
    """Resolve credentials if presented; None for truly anonymous calls."""
    if not request.headers.get("authorization") and not request.headers.get("x-api-key"):
        return None
    return await resolve_auth(request, db)


@router.post(
    "/register",
    status_code=201,
    response_model=UserEnvelope,
    dependencies=[Depends(register_limiter())],
)
async def register(body: RegisterRequest, request: Request, db: DbSessionDep) -> UserEnvelope:
    """Bootstrap the first owner account or accept an authenticated invitation."""
    actor = await _optional_actor(request, db)
    user = await auth_service.register(
        db,
        actor=actor,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        request=request,
    )
    return UserEnvelope(user=UserOut.from_user(user))


@router.post("/login", response_model=TokenOut, dependencies=[Depends(auth_limiter())])
async def login(
    body: LoginRequest, request: Request, response: Response, db: DbSessionDep
) -> TokenOut:
    """Authenticate and issue an access token plus the refresh cookie."""
    issued = await auth_service.login(
        db,
        email=body.email,
        password=body.password,
        ip=_request_ip(request),
        user_agent=_user_agent(request),
        request=request,
    )
    _set_refresh_cookie(request, response, issued.refresh_token)
    return TokenOut(
        access_token=issued.access_token,
        expires_in=issued.expires_in,
        user=UserOut.from_user(issued.user),
        organizations=[MembershipOut.from_membership(m) for m in issued.memberships],
        active_organization_id=issued.active_organization_id,
    )


@router.post("/refresh", response_model=TokenOut, dependencies=[Depends(token_refresh_limiter())])
async def refresh(
    request: Request, response: Response, db: DbSessionDep, body: RefreshRequest | None = None
) -> TokenOut:
    """Rotate the refresh token (cookie preferred over body) and re-issue access."""
    raw_token = request.cookies.get(auth_service.REFRESH_COOKIE_NAME) or (
        body.refresh_token if body is not None else None
    )
    if not raw_token:
        raise Unauthorized("Missing refresh token", code="REFRESH_MISSING")
    issued = await auth_service.refresh(db, raw_token=raw_token, request=request)
    _set_refresh_cookie(request, response, issued.refresh_token)
    return TokenOut(
        access_token=issued.access_token,
        expires_in=issued.expires_in,
        user=UserOut.from_user(issued.user),
        organizations=[MembershipOut.from_membership(m) for m in issued.memberships],
        active_organization_id=issued.active_organization_id,
    )


@router.post("/logout", status_code=204)
async def logout(ctx: IdentityUser, db: DbSessionDep, response: Response, request: Request) -> None:
    """Revoke the current session and clear the refresh cookie.

    Identity-only on purpose: an account must always be able to end its own
    session, even if it currently belongs to no organization.
    """
    await auth_service.logout(db, ctx=ctx, request=request)
    _clear_refresh_cookie(request, response)


@router.get("/me", response_model=MeOut)
async def me(ctx: IdentityUser, db: DbSessionDep) -> MeOut:
    """The caller's identity, organizations, and authority in the active one.

    Deliberately usable without ``X-Org-Id``: this is how a client learns which
    organizations it may act in. When the header *is* sent and valid, the
    response also reports the resolved organization and the permissions it
    grants.
    """
    memberships = await active_memberships(db, ctx.user_id)
    active_id = ctx.org_id
    if active_id is None and len(memberships) == 1:
        active_id = memberships[0].org_id

    role_name = ctx.role_name
    permissions: list[str] = []
    if ctx.membership is not None:
        permissions = role_service.permissions_for_role(ctx.membership.role)
    elif len(memberships) == 1 and memberships[0].role is not None:
        role_name = memberships[0].role.name
        permissions = role_service.permissions_for_role(memberships[0].role)

    return MeOut(
        user=UserOut.from_user(ctx.user),
        role=role_name,
        permissions=permissions,
        superadmin=ctx.user.is_superadmin,
        organizations=[MembershipOut.from_membership(m) for m in memberships],
        active_organization_id=active_id,
        active_organization=OrganizationOut.from_org(ctx.org) if ctx.org else None,
    )


@router.post("/password", response_model=UserEnvelope)
async def change_password(
    body: PasswordChangeRequest, ctx: IdentityUser, db: DbSessionDep, request: Request
) -> UserEnvelope:
    """Change own password; other sessions are revoked, current one survives."""
    user = await auth_service.change_own_password(
        db,
        ctx=ctx,
        current_password=body.current_password,
        new_password=body.new_password,
        request=request,
    )
    return UserEnvelope(user=UserOut.from_user(user))
