"""Housekeeping: metric rollups, log trims, notification retries, session expiry."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import Table, delete, select

from app.core.logging import get_logger
from app.tasks._util import org_for, org_session, run_async, sweep_session
from app.tasks.celery_app import app

logger = get_logger(__name__)

LOG_RETENTION = {
    "CONTAINER": timedelta(days=3),
    "DEPLOYMENT": timedelta(days=30),
    "SERVER": timedelta(days=7),
}
CONTAINER_LOG_CAP = 5000
#: Running containers pulled per sweep. Docker timestamps make re-collection
#: incremental (only lines newer than the newest stored row are kept), so this
#: can cover a whole host rather than the first handful alphabetically.
LOG_COLLECT_MAX_CONTAINERS = 25


@app.task(name="nx.aggregate_metrics", soft_time_limit=240, time_limit=280)
def aggregate_metrics() -> dict[str, int]:
    async def _run() -> dict[str, int]:
        from app.services.metrics_service import aggregate_rollups

        # Cross-tenant by construction: rollups are partitioned by org_id inside
        # the statement itself.
        async with sweep_session("task.aggregate_metrics") as db:
            return await aggregate_rollups(db)

    counts = run_async(_run())
    if any(counts.values()):
        logger.info("metric_rollups_done", **counts)
    return counts


@app.task(name="nx.trim_logs", soft_time_limit=240, time_limit=280)
def trim_logs() -> dict[str, int]:
    """Time-based retention per source plus a per-container row cap."""

    async def _run() -> dict[str, int]:
        from sqlalchemy import func

        from app.models import LogEntry

        deleted_total: dict[str, int] = {}
        # Retention is a platform policy applied to every tenant's rows.
        async with sweep_session("task.trim_logs") as db:
            now = datetime.now(UTC)
            for source, retention in LOG_RETENTION.items():
                cutoff = now - retention
                result = await db.execute(
                    delete(LogEntry).where(LogEntry.source == source, LogEntry.ts < cutoff)
                )
                deleted_total[source] = result.rowcount or 0

            # Per-container cap: trim oldest rows beyond CONTAINER_LOG_CAP for any
            # container that exceeded it. Small set of candidates via grouped count.
            overfull = (
                await db.execute(
                    select(LogEntry.container_id, func.count().label("n"))
                    .where(
                        LogEntry.source == "CONTAINER",
                        LogEntry.container_id.is_not(None),
                    )
                    .group_by(LogEntry.container_id)
                    .having(func.count() > CONTAINER_LOG_CAP)
                )
            ).all()
            trimmed = 0
            for container_id, _count in overfull:
                subq = (
                    select(LogEntry.id)
                    .where(LogEntry.container_id == container_id)
                    .order_by(LogEntry.ts.desc(), LogEntry.id.desc())
                    .offset(CONTAINER_LOG_CAP)
                ).scalar_subquery()
                result = await db.execute(delete(LogEntry).where(LogEntry.id.in_(subq)))
                trimmed += result.rowcount or 0
            deleted_total["CAPPED"] = trimmed

        return deleted_total

    return run_async(_run())


@app.task(name="nx.retry_notifications", soft_time_limit=120, time_limit=150)
def retry_notifications() -> dict[str, int]:
    async def _run() -> int:
        from app.services.notification_service import retry_due_deliveries

        # retry_due_deliveries claims across tenants and re-enters each row's
        # own organization before sending.
        async with sweep_session("task.retry_notifications") as db:
            return await retry_due_deliveries(db, limit=50)

    retried = run_async(_run())
    if retried:
        logger.info("notification_retries_processed", count=retried)
    return {"retried": retried}


@app.task(name="nx.expire_sessions", soft_time_limit=120, time_limit=150)
def expire_sessions() -> dict[str, int]:
    """Revoke sessions past their expiry and purge dead refresh tokens."""

    async def _run() -> dict[str, int]:
        from app.models import RefreshToken, Session

        now = datetime.now(UTC)
        counts = {}
        # Sessions and tokens are credentials, not tenant data: every user's
        # expired session is swept in one pass.
        async with sweep_session("task.expire_sessions") as db:
            expired = (
                (
                    await db.execute(
                        select(Session.id).where(
                            Session.revoked_at.is_(None), Session.expires_at < now
                        )
                    )
                )
                .scalars()
                .all()
            )
            if expired:
                await db.execute(
                    cast(Table, Session.__table__)
                    .update()
                    .where(Session.id.in_(expired), Session.revoked_at.is_(None))
                    .values(revoked_at=now, revoked_reason="expired")
                )
            counts["sessions"] = len(expired)

            result = await db.execute(
                delete(RefreshToken).where(RefreshToken.expires_at < now - timedelta(days=7))
            )
            counts["refresh_tokens_purged"] = result.rowcount or 0

            result = await db.execute(
                delete(RefreshToken).where(
                    RefreshToken.superseded_by_id.is_not(None),
                    RefreshToken.expires_at < now - timedelta(days=1),
                )
            )
            counts["rotated_tokens_purged"] = result.rowcount or 0
        return counts

    return run_async(_run())


@app.task(name="nx.expire_operations", soft_time_limit=120, time_limit=150)
def expire_operations() -> dict[str, int]:
    """Expire node operations past their deadline — pending and claimed alike.

    A claimed op whose agent died mid-execution must not stay live forever, and
    the architecture's choice is to expire it rather than re-queue a possibly
    already-executed action (re-delivering a non-idempotent op is the worse
    failure). The claim itself is the only cross-tenant step; every transition
    and its audit row run inside the owning organization.
    """

    async def _run() -> dict[str, int]:
        from app.models import Operation
        from app.models.enums import OperationStatus
        from app.services import audit_service, operation_service

        now = datetime.now(UTC)
        # Claim across tenants; the answer is what defines each row's scope.
        async with sweep_session("task.expire_operations") as db:
            due = (
                await db.execute(
                    select(Operation.id, Operation.org_id)
                    .where(
                        Operation.status.in_(
                            (
                                OperationStatus.PENDING,
                                OperationStatus.CLAIMED,
                                OperationStatus.RUNNING,
                            )
                        ),
                        Operation.expires_at <= now,
                    )
                    .limit(500)
                )
            ).all()

        expired = 0
        for operation_id, org_id in due:
            # A fresh session per row: one session must never span two scopes.
            async with org_session(org_id) as db:
                if not await operation_service.expire_one(db, operation_id):
                    # A claimant won the race between the sweep and this row.
                    continue
                await audit_service.record(
                    db,
                    None,
                    action="operation.expire",
                    resource_type="operation",
                    resource_id=operation_id,
                    org_id=org_id,
                )
                expired += 1
        return {"expired": expired}

    counts = run_async(_run())
    if counts["expired"]:
        logger.info("operations_expired", count=counts["expired"])
    return counts


@app.task(name="nx.sync_docker_hosts", soft_time_limit=300, time_limit=330)
def sync_docker_hosts() -> dict[str, int]:
    """Reconcile every registered Docker host; pull recent logs from real ones."""

    async def _run() -> dict[str, int]:
        from app.models import DockerHost

        totals = {"hosts": 0, "errors": 0}
        # Hosts belong to every tenant; each one is then synced inside its own
        # organization (see _sync_one / _collect_logs).
        async with sweep_session("task.sync_docker_hosts") as db:
            hosts = (await db.execute(select(DockerHost))).scalars().all()

        for host in hosts:
            totals["hosts"] += 1
            try:
                # Awaited, not run_async: this whole loop already runs inside
                # the _run() coroutine, and asyncio.run() inside a running
                # loop raises immediately.
                summary = await _sync_one(host.id)
                containers_seen = summary.get("seen", 0) if isinstance(summary, dict) else 0
                if summary and summary.get("error"):
                    totals["errors"] += 1
                    logger.warning(
                        "docker_host_sync_degraded",
                        host=str(host.id),
                        error=str(summary.get("error"))[:200],
                    )
                else:
                    logger.debug("docker_host_synced", host=str(host.id), seen=containers_seen)
            except Exception as exc:  # one dead host never kills the sweep
                totals["errors"] += 1
                logger.warning("docker_host_sync_failed", host=str(host.id), error=str(exc)[:200])
                continue

            # Log ingestion only makes sense against real docker endpoints.
            if host.endpoint_url.startswith(("unix://", "tcp://")):
                try:
                    await _collect_logs(host.id)
                except Exception as exc:
                    logger.warning(
                        "docker_log_collect_failed", host=str(host.id), error=str(exc)[:200]
                    )
        return totals

    return run_async(_run())


async def _sync_one(host_id) -> dict:
    from app.models import DockerHost
    from app.services.container_service import sync_host_state

    org_id = await org_for(DockerHost, host_id)
    if org_id is None:
        return {}
    async with org_session(org_id) as db:
        return await sync_host_state(db, host_id)


async def _collect_logs(host_id) -> None:
    from app.models import DockerHost
    from app.services.container_service import collect_recent_logs

    org_id = await org_for(DockerHost, host_id)
    if org_id is None:
        return
    async with org_session(org_id) as db:
        host = await db.get(DockerHost, host_id)
        if host is not None:
            await collect_recent_logs(db, host, max_containers=LOG_COLLECT_MAX_CONTAINERS)
