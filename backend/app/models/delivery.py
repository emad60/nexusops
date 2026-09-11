"""Delivery pipeline: projects → applications → environments → deployments."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, json_column, status_check, uuid_pk
from app.models.enums import DeploymentStatus, DeploymentTrigger, StepStatus


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    repository_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    default_branch: Mapped[str] = mapped_column(String(120), default="main", nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    applications: Mapped[list[Application]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )


class Application(TimestampMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_applications_project_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    repository_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    build_config: Mapped[dict] = json_column()
    current_version: Mapped[str | None] = mapped_column(String(160), nullable=True)
    current_deployment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deployments.id", ondelete="SET NULL", use_alter=True), nullable=True
    )

    project: Mapped[Project] = relationship(back_populates="applications")
    deployments: Mapped[list[Deployment]] = relationship(
        back_populates="application",
        foreign_keys="Deployment.application_id",
        order_by="Deployment.number.desc()",
    )


class DeploymentEnvironment(TimestampMixin, Base):
    __tablename__ = "deployment_environments"
    __table_args__ = (UniqueConstraint("application_id", "name", name="uq_envs_application_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(84), nullable=False)
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True
    )
    healthcheck_path: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    auto_deploy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Secret references by key name only — values always resolve server-side.
    config: Mapped[dict] = json_column()


class Deployment(TimestampMixin, Base):
    __tablename__ = "deployments"
    __table_args__ = (
        UniqueConstraint("application_id", "number", name="uq_deployments_app_number"),
        status_check("status", DeploymentStatus),
        status_check("trigger", DeploymentTrigger),
        Index("ix_deployments_status_created", "status", "created_at"),
        Index("ix_deployments_environment_created", "environment_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deployment_environments.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(160), nullable=False)
    git_commit: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    status: Mapped[DeploymentStatus] = mapped_column(
        String(16), default=DeploymentStatus.QUEUED, nullable=False, index=True
    )
    trigger: Mapped[DeploymentTrigger] = mapped_column(
        String(16), default=DeploymentTrigger.MANUAL, nullable=False
    )
    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_rollback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rollback_of_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deployments.id", ondelete="SET NULL"), nullable=True
    )

    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    failure_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    application: Mapped[Application] = relationship(
        back_populates="deployments", foreign_keys=[application_id]
    )
    environment: Mapped[DeploymentEnvironment] = relationship()
    steps: Mapped[list[DeploymentStep]] = relationship(
        back_populates="deployment",
        cascade="all, delete-orphan",
        order_by="DeploymentStep.idx",
        lazy="selectin",
    )


class DeploymentStep(TimestampMixin, Base):
    __tablename__ = "deployment_steps"
    __table_args__ = (
        UniqueConstraint("deployment_id", "idx", name="uq_steps_deployment_idx"),
        status_check("status", StepStatus),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[StepStatus] = mapped_column(
        String(16), default=StepStatus.PENDING, nullable=False
    )
    output: Mapped[str] = mapped_column(Text, default="", nullable=False)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deployment: Mapped[Deployment] = relationship(back_populates="steps")
