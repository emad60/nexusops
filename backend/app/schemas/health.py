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
    #: Key-management (KEK provider) status: one of ``ok``, ``disabled``,
    #: ``unreachable``, ``unauthorized``, ``invalid_configuration``. **Informational
    #: only** — it never gates readiness, because the platform keeps serving the
    #: features that do not need a DEK while the provider is down (phase5-design.md
    #: §6.9). Only the status is exposed: never the provider's address, key name or
    #: any credential.
    key_management: str = "unknown"


class ReadyOut(APIModel):
    """Readiness body; 503 with the failing components when not ready."""

    status: Literal["ready", "unavailable"]
    components: ReadyComponents = Field(default_factory=ReadyComponents)
