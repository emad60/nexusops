"""Schemas for the system events feed."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.schemas.base import APIModel, OutModel


class EventOut(OutModel):
    """One persisted system event."""

    type: str
    level: str
    message: str = ""
    actor_id: UUID | None = None
    actor_type: str
    resource_type: str | None = None
    resource_id: str | None = None
    data: dict[str, Any]


class EventTypeOut(APIModel):
    """Canonical event type with its human description."""

    type: str
    description: str
