"""User management routes (user.read / user.manage)."""

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
    db: DbSessionDep,
    params: _PageParams,
    q: str | None = Query(None, max_length=200, description="Match email or full name"),
    is_active: bool | None = Query(None),
    role_id: UUID | None = Query(None),
    sort: Literal["created_at", "email"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> Page[UserOut]:
    """Paginated user directory."""
    rows, total = await user_service.list_users(
        db,
        params=params,
        q=q,
        is_active=is_active,
        role_id=role_id,
        sort=sort,
        order=order,
    )
    return Page(
        items=[UserOut.from_user(u) for u in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get(
    "/{user_id}", response_model=UserOut, dependencies=[Depends(require_permission("user.read"))]
)
async def get_user(user_id: UUID, db: DbSessionDep) -> UserOut:
    """Fetch a single user."""
    return UserOut.from_user(await user_service.get_user(db, user_id))


@router.post(
    "",
    status_code=201,
    response_model=UserCreatedOut,
    dependencies=[Depends(require_permission("user.manage"))],
)
async def create_user(
    body: UserCreateRequest, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> UserCreatedOut:
    """Invite a user. When no password is supplied one is generated and shown once."""
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
    """Update name / role / activation with self-service and last-superadmin guards."""
    user = await user_service.update_user(
        db,
        actor=ctx,
        user_id=user_id,
        full_name=body.full_name,
        role_id=body.role_id,
        is_active=body.is_active,
        request=request,
    )
    return UserOut.from_user(user)


@router.delete(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_permission("user.manage"))],
)
async def deactivate_user(
    user_id: UUID, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> UserOut:
    """Deactivate a user (soft delete): revokes their sessions and API keys."""
    user = await user_service.deactivate_user(db, actor=ctx, user_id=user_id, request=request)
    return UserOut.from_user(user)
