"""Celery application: periodic cadences live here, dynamic work is claimed atomically.

Beat schedules fixed ticks only; every task that processes "due" rows claims them
with ``FOR UPDATE SKIP LOCKED`` so multiple workers never double-process.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

app = Celery(
    "nexusops",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.heartbeat",
        "app.tasks.monitoring",
        "app.tasks.deployments",
        "app.tasks.domain_routing",
        "app.tasks.maintenance",
        "app.tasks.simulation",
    ],
)

app.conf.update(
    task_default_queue="nx",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Periodic sweeps are cheap and idempotent; early-ack keeps Redis visibility
    # semantics simple (late-ack + redis can re-run tasks after visibility timeouts).
    task_acks_late=False,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=540,
    task_time_limit=600,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)

# Fixed cadences. Simulation tick self-disables unless SIMULATION_MODE=true.
app.conf.beat_schedule = {
    "sweep-server-heartbeats": {
        "task": "nx.sweep_servers",
        "schedule": 15.0,
        "options": {"expires": 10},
    },
    "run-due-monitors": {
        "task": "nx.run_due_monitors",
        "schedule": settings.monitor_dispatch_interval_seconds,
        "options": {"expires": settings.monitor_dispatch_interval_seconds - 2},
    },
    "sync-docker-hosts": {
        "task": "nx.sync_docker_hosts",
        "schedule": 30.0,
        "options": {"expires": 25},
    },
    "sweep-deployments": {
        "task": "nx.sweep_deployments",
        "schedule": 120.0,
        "options": {"expires": 100},
    },
    "retry-notifications": {
        "task": "nx.retry_notifications",
        "schedule": 60.0,
        "options": {"expires": 50},
    },
    "expire-sessions": {
        "task": "nx.expire_sessions",
        "schedule": 600.0,
        "options": {"expires": 500},
    },
    # Operations expire on a short cadence: the shortest per-type timeout is 30s,
    # so a minute keeps `expired` meaningful rather than a formality.
    "expire-operations": {
        "task": "nx.expire_operations",
        "schedule": 60.0,
        "options": {"expires": 50},
    },
    # Domains are re-proved on a cadence; each row also carries its own
    # ``next_check_at`` (grace/backoff), so a shorter dispatch tick only makes the
    # due row happen sooner — it never shortens the proof policy itself.
    "sweep-domains": {
        "task": "nx.sweep_domains",
        "schedule": settings.domain_sweep_interval_seconds,
        "options": {"expires": settings.domain_sweep_interval_seconds - 10},
    },
    # Desired-state reconciliation: ask nodes for their live fingerprint and
    # re-apply where the control plane's bundle is not the one the node has.
    "sweep-routes": {
        "task": "nx.sweep_routes",
        "schedule": settings.route_sweep_interval_seconds,
        "options": {"expires": settings.route_sweep_interval_seconds - 5},
    },
    "aggregate-metrics": {
        "task": "nx.aggregate_metrics",
        "schedule": settings.metrics_aggregation_interval_seconds,
        "options": {"expires": settings.metrics_aggregation_interval_seconds - 5},
    },
    "trim-logs": {
        "task": "nx.trim_logs",
        "schedule": crontab(minute="*/15"),
        "options": {"expires": 600},
    },
    "simulation-tick": {
        "task": "nx.simulation_tick",
        "schedule": 20.0,
        "options": {"expires": 15},
    },
}
