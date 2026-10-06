"""Monitor dispatch: claim due monitors atomically, run their checks."""

from __future__ import annotations

import uuid

from app.core.logging import get_logger
from app.models import Monitor
from app.tasks._util import org_for, org_session, run_async, sweep_session
from app.tasks.celery_app import app

logger = get_logger(__name__)

CLAIM_BATCH = 50


@app.task(name="nx.run_due_monitors", soft_time_limit=300, time_limit=330)
def run_due_monitors() -> dict[str, int]:
    """Claim up to CLAIM_BATCH due monitors and execute each check.

    ``claim_due_monitors`` uses FOR UPDATE SKIP LOCKED, so overlapping ticks or
    extra workers simply partition the batch instead of double-checking.
    """

    async def _run() -> int:
        from app.services import monitor_service

        # Due monitors span every tenant, so the claim runs under the system
        # scope — and each check then runs inside the organization that owns the
        # monitor, because a check writes results, incidents and events for it.
        async with sweep_session("task.run_due_monitors.claim") as db:
            monitor_ids: list[uuid.UUID] = await monitor_service.claim_due_monitors(
                db, limit=CLAIM_BATCH
            )

        ran = 0
        for mid in monitor_ids:
            org_id = await org_for(Monitor, mid)
            if org_id is None:
                continue
            # A fresh short transaction per check keeps one slow endpoint from
            # holding locks over the whole batch.
            async with org_session(org_id) as db:
                outcome = await monitor_service.run_check(db, mid)
            if outcome is not None:
                ran += 1
        return ran

    executed = run_async(_run())
    if executed:
        logger.info("monitor_checks_executed", count=executed)
    return {"executed": executed}
