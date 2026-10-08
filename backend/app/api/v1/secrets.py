"""Secrets manager API.

Reads return metadata only; plaintext values are accepted on create/rotate and
never echoed back. Resolution into deployments happens server-side only.

Two capabilities are deliberately distinct: ``secret.read`` covers *metadata*,
``secret.write`` covers managing values, and neither is the permission that lets
a deployment *consume* a secret — that is the deploy permission chain
(``deployment.create``). No endpoint in this module returns a value.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.schemas.secret import (
    SecretCreate,
    SecretOut,
    SecretRollback,
    SecretRotate,
    SecretVersionOut,
)
from app.services import secret_service

secrets_router = APIRouter(prefix="/secrets", tags=["secrets"])

DbSession = Annotated[AsyncSession, Depends(get_session)]
PageParamsDep = Annotated[PageParams, Depends(page_params)]
SecretReader = Annotated[AuthContext, Depends(require_permission("secret.read"))]
SecretWriter = Annotated[AuthContext, Depends(require_permission("secret.write"))]


@secrets_router.get("", response_model=Page[SecretOut])
async def list_secrets(
    ctx: SecretReader,
    db: DbSession,
    params: PageParamsDep,
    q: str | None = Query(None, description="Case-insensitive key substring"),
    project_id: uuid.UUID | None = Query(None),
    environment_id: uuid.UUID | None = Query(None),
) -> Page[SecretOut]:
    """Paginated secret metadata (keys, versions, digests — never values)."""
    items, total = await secret_service.list_secrets(
        db, q=q, project_id=project_id, environment_id=environment_id, params=params
    )
    return Page(
        items=[SecretOut.model_validate(item) for item in items],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@secrets_router.get("/{secret_id}", response_model=SecretOut)
async def get_secret(
    secret_id: uuid.UUID,
    ctx: SecretReader,
    db: DbSession,
) -> SecretOut:
    """One secret's metadata."""
    return SecretOut.model_validate(await secret_service.get_secret_detail(db, secret_id))


@secrets_router.get("/{secret_id}/versions", response_model=list[SecretVersionOut])
async def list_secret_versions(
    secret_id: uuid.UUID,
    ctx: SecretReader,
    db: DbSession,
) -> list[SecretVersionOut]:
    """Append-only version history, newest first. Metadata only — never values."""
    rows = await secret_service.list_secret_versions(db, secret_id)
    return [SecretVersionOut.model_validate(row) for row in rows]


@secrets_router.post("", response_model=SecretOut, status_code=status.HTTP_201_CREATED)
async def create_secret(
    payload: SecretCreate,
    request: Request,
    ctx: SecretWriter,
    db: DbSession,
) -> SecretOut:
    """Create an encrypted secret at organization, project or environment scope."""
    secret = await secret_service.create_secret(
        db,
        ctx,
        key=payload.key,
        value=payload.value,
        project_id=payload.project_id,
        environment_id=payload.environment_id,
        description=payload.description,
        request=request,
    )
    return SecretOut.model_validate(await secret_service.get_secret_detail(db, secret.id))


@secrets_router.post("/{secret_id}/rotate", response_model=SecretOut)
async def rotate_secret(
    secret_id: uuid.UUID,
    payload: SecretRotate,
    request: Request,
    ctx: SecretWriter,
    db: DbSession,
) -> SecretOut:
    """Append a new version with a new value and make it current."""
    secret = await secret_service.rotate_secret(db, ctx, secret_id, payload.value, request=request)
    return SecretOut.model_validate(await secret_service.get_secret_detail(db, secret.id))


@secrets_router.post("/{secret_id}/rollback", response_model=SecretOut)
async def rollback_secret(
    secret_id: uuid.UUID,
    payload: SecretRollback,
    request: Request,
    ctx: SecretWriter,
    db: DbSession,
) -> SecretOut:
    """Make a previous version current by appending a new version (non-destructive)."""
    secret = await secret_service.rollback_secret(
        db, ctx, secret_id, payload.version, request=request
    )
    return SecretOut.model_validate(await secret_service.get_secret_detail(db, secret.id))


@secrets_router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: uuid.UUID,
    request: Request,
    ctx: SecretWriter,
    db: DbSession,
) -> None:
    """Permanently remove a secret (and its version history)."""
    await secret_service.delete_secret(db, ctx, secret_id, request=request)
