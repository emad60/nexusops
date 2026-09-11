"""Public metadata schema + the canonical system-event type registry."""

from __future__ import annotations

from pydantic import Field

from app.schemas.base import APIModel

#: Canonical event type strings. Every event_bus.publish(type=...) in the repo
#: MUST use one of these values; /meta advertises them to clients.
EVENT_TYPES: tuple[str, ...] = (
    "SERVER_ONLINE",
    "SERVER_OFFLINE",
    "SERVER_CREATED",
    "SERVER_UPDATED",
    "SERVER_DELETED",
    "CONTAINER_STARTED",
    "CONTAINER_STOPPED",
    "CONTAINER_RESTARTED",
    "CONTAINER_REMOVED",
    "DEPLOYMENT_QUEUED",
    "DEPLOYMENT_STARTED",
    "DEPLOYMENT_SUCCEEDED",
    "DEPLOYMENT_FAILED",
    "DEPLOYMENT_CANCELLED",
    "MONITOR_DOWN",
    "MONITOR_RECOVERED",
    "INCIDENT_OPENED",
    "INCIDENT_ACKNOWLEDGED",
    "INCIDENT_RESOLVED",
    "USER_LOGIN",
    "USER_LOGOUT",
    "USER_CREATED",
    "USER_PASSWORD_CHANGED",
    "PERMISSION_CHANGED",
    "API_KEY_CREATED",
    "API_KEY_REVOKED",
    "SECRET_UPDATED",
    "CHANNEL_TESTED",
    "NOTIFICATION_FAILED",
)


class MetaOut(APIModel):
    """Instance metadata. Identity fields are populated only when the caller
    presents valid credentials; otherwise they stay None and are omitted."""

    name: str = "NexusOps"
    version: str = "1.0.0"
    environment: str
    simulation_mode: bool
    event_types: list[str] = Field(default_factory=list)
    permissions: list[str] | None = None
    role: str | None = None
    is_superadmin: bool | None = None
