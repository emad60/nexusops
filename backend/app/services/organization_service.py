"""Organizations (tenants) and memberships.

Who may do what here is a product decision, decided once and referenced
everywhere: **v1 onboards through operator-issued invites to pre-created
organizations**, not self-serve signup. Creating an organization is therefore
reserved to instance operators (``User.is_superadmin``), while managing members
*inside* an organization is ordinary ``user.manage`` scoped to that tenant.

Everything in this module runs on the pre-org credential/identity tables
(organizations, memberships) or inside an explicit organization scope, so the
tenancy guard is not the thing keeping these calls honest — the membership
checks are.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.core.tenancy import apply_scope_to_session, org_scope
from app.models import Membership, Organization, Role, User
from app.models.enums import ActorType, MembershipStatus, OrganizationStatus
from app.services import audit_service, event_bus

_SLUG_RE = re.compile(r"[^a-z0-9]+")

#: The role the creator of an organization receives, and the role new members
#: get when no role is named. ``Owner`` holds the wildcard permission.
DEFAULT_OWNER_ROLE = "Owner"
DEFAULT_MEMBER_ROLE = "Viewer"


def slugify(value: str) -> str:
    """ASCII slug from a display name; never empty."""
    slug = _SLUG_RE.sub("-", value.strip().lower()).strip("-")
    return (slug or "organization")[:140]


async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Organization:
    """Fetch an organization or raise NotFound."""
    org = await db.get(Organization, org_id)
    if org is None:
        raise NotFound("Organization not found", code="ORGANIZATION_NOT_FOUND")
    return org


async def _system_role(db: AsyncSession, name: str) -> Role | None:
    return (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()


async def unique_slug(db: AsyncSession, base: str, *, exclude: uuid.UUID | None = None) -> str:
    """``base``, or ``base-2``, ``base-3``… — slugs are instance-unique."""
    candidate = base
    suffix = 1
    while True:
        stmt = select(Organization.id).where(Organization.slug == candidate)
        if exclude is not None:
            stmt = stmt.where(Organization.id != exclude)
        if (await db.execute(stmt)).scalar_one_or_none() is None:
            return candidate
        suffix += 1
        candidate = f"{base[:134]}-{suffix}"


async def unique_name(db: AsyncSession, base: str, *, exclude: uuid.UUID | None = None) -> str:
    candidate = base
    suffix = 1
    while True:
        stmt = select(Organization.id).where(Organization.name == candidate)
        if exclude is not None:
            stmt = stmt.where(Organization.id != exclude)
        if (await db.execute(stmt)).scalar_one_or_none() is None:
            return candidate
        suffix += 1
        candidate = f"{base[:114]} ({suffix})"


async def create_organization(
    db: AsyncSession,
    *,
    actor: AuthContext,
    name: str,
    description: str = "",
    request: Request | None = None,
) -> tuple[Organization, Membership]:
    """Create an organization and make *actor* its Owner.

    Restricted to instance operators. Letting any authenticated user mint
    organizations would turn tenant creation into a self-service surface with no
    billing or abuse controls — and would let a member of one tenant create a
    fresh tenant purely to escape its permissions.
    """
    if not actor.user.is_superadmin:
        raise Forbidden(
            "Only an instance operator can create organizations in this version",
            code="ORGANIZATION_CREATE_FORBIDDEN",
        )

    clean_name = name.strip()
    if not clean_name:
        raise BadRequest("name must not be blank", code="INVALID_ORGANIZATION_NAME")

    now = datetime.now(UTC)
    org = Organization(
        name=await unique_name(db, clean_name),
        slug=await unique_slug(db, slugify(clean_name)),
        description=description.strip(),
        status=OrganizationStatus.ACTIVE,
        # A deliberately created organization is not provisional — only the
        # migration's auto-provisioned one is.
        is_provisional=False,
        created_by_id=actor.user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(org)
    try:
        await db.flush()
    except IntegrityError as exc:  # concurrent same-name creation
        await db.rollback()
        raise Conflict(
            "Organization name is already taken", code="ORGANIZATION_NAME_TAKEN"
        ) from exc

    owner_role = await _system_role(db, DEFAULT_OWNER_ROLE)
    membership = Membership(
        org_id=org.id,
        user_id=actor.user_id,
        role_id=owner_role.id if owner_role else None,
        status=MembershipStatus.ACTIVE,
        created_by_id=actor.user_id,
        created_at=now,
        updated_at=now,
    )
    # Relationship loading is selectin, which never fires on flush; populate
    # them here so the response serializes without a lazy round trip.
    membership.organization = org
    membership.role = owner_role
    db.add(membership)
    await db.flush()

    # The audit row and the event belong to the organization that was just
    # created, and PostgreSQL will only accept them under its scope — this route
    # deliberately runs without one (the caller is choosing a tenant). The
    # session already has a transaction open from the inserts, so the scope has
    # to be pushed onto the connection explicitly.
    with org_scope(org.id):
        await apply_scope_to_session(db)
        await audit_service.record(
            db,
            actor,
            action="organization.create",
            resource_type="organization",
            resource_id=org.id,
            metadata={"name": org.name, "slug": org.slug},
            request=request,
            # The row is about the *new* organization, so it must not inherit
            # the organization the caller happened to be acting in — the audit
            # reader for that tenant did not create this one.
            org_id=org.id,
        )
        await event_bus.publish(
            db,
            type="ORGANIZATION_CREATED",
            message=f"Organization {org.name} created",
            actor_id=actor.user_id,
            actor_type=ActorType.USER,
            resource_type="organization",
            resource_id=str(org.id),
            data={"name": org.name, "slug": org.slug},
            org_id=org.id,
        )
    return org, membership


async def update_organization(
    db: AsyncSession,
    *,
    actor: AuthContext,
    org_id: uuid.UUID,
    name: str | None = None,
    description: str | None = None,
    request: Request | None = None,
) -> Organization:
    """Rename/describe an organization the caller is currently acting in."""
    if actor.org_id != org_id:
        # A caller can only ever be inside one organization per request; asking
        # to modify another is answered exactly like a missing one.
        raise NotFound("Organization not found", code="ORGANIZATION_NOT_FOUND")
    if not actor.has_permission("user.manage"):
        raise Forbidden("Managing an organization requires user.manage", code="PERMISSION_DENIED")

    org = await get_organization(db, org_id)
    changes: dict[str, object] = {}

    if name is not None:
        clean = name.strip()
        if not clean:
            raise BadRequest("name must not be blank", code="INVALID_ORGANIZATION_NAME")
        if clean != org.name:
            changes["name"] = {"from": org.name, "to": clean}
            org.name = await unique_name(db, clean, exclude=org.id)
            org.slug = await unique_slug(db, slugify(org.name), exclude=org.id)
    if description is not None and description.strip() != org.description:
        changes["description"] = True
        org.description = description.strip()

    if not changes:
        return org

    if org.is_provisional:
        # The provisional name exists to be replaced. Naming the tenant is the
        # signal that it is now a real one.
        org.is_provisional = False
        org.renamed_at = datetime.now(UTC)
        changes["provisional_cleared"] = True

    await db.flush()
    await audit_service.record(
        db,
        actor,
        action="organization.update",
        resource_type="organization",
        resource_id=org.id,
        metadata={"changes": changes},
        request=request,
    )
    await event_bus.publish(
        db,
        type="ORGANIZATION_UPDATED",
        message=f"Organization {org.name} updated",
        actor_id=actor.user_id,
        actor_type=ActorType.USER,
        resource_type="organization",
        resource_id=str(org.id),
        data={"changes": changes},
    )
    return org


async def add_member(
    db: AsyncSession,
    *,
    actor: AuthContext,
    org_id: uuid.UUID,
    user: User,
    role_id: uuid.UUID,
    request: Request | None = None,
) -> Membership:
    """Attach an existing user to an organization with a role.

    The role is the membership's, not the user's: the same account can be an
    Admin here and a Viewer elsewhere. ``User.role_id`` is left untouched — it
    is only a default for the *next* membership created for that user.
    """
    if actor.org_id != org_id:
        raise NotFound("Organization not found", code="ORGANIZATION_NOT_FOUND")
    if not actor.has_permission("user.manage"):
        raise Forbidden("Adding members requires user.manage", code="PERMISSION_DENIED")

    role = await db.get(Role, role_id)
    if role is None:
        raise NotFound("Role not found", code="ROLE_NOT_FOUND")

    existing = (
        await db.execute(
            select(Membership).where(Membership.org_id == org_id, Membership.user_id == user.id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise Conflict("User is already a member of this organization", code="ALREADY_MEMBER")

    now = datetime.now(UTC)
    membership = Membership(
        org_id=org_id,
        user_id=user.id,
        role_id=role.id,
        status=MembershipStatus.ACTIVE,
        created_by_id=actor.user_id,
        created_at=now,
        updated_at=now,
    )
    db.add(membership)
    await db.flush()

    await audit_service.record(
        db,
        actor,
        action="organization.member.add",
        resource_type="membership",
        resource_id=membership.id,
        metadata={"user_id": str(user.id), "role": role.name},
        request=request,
    )
    await event_bus.publish(
        db,
        type="MEMBERSHIP_ADDED",
        message=f"{user.email} added to {actor.org.name if actor.org else 'the organization'}",
        actor_id=actor.user_id,
        actor_type=ActorType.USER,
        resource_type="membership",
        resource_id=str(membership.id),
        data={"user_id": str(user.id), "role": role.name},
    )
    return membership


async def membership_for_user(
    db: AsyncSession, *, org_id: uuid.UUID, user_id: uuid.UUID
) -> Membership | None:
    """A user's membership in one organization (any status)."""
    return (
        await db.execute(
            select(Membership).where(Membership.org_id == org_id, Membership.user_id == user_id)
        )
    ).scalar_one_or_none()
