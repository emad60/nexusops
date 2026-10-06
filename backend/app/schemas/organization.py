"""Organization (tenant) schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.models import Membership, Organization
from app.models.enums import MembershipStatus, OrganizationStatus
from app.schemas.base import APIModel, OutModel


class OrganizationOut(OutModel):
    """An organization as seen by a member of it."""

    name: str
    slug: str
    description: str
    status: OrganizationStatus
    #: True for the organization the tenancy migration auto-provisioned for
    #: pre-existing data. Every surface that shows it says so, because a
    #: provisional tenant must never be mistaken for a deliberately named one.
    is_provisional: bool
    renamed_at: datetime | None = None

    @classmethod
    def from_org(cls, org: Organization) -> OrganizationOut:
        return cls(
            id=org.id,
            created_at=org.created_at,
            name=org.name,
            slug=org.slug,
            description=org.description,
            status=OrganizationStatus(org.status),
            is_provisional=org.is_provisional,
            renamed_at=org.renamed_at,
        )


class MembershipOut(APIModel):
    """The caller's own membership: an organization plus their role in it.

    Deliberately carries no other member's data — the organization list is
    "where can I act", not "who else is here" (that is the ``user.read``
    directory, which is itself org-scoped).
    """

    organization: OrganizationOut
    role_name: str | None = None
    role_id: UUID | None = None
    status: MembershipStatus

    @classmethod
    def from_membership(cls, membership: Membership) -> MembershipOut:
        role = membership.role
        return cls(
            organization=OrganizationOut.from_org(membership.organization),
            role_name=role.name if role else None,
            role_id=membership.role_id,
            status=MembershipStatus(membership.status),
        )


class OrganizationCreateRequest(APIModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class OrganizationUpdateRequest(APIModel):
    """PATCH semantics: ``None`` means "leave unchanged"."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class OrganizationMemberInvite(APIModel):
    """Invite an existing or new user into an organization.

    v1 onboarding is operator-issued rather than self-serve: an administrator
    creates the account (or reuses one) and the membership in the same call.
    """

    email: EmailStr
    role_id: UUID
    full_name: str = Field(default="", max_length=160)
