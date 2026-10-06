"""Organization (tenant) routes.

These are the only authenticated routes that run **without** an organization
scope, and they exist precisely so a client can discover and choose one:

* ``GET /organizations`` answers "where may I act?" from the caller's
  memberships, which is a cross-organization read by construction (validating
  ``X-Org-Id`` *is* that read).
* ``POST /organizations`` is instance-operator only.
* ``PATCH /organizations/{org_id}`` is org-scoped: it requires the active
  organization to be the one addressed, so it can never touch another tenant's
  record.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbSessionDep, IdentityUser, active_memberships
from app.schemas.organization import (
    MembershipOut,
    OrganizationCreateRequest,
    OrganizationOut,
    OrganizationUpdateRequest,
)
from app.services import organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[MembershipOut])
async def list_my_organizations(ctx: IdentityUser, db: DbSessionDep) -> list[MembershipOut]:
    """Every organization the caller may act in, with their role in each.

    Only active memberships in non-suspended organizations are returned, so the
    list is exactly the set that ``X-Org-Id`` validation will accept.
    """
    memberships = await active_memberships(db, ctx.user_id)
    return [MembershipOut.from_membership(m) for m in memberships]


@router.post("", status_code=201, response_model=MembershipOut)
async def create_organization(
    body: OrganizationCreateRequest, ctx: IdentityUser, db: DbSessionDep, request: Request
) -> MembershipOut:
    """Create an organization and become its Owner (instance operators only)."""
    _org, membership = await organization_service.create_organization(
        db,
        actor=ctx,
        name=body.name,
        description=body.description,
        request=request,
    )
    # The service populated the membership's relationships at creation time
    # (selectin loading never fires on flush), so this needs no further IO.
    return MembershipOut.from_membership(membership)


@router.patch("/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: UUID,
    body: OrganizationUpdateRequest,
    ctx: CurrentUser,
    db: DbSessionDep,
    request: Request,
) -> OrganizationOut:
    """Rename or describe the organization this request is acting in."""
    org = await organization_service.update_organization(
        db,
        actor=ctx,
        org_id=org_id,
        name=body.name,
        description=body.description,
        request=request,
    )
    return OrganizationOut.from_org(org)
