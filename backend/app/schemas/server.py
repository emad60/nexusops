"""Server API schemas: create/update payloads, list/detail outputs, enrollment."""

from __future__ import annotations

import ipaddress
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import AfterValidator, Field, computed_field

from app.core.errors import UnprocessableEntity
from app.models.enums import ServerStatus
from app.schemas.base import APIModel, OutModel
from app.schemas.tag import TagRef


def _validate_ip(value: str | None) -> str | None:
    """Reject non-empty values that are not valid IPv4/IPv6 addresses."""
    if value is None:
        return None
    stripped = value.strip()
    if stripped:
        try:
            ipaddress.ip_address(stripped)
        except ValueError as exc:
            raise UnprocessableEntity(
                f"Invalid IP address: {stripped!r}", code="INVALID_IP"
            ) from exc
    return stripped


def _clean_tag_names(names: list[str]) -> list[str]:
    """Strip, drop empties and de-duplicate tag names case-insensitively."""
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in names:
        name = raw.strip()
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(name)
    return cleaned


IPAddress = Annotated[str, AfterValidator(_validate_ip)]
OptionalIPAddress = Annotated[str | None, AfterValidator(_validate_ip)]
TagNames = Annotated[list[str], AfterValidator(_clean_tag_names)]


class DockerHostSummary(APIModel):
    id: UUID
    name: str
    status: str


class ServerCreate(APIModel):
    """Payload for registering a server."""

    name: str = Field(min_length=1, max_length=120)
    hostname: str = Field(min_length=1, max_length=255)
    ip_address: IPAddress = ""
    os_name: str = Field(default="", max_length=96)
    os_version: str = Field(default="", max_length=96)
    arch: str = Field(default="", max_length=32)
    environment: str = Field(default="production", max_length=32)
    location: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=2000)
    heartbeat_interval_seconds: int = Field(default=30, ge=5, le=3600)
    offline_after_seconds: int | None = Field(default=None, gt=0, le=7 * 86400)
    tags: TagNames = Field(default_factory=list, max_length=50)
    simulated: bool = False


class ServerUpdate(APIModel):
    """Partial update. ``tags`` replaces the full set when provided."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    hostname: str | None = Field(default=None, min_length=1, max_length=255)
    ip_address: OptionalIPAddress = None
    os_name: str | None = Field(default=None, max_length=96)
    os_version: str | None = Field(default=None, max_length=96)
    arch: str | None = Field(default=None, max_length=32)
    environment: str | None = Field(default=None, max_length=32)
    location: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    heartbeat_interval_seconds: int | None = Field(default=None, ge=5, le=3600)
    offline_after_seconds: int | None = Field(default=None, gt=0, le=7 * 86400)
    tags: TagNames | None = Field(default=None, max_length=50)
    simulated: bool | None = None


class ServerOut(OutModel):
    """Server as listed in collections. Never exposes the agent token hash."""

    name: str
    hostname: str
    ip_address: str
    os_name: str
    os_version: str
    arch: str
    environment: str
    location: str
    description: str
    status: ServerStatus
    cpu_cores: int
    memory_total_mb: int
    disk_total_gb: int
    agent_version: str
    agent_enrolled_at: datetime | None
    last_heartbeat_at: datetime | None
    heartbeat_interval_seconds: int
    offline_after_seconds: int | None
    uptime_seconds: int
    simulated: bool
    tags: list[TagRef] = Field(default_factory=list)
    docker_host: DockerHostSummary | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def enrolled(self) -> bool:
        return self.agent_enrolled_at is not None


class SystemEventOut(APIModel):
    """Compact system event projection for server timelines."""

    id: UUID
    type: str
    level: str
    message: str = ""
    resource_type: str | None = None
    resource_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ServerCounts(APIModel):
    containers_running: int = 0
    containers_total: int = 0


class ServerDetail(ServerOut):
    """Full server view with recent timeline events and container counts."""

    recent_events: list[SystemEventOut] = Field(default_factory=list)
    counts: ServerCounts = Field(default_factory=ServerCounts)


class EnrollTokenOut(APIModel):
    """One-time agent enrollment token. The raw value is never stored."""

    agent_token: str
    install_hint: str
