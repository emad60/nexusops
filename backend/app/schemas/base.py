"""Shared Pydantic v2 base schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base for request/response models: ORM mode + strict-ish population."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")


class OutModel(APIModel):
    """Response model base — timestamps serialized as ISO-8601 UTC."""

    id: UUID
    created_at: datetime
