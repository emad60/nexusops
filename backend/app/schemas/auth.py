"""Authentication request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import APIModel
from app.schemas.organization import MembershipOut, OrganizationOut
from app.schemas.user import UserEnvelope, UserOut

__all__ = [
    "LoginRequest",
    "MeOut",
    "MembershipOut",
    "OrganizationOut",
    "PasswordChangeRequest",
    "RefreshRequest",
    "RegisterRequest",
    "TokenOut",
    "UserEnvelope",
    "UserOut",
]


class RegisterRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)
    full_name: str = Field(default="", max_length=160)


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class RefreshRequest(APIModel):
    """Optional body for non-browser clients; the cookie takes precedence."""

    refresh_token: str | None = Field(default=None, min_length=1, max_length=512)


class PasswordChangeRequest(APIModel):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=1, max_length=1024)


class TokenOut(APIModel):
    """Token response, plus everything a client needs to pick an organization.

    The JWT carries identity only — never a tenant — so the client has to be told
    which organizations it may act in and which one it should default to. Both
    fields are derived from active memberships at issue time; a stale org id in
    a client is not trusted later (every request re-validates ``X-Org-Id``).
    """

    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type literal, not a secret
    expires_in: int
    user: UserOut
    organizations: list[MembershipOut] = Field(default_factory=list)
    #: Set only when the choice is unambiguous (exactly one active membership).
    active_organization_id: UUID | None = None


class MeOut(APIModel):
    """Caller identity, their organizations, and their authority in the active one.

    This is the one authenticated route that works without ``X-Org-Id``: it is
    how a client discovers which organizations exist to choose from. Send the
    header and the response additionally reports the resolved organization and
    the permissions it grants there.
    """

    user: UserOut
    role: str | None = None
    permissions: list[str]
    superadmin: bool
    organizations: list[MembershipOut] = Field(default_factory=list)
    active_organization_id: UUID | None = None
    active_organization: OrganizationOut | None = None
