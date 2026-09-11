"""Secrets manager API.

Reads return metadata only; plaintext values are accepted on create/rotate and
never echoed back. Resolution into deployments happens server-side only.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.schemas.secret import SecretCreate, SecretOut, SecretRotate
from app.services import secret_service

secrets_router = APIRouter(prefix="/secrets", tags=["secrets"])

DbSession = Annotated[AsyncSession, Depends(get_session)]
PageParamsDep = Annotated[PageParams, Depends(page_params)]


@secrets_router.get("", response_model=Page[SecretOut])
async def list_secrets(
    ctx: Annotated[AuthContext, Depends(require_permission("secret.read"))],
    db: DbSession,
    params: PageParamsDep,
    q: str | None = Query(None, description="Case-insensitive key substring"),
    project_id: uuid.UUID | None = Query(None),
) -> Page[SecretOut]:
    """Paginated secret metadata (keys, versions, digests — never values)."""
    items, total = await secret_service.list_secrets(db, q=q, project_id=project_id, params=params)
    return Page(
        items=[SecretOut.model_validate(item) for item in items],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@secrets_router.get("/{secret_id}", response_model=SecretOut)
async def get_secret(
    secret_id: uuid.UUID,
    ctx: Annotated[AuthContext, Depends(require_permission("secret.read"))],
    db: DbSession,
) -> SecretOut:
    """One secret's metadata."""
    return SecretOut.model_validate(await secret_service.get_secret_detail(db, secret_id))


@secrets_router.post("", response_model=SecretOut, status_code=status.HTTP_201_CREATED)
async def create_secret(
    payload: SecretCreate,
    request: Request,
    ctx: Annotated[AuthContext, Depends(require_permission("secret.write"))],
    db: DbSession,
) -> SecretOut:
    """Create an encrypted secret scoped to a project or globally."""
    secret = await secret_service.create_secret(
        db,
        ctx,
        key=payload.key,
        value=payload.value,
        project_id=payload.project_id,
        description=payload.description,
        request=request,
    )
    return SecretOut.model_validate(await secret_service.get_secret_detail(db, secret.id))


@secrets_router.post("/{secret_id}/rotate", response_model=SecretOut)
async def rotate_secret(
    secret_id: uuid.UUID,
    payload: SecretRotate,
    request: Request,
    ctx: Annotated[AuthContext, Depends(require_permission("secret.write"))],
    db: DbSession,
) -> SecretOut:
    """Replace the encrypted value and bump the version."""
    secret = await secret_service.rotate_secret(db, ctx, secret_id, payload.value, request=request)
    return SecretOut.model_validate(await secret_service.get_secret_detail(db, secret.id))


@secrets_router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: uuid.UUID,
    request: Request,
    ctx: Annotated[AuthContext, Depends(require_permission("secret.write"))],
    db: DbSession,
) -> None:
    """Permanently remove a secret."""
    await secret_service.delete_secret(db, ctx, secret_id, request=request)
