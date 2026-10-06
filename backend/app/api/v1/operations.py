"""Node operations API: dispatch, inspect and cancel whitelisted actions.

Authorisation is **per type**, because the architecture reuses the permission of
the thing being acted on rather than adding a generic ``node.execute`` grant: a
container lifecycle op needs ``container.lifecycle``, a removal needs
``container.remove``, a log tail needs ``container.logs``. Reading operations is
a node-scoped read (``node.read``), since an operation is an artifact of the node
it targets.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.errors import Forbidden
from app.core.pagination import Page, PageParams, page_params
from app.models.enums import OperationStatus
from app.schemas.operation import OPERATION_SPECS, OperationCreate, OperationOut
from app.services import audit_service, operation_service

router = APIRouter(prefix="/operations", tags=["operations"])

DbDep = Annotated[AsyncSession, Depends(get_session)]
ReadCtx = Annotated[AuthContext, Depends(require_permission("node.read"))]


def _require_type_permission(ctx: AuthContext, op_type: object) -> str:
    """Enforce the codename the operation *type* declares."""
    codename = OPERATION_SPECS[op_type].permission  # type: ignore[index]
    if not ctx.has_permission(codename):
        raise Forbidden(f"Missing required permission: {codename}", code="PERMISSION_DENIED")
    return codename


@router.post("", response_model=OperationOut, status_code=status.HTTP_201_CREATED)
async def create_operation(
    payload: OperationCreate,
    request: Request,
    ctx: ReadCtx,
    db: DbDep,
) -> OperationOut:
    """Queue one whitelisted action for one node in the caller's organization."""
    _require_type_permission(ctx, payload.type)

    operation = await operation_service.create_operation(db, ctx, payload, request=request)
    await audit_service.record(
        db,
        ctx,
        action="operation.create",
        resource_type="operation",
        resource_id=operation.id,
        metadata={"node_id": str(operation.node_id), "type": str(operation.type)},
        request=request,
    )
    return OperationOut.model_validate(operation)


@router.get("", response_model=Page[OperationOut])
async def list_operations(
    ctx: ReadCtx,
    db: DbDep,
    params: Annotated[PageParams, Depends(page_params)],
    node_id: uuid.UUID | None = Query(None),
    status_filter: OperationStatus | None = Query(None, alias="status"),
) -> Page[OperationOut]:
    """Operations in the active organization, newest first."""
    items, total = await operation_service.list_operations(
        db,
        node_id=node_id,
        status=status_filter,
        limit=params.limit,
        offset=params.offset,
    )
    return Page(
        items=[OperationOut.model_validate(item) for item in items],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/{operation_id}", response_model=OperationOut)
async def get_operation(
    operation_id: uuid.UUID,
    ctx: ReadCtx,
    db: DbDep,
) -> OperationOut:
    """One operation's current state."""
    return OperationOut.model_validate(await operation_service.get_operation(db, operation_id))


@router.post("/{operation_id}/cancel", response_model=OperationOut)
async def cancel_operation(
    operation_id: uuid.UUID,
    request: Request,
    ctx: ReadCtx,
    db: DbDep,
) -> OperationOut:
    """Cancel a still-pending operation.

    A claimed operation is already in the node's hands and cannot be recalled —
    the control plane has no channel to the node by design.
    """
    # Read first so the permission checked is the one this operation's type
    # declares; a foreign id is a 404 here, before any codename is revealed.
    existing = await operation_service.get_operation(db, operation_id)
    _require_type_permission(ctx, existing.type)

    operation = await operation_service.cancel_operation(db, operation_id)
    await audit_service.record(
        db,
        ctx,
        action="operation.cancel",
        resource_type="operation",
        resource_id=operation.id,
        metadata={"node_id": str(operation.node_id), "type": str(operation.type)},
        request=request,
    )
    return OperationOut.model_validate(operation)
