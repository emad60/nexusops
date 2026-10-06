"""User management routes (user.read / user.manage), scoped to the active tenant.

These endpoints manage the **members of the organization the request is acting
in**. ``users`` is an instance-level identity table, so every route here resolves
the target through its membership first: a user who shares no organization with
the caller is not addressable, and a role change or removal written through
here only ever affects this tenant.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import CurrentUser, DbSessionDep, require_permission
from app.core.pagination import Page, PageParams, page_params
from app.schemas.user import (
    UserCreatedOut,
    UserCreateRequest,
    UserOut,
    UserUpdateRequest,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

_PageParams = Annotated[PageParams, Depends(page_params)]


@router.get(
    "", response_model=Page[UserOut], dependencies=[Depends(require_permission("user.read"))]
)
async def list_users(
    ctx: CurrentUser,
    db: DbSessionDep,
    params: _PageParams,
    q: str | None = Query(None, max_length=200, description="Match email or full name"),
    is_active: bool | None = Query(None, description="Membership status in this organization"),
    role_id: UUID | None = Query(None, description="Role held in this organization"),
    sort: Literal["created_at", "email"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> Page[UserOut]:
    """Paginated directory of this organization's members."""
    rows, total = await user_service.list_users(
        db,
        org_id=ctx.require_org_id(),
        params=params,
        q=q,
        is_active=is_active,
        role_id=role_id,
        sort=sort,
        order=order,
    )
    return Page(
        items=[UserOut.from_user(user, membership) for user, membership in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get(
    "/{user_id}", response_model=UserOut, dependencies=[Depends(require_permission("user.read"))]
)
async def get_user(user_id: UUID, ctx: CurrentUser, db: DbSessionDep) -> UserOut:
    """Fetch one member of this organization (404 for anyone outside it)."""
    user, membership = await user_service.get_member(
        db, user_id=user_id, org_id=ctx.require_org_id()
    )
    return UserOut.from_user(user, membership)


@router.post(
    "",
    status_code=201,
    response_model=UserCreatedOut,
    dependencies=[Depends(require_permission("user.manage"))],
)
async def create_user(
    body: UserCreateRequest, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> UserCreatedOut:
    """Invite a user into this organization; a generated password is shown once."""
    user, initial_password = await user_service.create_user(
        db,
        actor=ctx,
        email=str(body.email),
        password=body.password,
        full_name=body.full_name,
        role_id=body.role_id,
        request=request,
    )
    return UserCreatedOut(user=UserOut.from_user(user), initial_password=initial_password)


@router.patch(
    "/{user_id}", response_model=UserOut, dependencies=[Depends(require_permission("user.manage"))]
)
async def update_user(
    user_id: UUID, body: UserUpdateRequest, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> UserOut:
    """Update a member's name, role or membership status within this organization."""
    user, membership = await user_service.update_user(
        db,
        actor=ctx,
        org_id=ctx.require_org_id(),
        user_id=user_id,
        full_name=body.full_name,
        role_id=body.role_id,
        is_active=body.is_active,
        request=request,
    )
    return UserOut.from_user(user, membership)


@router.delete(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_permission("user.manage"))],
)
async def deactivate_user(
    user_id: UUID, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> UserOut:
    """Remove a user from this organization (their membership is suspended)."""
    user, membership = await user_service.deactivate_user(
        db, actor=ctx, org_id=ctx.require_org_id(), user_id=user_id, request=request
    )
    return UserOut.from_user(user, membership)
