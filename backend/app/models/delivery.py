"""Delivery pipeline: projects → environments → applications → deployments.

Phase 2 promotes the environment to **project scope**: a project owns its
environments (dev/staging/prod), and applications are deployed *into* them.
A ``Deployment`` keeps its ``(application_id, environment_id)`` pair, which now
reads "application X was deployed into project environment Y".
"""

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

from app.models.base import (
    Base,
    OrgScoped,
    TimestampMixin,
    json_column,
    status_check,
    uuid_pk,
)
from app.models.enums import DeploymentStatus, DeploymentTrigger, EnvironmentType, StepStatus


class Project(OrgScoped, TimestampMixin, Base):
    __tablename__ = "projects"
    # Project names are unique within an organization, not across the instance.
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_projects_org_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    repository_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    default_branch: Mapped[str] = mapped_column(String(120), default="main", nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    #: Base layer of the project's deploy configuration (Phase 2). Structured
    #: data only: non-secret settings plus ``${secret:KEY}`` references. Holds no
    #: execution semantics — nothing interpolates or evaluates the values here.
    config: Mapped[dict] = json_column()

    applications: Mapped[list[Application]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    environments: Mapped[list[DeploymentEnvironment]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )


class Application(OrgScoped, TimestampMixin, Base):
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


class DeploymentEnvironment(OrgScoped, TimestampMixin, Base):
    """A **project-scoped** deployment environment (Phase 2 promotion).

    The environment belongs to the *project*, not to an application — "Project
    Ymart → Production". Applications deploy *into* a project environment; a
    ``Deployment`` still carries its ``(application_id, environment_id)`` pair,
    which now reads "application X was deployed into environment Y".

    Uniqueness is ``(project_id, slug)``. ``environment_type`` is descriptive:
    it never gates access (permissions do). ``server_id`` (Node) is the target
    machine for the environment when one is assigned; the column keeps its
    Phase 1 name — the ``server.*``→``node.*`` rename was a surface rename and
    the physical column rename is a later cleanup phase (domain-model.md §2.3).
    """

    __tablename__ = "deployment_environments"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_envs_project_slug"),
        status_check("environment_type", EnvironmentType),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(84), nullable=False)
    environment_type: Mapped[EnvironmentType] = mapped_column(
        String(16), default=EnvironmentType.DEV, nullable=False, index=True
    )
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True
    )
    healthcheck_path: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    auto_deploy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Environment *overrides* over the project config: secret references by key
    # name only — values always resolve server-side, never through the API.
    config: Mapped[dict] = json_column()

    project: Mapped[Project] = relationship(back_populates="environments")


class Deployment(OrgScoped, TimestampMixin, Base):
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


class DeploymentStep(OrgScoped, TimestampMixin, Base):
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
