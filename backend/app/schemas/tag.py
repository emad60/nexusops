"""Server tag schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.base import APIModel, OutModel


class TagRef(APIModel):
    """Minimal tag reference embedded in server payloads."""

    id: UUID
    name: str
    color: str


class TagOut(OutModel):
    """Tag with its usage count across servers."""

    name: str
    color: str
    usage_count: int = 0


class TagUpsertIn(APIModel):
    """Create-or-update payload for a tag."""

    name: str = Field(min_length=1, max_length=64)
    color: str = Field(
        default="#64748b",
        max_length=16,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Hex RGB colour, e.g. #38bdf8",
    )
