"""User request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.models import User
from app.models.enums import UserStatus
from app.schemas.base import APIModel, OutModel


class UserOut(OutModel):
    """Public user representation. Never exposes password hashes or the superadmin flag."""

    email: EmailStr
    full_name: str
    is_active: bool
    status: UserStatus
    role_id: UUID | None = None
    role_name: str | None = None
    last_login_at: datetime | None = None

    @classmethod
    def from_user(cls, user: User) -> UserOut:
        """Build from an ORM user whose ``role`` relationship is loaded."""
        role = user.role
        return cls(
            id=user.id,
            created_at=user.created_at,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            status=UserStatus(user.status),
            role_id=user.role_id,
            role_name=role.name if role else None,
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
