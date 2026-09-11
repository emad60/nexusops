"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.base import APIModel
from app.schemas.user import UserEnvelope, UserOut

__all__ = [
    "LoginRequest",
    "MeOut",
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
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type literal, not a secret
    expires_in: int
    user: UserOut


class MeOut(APIModel):
    user: UserOut
    role: str | None = None
    permissions: list[str]
    superadmin: bool
