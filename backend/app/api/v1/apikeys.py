"""API key routes — self-service management of the caller's own machine credentials."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import CurrentUser, DbSessionDep
from app.core.pagination import Page, PageParams, page_params
from app.schemas.apikey import ApiKeyCreatedOut, ApiKeyCreateRequest, ApiKeyOut
from app.services import api_key_service

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

_PageParams = Annotated[PageParams, Depends(page_params)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiKeyCreatedOut)
async def create_api_key(
    body: ApiKeyCreateRequest, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> ApiKeyCreatedOut:
    """Create a key for the caller. The raw secret appears exactly once."""
    key, raw_key = await api_key_service.create_api_key(
        db,
        actor=ctx,
        user_id=ctx.user_id,
        name=body.name,
        scopes=body.scopes,
        expires_in_days=body.expires_in_days,
        request=request,
    )
    return ApiKeyCreatedOut(**ApiKeyOut.from_key(key).model_dump(), key=raw_key)


@router.get("", response_model=Page[ApiKeyOut])
async def list_api_keys(ctx: CurrentUser, db: DbSessionDep, params: _PageParams) -> Page[ApiKeyOut]:
    """The caller's live keys (prefix metadata only — never the secret)."""
    rows, total = await api_key_service.list_api_keys(db, owner_id=ctx.user_id, params=params)
    return Page(
        items=[ApiKeyOut.from_key(k) for k in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> None:
    """Revoke one of the caller's own keys. Foreign keys return 404."""
    await api_key_service.revoke_api_key(
        db, actor=ctx, key_id=key_id, owner_id=ctx.user_id, request=request
    )
