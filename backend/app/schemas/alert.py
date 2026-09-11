"""Schemas for operator-facing alerts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AlertSeverity
from app.schemas.base import OutModel


class AlertOut(OutModel):
    updated_at: datetime
    severity: AlertSeverity
    title: str
    body: str = ""
    event_type: str = ""
    source: str = "system"
    resource_type: str | None = None
    resource_id: str | None = None
    read_at: datetime | None = None


class UnreadCountOut(BaseModel):
    count: int


__all__ = ["AlertOut", "UnreadCountOut"]
