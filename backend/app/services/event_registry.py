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
    # domains & routing (Phase 4)
    "DOMAIN_CREATED": "Domain added and awaiting DNS verification",
    "DOMAIN_VERIFIED": "Domain ownership verified via its TXT record",
    "DOMAIN_UNVERIFIED": "Domain lost its proof of control; its routes left the desired configuration and each node's removal still has to be confirmed",
    "DOMAIN_STALE": "Domain proof is missing; its routes leave the desired configuration during the grace window",
    "DOMAIN_DELETED": "Domain removed",
    "ROUTE_CREATED": "Route created",
    "ROUTE_ENABLED": "Route enabled and queued for configuration apply",
    "ROUTE_DISABLED": "Route disabled and removed at the next configuration apply",
    "ROUTE_DELETED": "Route deleted",
    "ROUTE_APPLIED": "Node configuration applied for a route",
    "ROUTE_APPLY_FAILED": "Node configuration apply failed for a route",
    "ROUTE_REMOVAL_REQUESTED": "Route is out of the desired configuration; no node has confirmed it stopped serving it yet",
    "ROUTE_REMOVAL_CONFIRMED": "A node applied a configuration without this route, so it is no longer served",
    "NGINX_DRIFT_DETECTED": "Node configuration drifted from the desired bundle",
    "NGINX_DRIFT_RECOVERED": "Node configuration was re-applied after drift",
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
