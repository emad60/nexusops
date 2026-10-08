"""Project API schemas."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.application import ApplicationOut, ApplicationSummary
from app.schemas.base import APIModel, OutModel
from app.schemas.environment import EnvironmentOut
from app.services.config_service import validate_config


class ProjectBase(APIModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=5000)
    repository_url: str = Field(default="", max_length=500)
    default_branch: str = Field(default="main", max_length=120)
    config: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Project base configuration: a flat string→string map applied to every "
            "environment of the project. Environment overrides win per key. Values "
            "may be '${secret:KEY_NAME}' references; raw secret values are rejected."
        ),
    )

    @field_validator("config")
    @classmethod
    def _validate_config(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_config(value, label="config")


class ProjectCreate(ProjectBase):
    """Payload to create a project; owner defaults to the caller."""

    owner_id: UUID | None = None


class ProjectUpdate(APIModel):
    """Partial project update; omitted fields are left untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    repository_url: str | None = Field(default=None, max_length=500)
    default_branch: str | None = Field(default=None, max_length=120)
    config: dict[str, str] | None = None

    @field_validator("config")
    @classmethod
    def _validate_config(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        return validate_config(value, label="config")


class ProjectOut(OutModel):
    """Project output with its applications eager-listed."""

    updated_at: datetime
    name: str
    description: str
    repository_url: str
    default_branch: str
    owner_id: UUID | None = None
    config: dict[str, str] = Field(default_factory=dict)
    # Sequence (covariant) so ProjectDetailOut may narrow items to ApplicationOut.
    applications: Sequence[ApplicationSummary] = Field(default_factory=list)


class ProjectDetailOut(ProjectOut):
    """Project detail: applications with latest deployment, plus its environments.

    The project is the parent of its environments (Phase 2); the detail view is
    where the SPA lists them.
    """

    applications: list[ApplicationOut] = Field(default_factory=list)
    environments: list[EnvironmentOut] = Field(default_factory=list)
