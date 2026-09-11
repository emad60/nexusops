"""Canonical registry of system-event types.

Single source of truth shared by emitters (event_bus callers), the events API
(``GET /events/types``) and the WebSocket hub. Event types are SCREAMING_SNAKE
strings so they survive JSON round-trips without enum coupling.
"""

from __future__ import annotations

EVENT_TYPES: dict[str, str] = {
    # servers
    "SERVER_ONLINE": "Server agent came online",
    "SERVER_OFFLINE": "Server missed heartbeats and is offline",
    "SERVER_CREATED": "Server registered",
    "SERVER_UPDATED": "Server details updated",
    "SERVER_DELETED": "Server removed",
    # containers
    "CONTAINER_STARTED": "Container started",
    "CONTAINER_STOPPED": "Container stopped",
    "CONTAINER_RESTARTED": "Container restarted",
    "CONTAINER_REMOVED": "Container removed",
    # delivery
    "DEPLOYMENT_QUEUED": "Deployment queued",
    "DEPLOYMENT_STARTED": "Deployment started running",
    "DEPLOYMENT_SUCCEEDED": "Deployment finished successfully",
    "DEPLOYMENT_FAILED": "Deployment failed",
    "DEPLOYMENT_CANCELLED": "Deployment cancelled",
    # monitoring
    "MONITOR_DOWN": "Monitor exceeded its failure threshold",
    "MONITOR_RECOVERED": "Monitor recovered after failures",
    "INCIDENT_OPENED": "Incident opened",
    "INCIDENT_ACKNOWLEDGED": "Incident acknowledged",
    "INCIDENT_RESOLVED": "Incident resolved",
    # identity & access
    "USER_LOGIN": "User signed in",
    "USER_LOGOUT": "User signed out",
    "USER_CREATED": "User account created",
    "USER_PASSWORD_CHANGED": "User password changed",
    "PERMISSION_CHANGED": "Role permissions or role assignment changed",
    "API_KEY_CREATED": "API key created",
    "API_KEY_REVOKED": "API key revoked",
    # secrets & notifications
    "SECRET_UPDATED": "Secret created, rotated or deleted (value never included)",
    "CHANNEL_TESTED": "Notification channel test sent",
    "NOTIFICATION_FAILED": "Notification delivery failed",
}

#: Types surfaced to the ``incidents`` WebSocket channel.
INCIDENT_CHANNEL_PREFIXES: tuple[str, ...] = ("INCIDENT_", "MONITOR_")


def is_known_event_type(event_type: str) -> bool:
    """Return True when *event_type* is part of the canonical registry."""
    return event_type in EVENT_TYPES


def event_type_catalogue() -> list[dict[str, str]]:
    """Serialise the registry for the ``/events/types`` endpoint."""
    return [{"type": t, "description": d} for t, d in EVENT_TYPES.items()]
