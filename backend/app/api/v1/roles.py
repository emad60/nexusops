"""Role management and permission-registry routes (role.read / role.manage)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import CurrentUser, DbSessionDep, require_permission
from app.core.pagination import Page, PageParams, page_params
from app.schemas.role import PermissionOut, RoleCreateRequest, RoleOut, RoleUpdateRequest
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])

_PageParams = Annotated[PageParams, Depends(page_params)]


@router.get(
    "", response_model=Page[RoleOut], dependencies=[Depends(require_permission("role.read"))]
)
async def list_roles(db: DbSessionDep, params: _PageParams) -> Page[RoleOut]:
    """All roles with their permission codenames expanded."""
    rows = await role_service.list_roles(db)
    total = len(rows)
    window = rows[params.offset : params.offset + params.limit]
    return Page(
        items=[RoleOut.from_role(r) for r in window],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get(
    "/permissions",
    response_model=list[PermissionOut],
    dependencies=[Depends(require_permission("role.read"))],
)
async def list_permissions() -> list[PermissionOut]:
    """The static permission registry grouped for UI rendering."""
    return [PermissionOut(**entry) for entry in role_service.permission_registry()]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RoleOut,
    dependencies=[Depends(require_permission("role.manage"))],
)
async def create_role(
    body: RoleCreateRequest, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> RoleOut:
    """Create a custom role from registry codenames."""
    role = await role_service.create_role(
        db,
        actor=ctx,
        name=body.name,
        description=body.description,
        permissions=body.permissions,
        request=request,
    )
    return RoleOut.from_role(role)


@router.patch(
    "/{role_id}", response_model=RoleOut, dependencies=[Depends(require_permission("role.manage"))]
)
async def update_role(
    role_id: UUID, body: RoleUpdateRequest, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> RoleOut:
    """Update a custom role's name, description or permission set."""
    role = await role_service.update_role(
        db,
        actor=ctx,
        role_id=role_id,
        name=body.name,
        description=body.description,
        permissions=body.permissions,
        request=request,
    )
    return RoleOut.from_role(role)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("role.manage"))],
)
async def delete_role(role_id: UUID, ctx: CurrentUser, db: DbSessionDep, request: Request) -> None:
    """Delete an unassigned custom role."""
    await role_service.delete_role(db, actor=ctx, role_id=role_id, request=request)
