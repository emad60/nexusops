"""Schemas for incidents and their timeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import IncidentEventKind, IncidentSeverity, IncidentStatus
from app.schemas.base import APIModel, OutModel


class IncidentEventOut(APIModel):
    id: UUID
    kind: IncidentEventKind
    message: str = ""
    actor_id: UUID | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime


class IncidentOut(OutModel):
    """Incident as listed; timeline is only on the detail representation."""

    updated_at: datetime
    monitor_id: UUID
    monitor_name: str | None = None
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    failure_count: int
    opened_at: datetime
    detected_at: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by_id: UUID | None = None
    resolved_at: datetime | None = None
    resolution: str = ""


class IncidentDetail(IncidentOut):
    timeline: list[IncidentEventOut] = Field(default_factory=list)


class IncidentAcknowledge(APIModel):
    """Payload for POST /incidents/{id}/acknowledge."""

    note: str | None = Field(default=None, max_length=2000)


class IncidentResolve(APIModel):
    """Payload for POST /incidents/{id}/resolve."""

    resolution: str = Field(min_length=1, max_length=4000)


class IncidentNote(APIModel):
    """Payload for POST /incidents/{id}/notes."""

    message: str = Field(min_length=1, max_length=2000)


class IncidentSortField:
    OPENED_AT = "opened_at"

    ALL = frozenset({OPENED_AT})


__all__ = [
    "IncidentAcknowledge",
    "IncidentDetail",
    "IncidentEventOut",
    "IncidentNote",
    "IncidentOut",
    "IncidentResolve",
    "IncidentSortField",
]
