"""Heartbeat sweeps: offline detection and recovery for servers."""

from __future__ import annotations

from app.core.logging import get_logger
from app.tasks._util import run_async, task_session
from app.tasks.celery_app import app

logger = get_logger(__name__)


@app.task(name="nx.sweep_servers", soft_time_limit=60, time_limit=90)
def sweep_servers() -> dict[str, int]:
    """Flag silent servers OFFLINE, recover returning ones. Safe to overlap."""

    async def _run() -> list[dict[str, str]]:
        from app.services import server_service

        async with task_session() as db:
            return await server_service.mark_stale_servers(db)

    transitions = run_async(_run())
    counts: dict[str, int] = {}
    for server_name, new_status in transitions:
        counts[new_status] = counts.get(new_status, 0) + 1
        logger.info("server_status_transition", server=server_name, status=new_status)
    if transitions:
        logger.info("sweep_servers_done", transitions=len(transitions), **counts)
    return {"transitions": len(transitions), **counts}
