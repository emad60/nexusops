"""API key schemas. Raw keys appear exactly once, at creation."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models import ApiKey
from app.schemas.base import APIModel, OutModel


class ApiKeyCreateRequest(APIModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1, max_length=64)
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class ApiKeyOut(OutModel):
    """Metadata only — the key hash and raw secret are never rendered."""

    name: str
    key_prefix: str
    scopes: list[str]
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @classmethod
    def from_key(cls, key: ApiKey) -> ApiKeyOut:
        return cls(
            id=key.id,
            created_at=key.created_at,
            name=key.name,
            key_prefix=key.key_prefix,
            scopes=list(key.scopes or []),
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
            revoked_at=key.revoked_at,
        )


class ApiKeyCreatedOut(ApiKeyOut):
    """Creation response; ``key`` is the raw secret shown exactly once."""

    key: str
