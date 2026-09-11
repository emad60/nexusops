"""Session routes: list active sessions, revoke own or (with user.manage) any."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import CurrentUser, DbSessionDep
from app.core.errors import Forbidden
from app.core.pagination import Page, PageParams, page_params
from app.schemas.session import SessionOut
from app.services import user_service

router = APIRouter(prefix="/sessions", tags=["sessions"])

_PageParams = Annotated[PageParams, Depends(page_params)]


@router.get("", response_model=Page[SessionOut])
async def list_sessions(
    ctx: CurrentUser,
    db: DbSessionDep,
    params: _PageParams,
    all_users: bool = Query(False, alias="all", description="Requires user.manage"),
    user_id: UUID | None = Query(None, description="Filter by owner (requires user.manage)"),
) -> Page[SessionOut]:
    """Active sessions. Defaults to the caller's own; ``all``/``user_id`` need user.manage."""
    if (all_users or user_id is not None) and not ctx.has_permission("user.manage"):
        raise Forbidden(
            "Listing other users' sessions requires the user.manage permission",
            code="PERMISSION_DENIED",
        )
    target_user_id = user_id or ctx.user_id
    rows, total = await user_service.list_sessions(db, user_id=target_user_id, params=params)
    return Page(
        items=[SessionOut.from_session(row, current=row.id == ctx.session_id) for row in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: UUID, ctx: CurrentUser, db: DbSessionDep, request: Request
) -> None:
    """Revoke a session and its refresh tokens. Own session always; others need user.manage."""
    await user_service.revoke_session_as(db, ctx=ctx, session_id=session_id, request=request)
