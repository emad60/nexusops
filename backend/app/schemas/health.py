"""Health / readiness schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.base import APIModel


class HealthOut(APIModel):
    """Liveness body — always 200 while the process can serve at all."""

    status: Literal["alive"] = "alive"


class ReadyComponents(APIModel):
    database: str = "unknown"
    redis: str = "unknown"


class ReadyOut(APIModel):
    """Readiness body; 503 with the failing components when not ready."""

    status: Literal["ready", "unavailable"]
    components: ReadyComponents = Field(default_factory=ReadyComponents)
