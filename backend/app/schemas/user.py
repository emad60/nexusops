"""User request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.models import Membership, User
from app.models.enums import MembershipStatus, UserStatus
from app.schemas.base import APIModel, OutModel


class UserOut(OutModel):
    """Public user representation. Never exposes password hashes or the superadmin flag.

    ``role``/``membership_status`` describe the caller's organization, not the
    account: a person is an Admin in one tenant and a Viewer in another, so a
    representation that showed the account's default role would be meaningless
    (and, read from the wrong tenant, misleading). ``is_active``/``status``
    remain the *account* state, which is instance-wide by nature.
    """

    email: EmailStr
    full_name: str
    is_active: bool
    status: UserStatus
    role_id: UUID | None = None
    role_name: str | None = None
    membership_status: MembershipStatus | None = None
    last_login_at: datetime | None = None

    @classmethod
    def from_user(cls, user: User, membership: Membership | None = None) -> UserOut:
        """Build from an ORM user, preferring the membership's role when given.

        ``membership`` is loaded by every org-scoped caller (the directory, the
        member lookup); it is omitted only on the create path, where the two
        roles are identical by construction and no directory row exists yet.
        """
        role = membership.role if membership is not None else user.role
        return cls(
            id=user.id,
            created_at=user.created_at,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            status=UserStatus(user.status),
            role_id=membership.role_id if membership is not None else user.role_id,
            role_name=role.name if role else None,
            membership_status=(
                MembershipStatus(membership.status) if membership is not None else None
            ),
            last_login_at=user.last_login_at,
        )


class UserCreateRequest(APIModel):
    email: EmailStr
    password: str | None = Field(default=None, min_length=1, max_length=1024)
    full_name: str = Field(default="", max_length=160)
    role_id: UUID


class UserUpdateRequest(APIModel):
    """PATCH semantics: ``None`` means "leave unchanged"."""

    full_name: str | None = Field(default=None, max_length=160)
    role_id: UUID | None = None
    is_active: bool | None = None


class UserCreatedOut(APIModel):
    """Creation result; ``initial_password`` is rendered exactly once."""

    user: UserOut
    initial_password: str | None = None


class UserEnvelope(APIModel):
    user: UserOut
