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
    """Active sessions of this organization's members.

    Defaults to the caller's own; ``all``/``user_id`` need ``user.manage`` **in
    the active organization**, and a ``user_id`` outside it is reported as not
    found rather than listed or refused (see :func:`require_member`).
    """
    if (all_users or user_id is not None) and not ctx.has_permission("user.manage"):
        raise Forbidden(
            "Listing other users' sessions requires the user.manage permission",
            code="PERMISSION_DENIED",
        )
    org_id = ctx.require_org_id()
    if user_id is not None and user_id != ctx.user_id:
        # Membership is the boundary: an admin may look at the sessions of the
        # people in their own organization and no one else.
        await user_service.get_member(db, user_id=user_id, org_id=org_id)
    # ``all`` widens the listing to every member of the organization; without it
    # (and without an explicit ``user_id``) the caller sees only their own
    # sessions. ``None`` means "any member", never "any user" — the service
    # intersects with the organization's memberships.
    target_user_id = user_id if user_id is not None else (None if all_users else ctx.user_id)
    rows, total = await user_service.list_sessions(
        db,
        org_id=org_id,
        params=params,
        user_id=target_user_id,
    )
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
