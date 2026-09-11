"""Canonical Redis pub/sub channel names shared by API, workers and WS hub."""

from __future__ import annotations

CHANNEL_EVENTS = "nx:events"


def container_log_channel(container_id: str) -> str:
    return f"nx:logs:{container_id}"


def deployment_log_channel(deployment_id: str) -> str:
    return f"nx:deploy:{deployment_id}"


def server_metrics_channel(server_id: str) -> str:
    return f"nx:metrics:{server_id}"


WS_CHANNEL_GLOBAL = "global"
WS_CHANNEL_SERVER_METRICS = "server-metrics"
WS_CHANNEL_CONTAINER_LOGS = "container-logs"
WS_CHANNEL_DEPLOYMENT_LOGS = "deployment-logs"
WS_CHANNEL_INCIDENTS = "incidents"
