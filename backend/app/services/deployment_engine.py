"""Deployment engine: queueing, execution, cancellation and rollback.

``execute_deployment`` runs in its OWN database session (worker context) and
never holds a row lock while streaming output: it claims the QUEUED row with
``SELECT ... FOR UPDATE``, commits, then polls ``cancel_requested`` between
steps so a cancel request from the API is never blocked.

Cross-module integrations (task queue, log persistence, secret resolution,
alerting) are late-imported inside functions because those modules live in
sibling domains owned by other services.
"""

from __future__ import annotations

import asyncio
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import orjson
from sqlalchemy import event as sa_event
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import AuthContext
from app.core.channels import deployment_log_channel
from app.core.db import get_sessionmaker
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.core.logging import get_logger
from app.core.redis_client import get_redis
from app.models import (
    Alert,
    Application,
    Deployment,
    DeploymentEnvironment,
    DeploymentStep,
    LogEntry,
    Project,
    Server,
)
from app.models.enums import (
    ActorType,
    AlertSeverity,
    DeploymentStatus,
    DeploymentTrigger,
    EventLevel,
    LogSource,
    StepStatus,
)
from app.providers.base import LogLine
from app.providers.deployment_runner import (
    RunContext,
    SimulatedDeploymentRunner,
    StepFailure,
    StepLine,
)
from app.services import audit_service, event_bus
from app.services.project_service import actor_of

log = get_logger("nexusops.deployments")

