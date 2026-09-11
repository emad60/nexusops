"""Deployment API schemas: requests, outputs, step and log items."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import DeploymentStatus, DeploymentTrigger, LogLevel, LogSource, StepStatus
from app.schemas.base import APIModel, OutModel

_VERSION_PATTERN = r"^[A-Za-z0-9._/-]+$"


class DeploymentCreate(APIModel):
    """Request body for triggering a deployment of an application."""

    environment_id: UUID
    version: str = Field(min_length=1, max_length=160, pattern=_VERSION_PATTERN)
    git_commit: str = Field(default="", max_length=80)
    notes: str = Field(default="", max_length=5000)


class LatestDeploymentSummary(APIModel):
    """Compact per-application deployment summary used in project detail."""

    number: int
    status: DeploymentStatus
    version: str
    finished_at: datetime | None = None


class DeploymentApplicationRef(APIModel):
    """Minimal application reference embedded in deployment outputs."""

    id: UUID
    name: str
    slug: str


class DeploymentEnvironmentRef(APIModel):
    """Minimal environment reference embedded in deployment outputs."""

    id: UUID
    name: str
    slug: str


class DeploymentStepOut(OutModel):
    """One pipeline step with its accumulated output."""

    idx: int
    name: str
    status: StepStatus
    output: str = ""
    error: str = ""
    retry_count: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None


class DeploymentOut(OutModel):
    """Deployment row plus denormalised references, actor email and step counts."""

    updated_at: datetime
    number: int
    application_id: UUID
    environment_id: UUID
    version: str
    git_commit: str
    notes: str
    status: DeploymentStatus
    trigger: DeploymentTrigger
    triggered_by_id: UUID | None = None
    triggered_by_email: str | None = None
    is_rollback: bool
    rollback_of_id: UUID | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    failure_reason: str = ""
    cancel_requested: bool = False

    application: DeploymentApplicationRef
    environment: DeploymentEnvironmentRef

    steps_total: int = 0
    steps_success: int = 0
    steps_failed: int = 0
    steps_running: int = 0
    steps_skipped: int = 0
    steps_cancelled: int = 0
    steps_pending: int = 0

    @classmethod
    def build(cls, dep: Any, triggered_by_email: str | None = None) -> DeploymentOut:
        """Serialize a deployment ORM row; ``dep.steps`` must be pre-loaded."""
        counts = Counter(step.status for step in dep.steps)
        return cls(
            id=dep.id,
            created_at=dep.created_at,
            updated_at=dep.updated_at,
            number=dep.number,
            application_id=dep.application_id,
            environment_id=dep.environment_id,
            version=dep.version,
            git_commit=dep.git_commit,
            notes=dep.notes,
            status=DeploymentStatus(dep.status),
            trigger=DeploymentTrigger(dep.trigger),
            triggered_by_id=dep.triggered_by_id,
            triggered_by_email=triggered_by_email,
            is_rollback=dep.is_rollback,
            rollback_of_id=dep.rollback_of_id,
            queued_at=dep.queued_at,
            started_at=dep.started_at,
            finished_at=dep.finished_at,
            duration_ms=dep.duration_ms,
            failure_reason=dep.failure_reason,
            cancel_requested=dep.cancel_requested,
            application=DeploymentApplicationRef.model_validate(dep.application),
            environment=DeploymentEnvironmentRef.model_validate(dep.environment),
            steps_total=len(dep.steps),
            steps_success=counts.get(StepStatus.SUCCESS, 0),
            steps_failed=counts.get(StepStatus.FAILED, 0),
            steps_running=counts.get(StepStatus.RUNNING, 0),
            steps_skipped=counts.get(StepStatus.SKIPPED, 0),
            steps_cancelled=counts.get(StepStatus.CANCELLED, 0),
            steps_pending=counts.get(StepStatus.PENDING, 0),
        )


class DeploymentDetail(DeploymentOut):
    """Deployment output including its ordered step list."""

    steps: list[DeploymentStepOut] = Field(default_factory=list)

    @classmethod
    def build(cls, dep: Any, triggered_by_email: str | None = None) -> DeploymentDetail:
        base = DeploymentOut.build(dep, triggered_by_email)
        return cls(
            **base.model_dump(),
            steps=[DeploymentStepOut.model_validate(step) for step in dep.steps],
        )


class LogOut(APIModel):
    """Persisted deployment log line."""

    model_config = APIModel.model_config.copy()
    model_config["extra"] = "ignore"

    id: int
    deployment_id: UUID | None = None
    source: LogSource
    stream: str = "stdout"
    level: LogLevel
    message: str
    ts: datetime
    #: Attributed from step start/finish timestamps (LogEntry has no column).
    step_idx: int | None = None
