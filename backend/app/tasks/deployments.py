"""Deployment execution task + stuck-deployment sweeper."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import select

from app.core.logging import get_logger
from app.core.tenancy import org_scope
from app.tasks._util import org_for, run_async, sweep_session
from app.tasks.celery_app import app

logger = get_logger(__name__)

STUCK_QUEUED_AFTER = timedelta(minutes=5)
STUCK_RUNNING_AFTER = timedelta(minutes=30)


@app.task(name="nx.run_deployment", soft_time_limit=560, time_limit=590)
def run_deployment(deployment_id: str) -> dict[str, str]:
    """Execute one queued deployment. The engine owns all state transitions."""

    async def _run() -> None:
        from app.models import Deployment
        from app.services.deployment_engine import execute_deployment

        # Resolve the owning organization first, then run the whole deployment
        # inside it: the engine writes steps, logs and events for that tenant,
        # and a worker has no ambient organization to inherit. The scope wraps
        # the call rather than a session because the engine opens several
        # sessions of its own — each new transaction picks the scope up.
        org_id = await org_for(Deployment, deployment_id)
        if org_id is None:
            logger.warning("deployment_org_unresolved", deployment_id=deployment_id)
            return
        with org_scope(org_id):
            # Celery delivers the id as a str; the engine's UUID-keyed queries
            # accept it via driver-side coercion.
            await execute_deployment(cast(uuid.UUID, deployment_id))

    run_async(_run())
    logger.info("deployment_task_finished", deployment_id=deployment_id)
    return {"deployment_id": deployment_id, "status": "processed"}


@app.task(name="nx.sweep_deployments", soft_time_limit=120, time_limit=150)
def sweep_deployments() -> dict[str, int]:
    """Re-enqueue deployments the broker lost; fail ones whose worker died.

    ``execute_deployment`` re-checks status QUEUED under a row lock, so a
    re-enqueued deployment that actually started is never double-executed.
    """

    async def _run() -> dict[str, int]:
        from app.models import Deployment
        from app.models.enums import DeploymentStatus, EventLevel
        from app.services import event_bus

        counts = {"requeued": 0, "failed": 0}
        now = datetime.now(UTC)

        # Stuck deployments exist in every tenant, so the sweep is cross-tenant;
        # everything it writes is attributed to the deployment's own org.
        async with sweep_session("task.sweep_deployments") as db:
            stuck_queued = (
                (
                    await db.execute(
                        select(Deployment).where(
                            Deployment.status == DeploymentStatus.QUEUED,
                            Deployment.queued_at < now - STUCK_QUEUED_AFTER,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for dep in stuck_queued:
                try:
                    run_deployment.delay(str(dep.id))
                    dep.queued_at = now  # push the next sweep window out
                    counts["requeued"] += 1
                    logger.warning("deployment_requeued", deployment_id=str(dep.id))
                except Exception:
                    # Broker still down; leave for the next sweep.
                    break
            await db.flush()

            lost = (
                (
                    await db.execute(
                        select(Deployment).where(
                            Deployment.status == DeploymentStatus.RUNNING,
                            Deployment.started_at < now - STUCK_RUNNING_AFTER,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for dep in lost:
                dep.status = DeploymentStatus.FAILED
                dep.failure_reason = "worker stopped responding (sweeper)"
                dep.finished_at = now
                counts["failed"] += 1
                logger.error("deployment_marked_lost", deployment_id=str(dep.id))
                await event_bus.publish(
                    db,
                    type="DEPLOYMENT_FAILED",
                    message=f"Deployment #{dep.number} marked failed: worker lost",
                    level=EventLevel.ERROR,
                    resource_type="deployment",
                    resource_id=str(dep.id),
                    # No ambient org inside a sweep: the event belongs to the
                    # deployment's tenant, and publishing it to the wrong one
                    # would notify the wrong people.
                    org_id=dep.org_id,
                )

        return counts

    return run_async(_run())