VERSION_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
FLUSH_EVERY = 20
OUTPUT_CAP_BYTES = 60 * 1024
TERMINAL_STATUSES = frozenset(
    {DeploymentStatus.SUCCESS, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED}
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _validate_version(version: str) -> None:
    if not 1 <= len(version) <= 160 or not VERSION_RE.fullmatch(version):
        raise UnprocessableEntity(
            "Version must be 1-160 chars of letters, digits, dot, underscore, slash or dash",
            code="INVALID_VERSION",
        )


def _sanitize_reason(text: str) -> str:
    return " ".join(str(text).split())[:480]


async def _enqueue_task(deployment_id: uuid.UUID) -> None:
    """Hand the deployment to Celery; broker downtime is tolerated (beat sweeps)."""
    try:
        from app.tasks import deployments as deployment_tasks

        task = getattr(deployment_tasks, "run_deployment_task", None) or getattr(
            deployment_tasks, "run_deployment", None
        )
        if task is None:
            raise AttributeError("no deployment task registered in app.tasks.deployments")
        task.delay(str(deployment_id))
    except Exception as exc:
        log.warning(
            "deployment_enqueue_failed",
            deployment_id=str(deployment_id),
            error=str(exc),
        )


_background_enqueues: set[asyncio.Task[None]] = set()


def _after_commit_enqueue(session: Any) -> None:
    ids = session.info.pop("_deployment_enqueues_pending", [])
    if not ids:
        return
    loop = asyncio.get_running_loop()
    for deployment_id in ids:
        task = loop.create_task(_enqueue_task(deployment_id))
        _background_enqueues.add(task)
        task.add_done_callback(_background_enqueues.discard)


def _after_rollback_drop(session: Any) -> None:
    """Drop stashed ids on rollback — otherwise a LATER, unrelated commit on
    the same session would enqueue a deployment whose row never existed.
    (No stash point runs inside a savepoint, so the outer event suffices.)
    """
    session.info.pop("_deployment_enqueues_pending", None)


def _enqueue_after_commit(db: AsyncSession, deployment_id: uuid.UUID) -> None:
    """Defer the Celery handoff until the QUEUED row is actually committed.

    Enqueueing inline raced the worker: its claim query filters on
    ``status == QUEUED`` and ran against a row the API transaction had not
    committed yet, so the task no-op'd in ~4ms and the deployment sat QUEUED
    until the 5-minute sweep rescued it — far past any interactive timeout.
    Same after-commit pattern as the event bus publish path.
    """
    sync = db.sync_session
    pending: list[uuid.UUID] = sync.info.setdefault("_deployment_enqueues_pending", [])
    pending.append(deployment_id)
    if not sync.info.get("_deployment_enqueue_hook_installed"):
        sync.info["_deployment_enqueue_hook_installed"] = True
        sa_event.listen(sync, "after_commit", _after_commit_enqueue)
        sa_event.listen(sync, "after_rollback", _after_rollback_drop)


# --- Queue --------------------------------------------------------------------


async def queue_deployment(
    db: AsyncSession,
    *,
    ctx: AuthContext | None,
    application: Application,
    environment: DeploymentEnvironment,
    version: str,
    git_commit: str = "",
    notes: str = "",
    trigger: DeploymentTrigger = DeploymentTrigger.MANUAL,
    is_rollback: bool = False,
    rollback_of: Deployment | None = None,
    enqueue: bool = True,
    request: Any = None,
) -> Deployment:
    """Create QUEUED deployment + PENDING steps; race-safe per-application number."""
    _validate_version(version)
    if environment.application_id != application.id:
        raise NotFound("Environment does not belong to this application")

    await db.execute(
        select(Application.id).where(Application.id == application.id).with_for_update()
    )
    next_number = (
        int(
            await db.scalar(
                select(func.coalesce(func.max(Deployment.number), 0)).where(
                    Deployment.application_id == application.id
                )
            )
        )
        + 1
    )

    project_name = ""
    if application.project_id:
        project_name = getattr(await db.get(Project, application.project_id), "name", "")
    run_ctx = RunContext(
        project_name=project_name,
        application_name=application.name,
        environment_name=environment.name,
        version=version,
        git_commit=git_commit,
    )
    runner = SimulatedDeploymentRunner()

    deployment = Deployment(
        number=next_number,
        application_id=application.id,
        environment_id=environment.id,
        version=version,
        git_commit=(git_commit or "")[:80],
        notes=notes or "",
        status=DeploymentStatus.QUEUED,
        trigger=trigger,
        triggered_by_id=ctx.user_id if ctx else None,
        is_rollback=is_rollback,
        rollback_of_id=rollback_of.id if rollback_of else None,
        queued_at=_utcnow(),
    )
    db.add(deployment)
    await db.flush()
    for idx, name in enumerate(runner.plan_steps(run_ctx)):
        db.add(DeploymentStep(deployment_id=deployment.id, idx=idx, name=name))
    await db.flush()

    actor_id, actor_type = actor_of(ctx)
    data: dict[str, Any] = {
        "number": next_number,
        "version": version,
        "trigger": trigger.value,
        "is_rollback": is_rollback,
        "environment": environment.name,
    }
    if rollback_of is not None:
        data["rollback_of_number"] = rollback_of.number
    await event_bus.publish(
        db,
        type="DEPLOYMENT_QUEUED",
        message=f"Deployment #{next_number} of {application.name} queued for {environment.name}",
        level=EventLevel.INFO,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="deployment",
        resource_id=str(deployment.id),
        data=data,
    )
    await audit_service.record(
        db,
        ctx,
        action="deployment.queue",
        resource_type="deployment",
        resource_id=deployment.id,
        metadata={
            "number": next_number,
            "version": version,
            "is_rollback": is_rollback,
            "trigger": trigger.value,
        },
        request=request,
    )
    if enqueue:
        _enqueue_after_commit(db, deployment.id)
    log.info(
        "deployment_queued",
        deployment_id=str(deployment.id),
        application=application.name,
        version=version,
        is_rollback=is_rollback,
    )
    return deployment


# --- Execution ------------------------------------------------------------------


async def execute_deployment(deployment_id: uuid.UUID) -> None:
    """Run one deployment to a terminal state. Never raises; safe to re-run."""
    factory = get_sessionmaker()
    async with factory() as db:
        try:
            await _run(db, factory, deployment_id)
        except Exception as exc:
            log.error("deployment_executor_error", deployment_id=str(deployment_id), exc_info=True)
            await _fail_from_exception(factory, deployment_id, exc)


async def _run(db: AsyncSession, factory: Any, deployment_id: uuid.UUID) -> None:
    claimed = (
        await db.execute(
            select(Deployment)
            .where(Deployment.id == deployment_id, Deployment.status == DeploymentStatus.QUEUED)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if claimed is None:
        # Not committed yet (enqueue raced the commit — must not happen since
        # the after-commit deferral), already running, or already finished.
        exists = await db.get(Deployment, deployment_id)
        if exists is None:
            log.warning("deployment_claim_missed_row_absent", deployment_id=str(deployment_id))
        else:
            log.info(
                "deployment_claim_skipped",
                deployment_id=str(deployment_id),
                status=exists.status.value,
            )
        return

    application = await db.get(Application, claimed.application_id)
    environment = await db.get(DeploymentEnvironment, claimed.environment_id)
    if application is None or environment is None:
        claimed.status = DeploymentStatus.FAILED
        claimed.failure_reason = "Application or environment vanished"
        claimed.finished_at = _utcnow()
        await db.commit()
        return

    claimed.status = DeploymentStatus.RUNNING
    claimed.started_at = _utcnow()
    await event_bus.publish(
        db,
        type="DEPLOYMENT_STARTED",
        message=f"Deployment #{claimed.number} of {application.name} started",
        resource_type="deployment",
        resource_id=str(claimed.id),
        data={"version": claimed.version, "is_rollback": claimed.is_rollback},
    )
    await db.commit()  # release the row lock before any slow work

    server_name = await _server_name(db, environment.server_id)
    run_ctx = RunContext(
        project_name=getattr(await db.get(Project, application.project_id), "name", ""),
        application_name=application.name,
        environment_name=environment.name,
        version=claimed.version,
        git_commit=claimed.git_commit,
        server_name=server_name,
        secrets=await _resolve_secrets(db, environment),
    )
    steps = list(
        (
            await db.execute(
                select(DeploymentStep)
                .where(DeploymentStep.deployment_id == claimed.id)
                .order_by(DeploymentStep.idx)
            )
        )
        .scalars()
        .all()
    )

    cancelled = False
    failure_step: DeploymentStep | None = None
    failure_error = ""
    runner = SimulatedDeploymentRunner()
    for step in steps:
        if await _cancel_requested(db, claimed.id):
            cancelled = True
            break
        step.status = StepStatus.RUNNING
        step.started_at = _utcnow()
        await db.commit()
        try:
            await _stream_step(db, claimed, step, runner, run_ctx)
        except StepFailure as exc:
            failure_step, failure_error = step, str(exc)
            break

    if failure_step is not None:
        await _finalize_failed(db, claimed, failure_step, failure_error, application)
    elif cancelled:
        await _finalize_cancelled(db, claimed, steps)
    else:
        await _finalize_success(db, claimed, steps, application)


async def _server_name(db: AsyncSession, server_id: uuid.UUID | None) -> str | None:
    if server_id is None:
        return None
    server = await db.get(Server, server_id)
    return server.name if server else None


async def _resolve_secrets(db: AsyncSession, environment: DeploymentEnvironment) -> dict[str, str]:
    """Resolve config references via the secrets domain; failures degrade to {}."""
    try:
        from app.services import secret_service

        resolved = await secret_service.resolve_secrets_for_environment(db, environment)
        return {str(key): str(value) for key, value in dict(resolved).items()}
    except Exception as exc:
        log.warning(
            "deployment_secret_resolution_failed",
            environment_id=str(environment.id),
            error=str(exc),
        )
        return {}


async def _cancel_requested(db: AsyncSession, deployment_id: uuid.UUID) -> bool:
    value = await db.scalar(
        select(Deployment.cancel_requested).where(Deployment.id == deployment_id)
    )
    return bool(value)


async def _stream_step(
    db: AsyncSession,
    deployment: Deployment,
    step: DeploymentStep,
    runner: SimulatedDeploymentRunner,
    run_ctx: RunContext,
) -> None:
    """Stream one step's lines into output/log rows/Redis frames, then commit."""
    buffer: list[StepLine] = []
    try:
        async for line in runner.execute_step(step.name, run_ctx):
            buffer.append(line)
            if len(buffer) >= FLUSH_EVERY:
                await _flush_buffer(db, deployment, step, buffer)
        step.status = StepStatus.SUCCESS
    except StepFailure:
        step.status = StepStatus.FAILED
        raise
    finally:
        if buffer:
            await _flush_buffer(db, deployment, step, buffer)
        step.finished_at = _utcnow()
        await db.commit()


async def _flush_buffer(
    db: AsyncSession, deployment: Deployment, step: DeploymentStep, buffer: list[StepLine]
) -> None:
    """Persist + broadcast buffered lines, appending to capped step output."""
    lines = list(buffer)
    buffer.clear()
    ts = _utcnow()
    await _persist_log_lines(db, deployment.id, lines, ts)
    current = step.output or ""
    for item in lines:
        current += ("\n" if current else "") + item.line
    step.output = current.encode("utf-8")[:OUTPUT_CAP_BYTES].decode("utf-8", "ignore")
    frames = [
        {
            "deployment_id": str(deployment.id),
            "step_idx": step.idx,
            "step": step.name,
            "line": item.line,
            "level": item.level.value,
            "ts": ts.isoformat(),
        }
        for item in lines
    ]
    await _publish_frames(frames)
    await db.commit()


async def _persist_log_lines(
    db: AsyncSession, deployment_id: uuid.UUID, lines: list[StepLine], ts: datetime
) -> None:
    """Write LogEntry rows via log_service.append_lines, falling back to direct inserts."""
    if not lines:
        return
    log_lines = [LogLine(ts=ts, stream="stdout", message=item.line) for item in lines]
    try:
        from app.services import log_service

        await log_service.append_lines(
            db,
            source=LogSource.DEPLOYMENT,
            deployment_id=deployment_id,
            lines=log_lines,
        )
        return
    except Exception as exc:
        # Shared ingestion unavailable/unhappy — persist directly so no output is lost.
        log.warning("deployment_log_persist_fallback", error=str(exc))
        try:
            await db.rollback()  # drop any partial inserts from the failed call
        except Exception as rb_exc:  # pragma: no cover - never mask the fallback
            log.debug("deployment_rollback_failed", error=str(rb_exc))
    db.add_all(
        LogEntry(
            source=LogSource.DEPLOYMENT,
            deployment_id=deployment_id,
            stream="stdout",
            level=item.level,
            message=item.line,
            ts=ts,
        )
        for item in lines
    )
    await db.flush()


async def _publish_frames(frames: list[dict[str, Any]]) -> None:
    if not frames:
        return
    channel = deployment_log_channel(str(frames[0]["deployment_id"]))
    try:
        redis = get_redis()
        pipe = redis.pipeline(transaction=False)
        for frame in frames:
            pipe.publish(channel, orjson.dumps(frame).decode())
        await pipe.execute()
    except Exception as exc:
        log.warning("deployment_frame_publish_failed", error=str(exc))


# --- Terminal transitions -------------------------------------------------------


def _finish(deployment: Deployment, status: DeploymentStatus, now: datetime) -> None:
    deployment.status = status
    deployment.finished_at = now
    if deployment.started_at is not None:
        deployment.duration_ms = int((now - deployment.started_at).total_seconds() * 1000)


async def _emit(
    db: AsyncSession,
    *,
    type: str,
    level: EventLevel,
    message: str,
    deployment: Deployment,
    data: dict[str, Any],
) -> None:
    await event_bus.publish(
        db,
        type=type,
        level=level,
        message=message[:500],
        resource_type="deployment",
        resource_id=str(deployment.id),
        data=data,
        actor_type=ActorType.SYSTEM,
    )


async def _notify_alert(
    db: AsyncSession,
    *,
    severity: AlertSeverity,
    event_type: str,
    title: str,
    body: str,
    deployment: Deployment,
) -> None:
    """Best-effort alert creation through the observability domain."""
    try:
        from app.services import alert_service

        await alert_service.create_alert(
            db,
            event_type=event_type,
            severity=severity,
            title=title,
            body=body,
            source="deployment-engine",
            resource_type="deployment",
            resource_id=str(deployment.id),
        )
        return
    except Exception as exc:
        log.warning("deployment_alert_fallback", error=str(exc))
        try:
            await db.rollback()  # drop any partial inserts from the failed call
        except Exception as rb_exc:  # pragma: no cover - never mask the fallback
            log.debug("deployment_rollback_failed", error=str(rb_exc))
    try:
        db.add(
            Alert(
                severity=severity,
                title=title[:240],
                body=body[:4000],
                event_type=event_type[:64],
                source="deployment-engine",
                resource_type="deployment",
                resource_id=str(deployment.id),
            )
        )
        await db.flush()
    except Exception:  # pragma: no cover - alerting must never block flow
        await db.rollback()
        log.warning("deployment_alert_persist_failed", exc_info=True)


async def _finalize_success(
    db: AsyncSession,
    deployment: Deployment,
    steps: list[DeploymentStep],
    application: Application,
) -> None:
    now = _utcnow()
    for step in steps:
        step.status = StepStatus.SUCCESS
    _finish(deployment, DeploymentStatus.SUCCESS, now)
    application.current_version = deployment.version
    application.current_deployment_id = deployment.id
    await _emit(
        db,
        type="DEPLOYMENT_SUCCEEDED",
        level=EventLevel.INFO,
        message=(
            f"Deployment #{deployment.number} of {application.name} succeeded "
            f"({deployment.version})"
        ),
        deployment=deployment,
        data={"version": deployment.version, "duration_ms": deployment.duration_ms},
    )
    await _notify_alert(
        db,
        severity=AlertSeverity.INFO,
        event_type="DEPLOYMENT_SUCCEEDED",
        title=f"Deployment #{deployment.number} of {application.name} succeeded",
        body=f"{application.name} now runs {deployment.version}",
        deployment=deployment,
    )
    await db.commit()
    log.info("deployment_succeeded", deployment_id=str(deployment.id))


async def _finalize_failed(
    db: AsyncSession,
    deployment: Deployment,
    step: DeploymentStep,
    error: str,
    application: Application,
) -> None:
    now = _utcnow()
    step.error = error[:2000]
    # Unreached steps: mirror the cancel path's vocabulary — anything not yet
    # run is SKIPPED, so a terminal deployment never shows live PENDING steps.
    remaining = (
        (
            await db.execute(
                select(DeploymentStep).where(DeploymentStep.deployment_id == deployment.id)
            )
        )
        .scalars()
        .all()
    )
    for pending in remaining:
        if pending.id != step.id and pending.status in (
            StepStatus.PENDING,
            StepStatus.RUNNING,
        ):
            pending.status = StepStatus.SKIPPED
    _finish(deployment, DeploymentStatus.FAILED, now)
    deployment.failure_reason = _sanitize_reason(f"Step {step.name} failed: {error}")
    await _emit(
        db,
        type="DEPLOYMENT_FAILED",
        level=EventLevel.ERROR,
        message=f"Deployment #{deployment.number} of {application.name} failed at {step.name}",
        deployment=deployment,
        data={
            "version": deployment.version,
            "step": step.name,
            "reason": deployment.failure_reason,
            "is_rollback": deployment.is_rollback,
        },
    )
    await _notify_alert(
        db,
        severity=AlertSeverity.CRITICAL,
        event_type="DEPLOYMENT_FAILED",
        title=f"Deployment #{deployment.number} of {application.name} failed",
        body=deployment.failure_reason,
        deployment=deployment,
    )
    await db.commit()
    log.warning(
        "deployment_failed", deployment_id=str(deployment.id), reason=deployment.failure_reason
    )


async def _finalize_cancelled(
    db: AsyncSession, deployment: Deployment, steps: list[DeploymentStep]
) -> None:
    now = _utcnow()
    for step in steps:
        if step.status in (StepStatus.PENDING, StepStatus.RUNNING):
            step.status = StepStatus.SKIPPED
    _finish(deployment, DeploymentStatus.CANCELLED, now)
    await event_bus.publish(
        db,
        type="DEPLOYMENT_CANCELLED",
        message=f"Deployment #{deployment.number} was cancelled",
        level=EventLevel.WARNING,
        resource_type="deployment",
        resource_id=str(deployment.id),
        data={"version": deployment.version, "is_rollback": deployment.is_rollback},
    )
    await db.commit()
    log.info("deployment_cancelled", deployment_id=str(deployment.id))


async def _fail_from_exception(factory: Any, deployment_id: uuid.UUID, exc: Exception) -> None:
    """Last-resort FAILED marking in a fresh session; never raises."""
    try:
        async with factory() as db:
            row = (
                await db.execute(
                    select(Deployment)
                    .where(
                        Deployment.id == deployment_id,
                        Deployment.status.in_((DeploymentStatus.QUEUED, DeploymentStatus.RUNNING)),
                    )
                    .with_for_update()
                )
            ).scalar_one_or_none()
            if row is None:
                return
            _finish(row, DeploymentStatus.FAILED, _utcnow())
            row.failure_reason = _sanitize_reason(f"{type(exc).__name__}: {exc}")
            await db.commit()
    except Exception:  # pragma: no cover - nothing left to do but log
        log.error(
            "deployment_failover_mark_failed", deployment_id=str(deployment_id), exc_info=True
        )


# --- Cancel & rollback ------------------------------------------------------------


async def cancel_deployment(
    db: AsyncSession,
    ctx: AuthContext | None,
    deployment_id: uuid.UUID,
    *,
    request: Any = None,
) -> Deployment:
    """Cancel immediately when QUEUED; flag cooperative cancel when RUNNING."""
    deployment = (
        await db.execute(select(Deployment).where(Deployment.id == deployment_id).with_for_update())
    ).scalar_one_or_none()
    if deployment is None:
        raise NotFound("Deployment not found")
    if deployment.status in TERMINAL_STATUSES:
        raise Conflict("Deployment already finished", code="ALREADY_FINISHED")

    if deployment.status == DeploymentStatus.RUNNING:
        deployment.cancel_requested = True
        await audit_service.record(
            db,
            ctx,
            action="deployment.cancel",
            resource_type="deployment",
            resource_id=deployment.id,
            metadata={"mode": "requested", "number": deployment.number},
            request=request,
        )
        await db.flush()
        return deployment

    now = _utcnow()
    steps = (
        (
            await db.execute(
                select(DeploymentStep).where(DeploymentStep.deployment_id == deployment.id)
            )
        )
        .scalars()
        .all()
    )
    for step in steps:
        if step.status in (StepStatus.PENDING, StepStatus.RUNNING):
            step.status = StepStatus.SKIPPED
    _finish(deployment, DeploymentStatus.CANCELLED, now)
    actor_id, actor_type = actor_of(ctx)
    await event_bus.publish(
        db,
        type="DEPLOYMENT_CANCELLED",
        message=f"Deployment #{deployment.number} was cancelled before starting",
        level=EventLevel.WARNING,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="deployment",
        resource_id=str(deployment.id),
        data={"version": deployment.version, "is_rollback": deployment.is_rollback},
    )
    await audit_service.record(
        db,
        ctx,
        action="deployment.cancel",
        resource_type="deployment",
        resource_id=deployment.id,
        metadata={"mode": "immediate", "number": deployment.number},
        request=request,
    )
    await db.flush()
    return deployment


async def rollback_deployment(
    db: AsyncSession,
    ctx: AuthContext | None,
    deployment_id: uuid.UUID,
    *,
    request: Any = None,
) -> Deployment:
    """Queue a ROLLBACK deployment restoring the last good version."""
    original = await db.get(Deployment, deployment_id)
    if original is None:
        raise NotFound("Deployment not found")
    if original.status not in (DeploymentStatus.SUCCESS, DeploymentStatus.FAILED):
        raise Conflict(
            "Only successful or failed deployments can be rolled back", code="NOT_ROLLBACKABLE"
        )
    target = (
        await db.execute(
            select(Deployment)
            .where(
                Deployment.application_id == original.application_id,
                Deployment.environment_id == original.environment_id,
                Deployment.is_rollback.is_(False),
                Deployment.id != original.id,
                Deployment.status == DeploymentStatus.SUCCESS,
            )
            .order_by(Deployment.finished_at.desc().nulls_last(), Deployment.number.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if target is None:
        raise Conflict("No prior successful deployment to roll back to", code="NO_ROLLBACK_TARGET")

    application = await db.get(Application, original.application_id)
    environment = await db.get(DeploymentEnvironment, original.environment_id)
    if application is None or environment is None:
        raise NotFound("Deployment parent records are missing")
    new_deployment = await queue_deployment(
        db,
        ctx=ctx,
        application=application,
        environment=environment,
        version=target.version,
        git_commit=target.git_commit,
        notes=f"Rollback of #{original.number} to {target.version}",
        trigger=DeploymentTrigger.ROLLBACK,
        is_rollback=True,
        rollback_of=original,
        request=request,
    )
    await audit_service.record(
        db,
        ctx,
        action="deployment.rollback",
        resource_type="deployment",
        resource_id=new_deployment.id,
        metadata={
            "original_number": original.number,
            "target_number": target.number,
            "target_version": target.version,
        },
        request=request,
    )
    return new_deployment


# --- Shared getters ----------------------------------------------------------------


async def get_deployment(db: AsyncSession, deployment_id: uuid.UUID) -> Deployment:
    """Load a deployment with application/environment/steps eager-loaded."""
    deployment = (
        await db.execute(
            select(Deployment)
            .where(Deployment.id == deployment_id)
            .options(
                selectinload(Deployment.application),
                selectinload(Deployment.environment),
            )
        )
    ).scalar_one_or_none()
    if deployment is None:
        raise NotFound("Deployment not found")
    return deployment
