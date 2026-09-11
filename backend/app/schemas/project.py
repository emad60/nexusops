"""Project API schemas."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.application import ApplicationOut, ApplicationSummary
from app.schemas.base import APIModel, OutModel


class ProjectBase(APIModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=5000)
    repository_url: str = Field(default="", max_length=500)
    default_branch: str = Field(default="main", max_length=120)


class ProjectCreate(ProjectBase):
    """Payload to create a project; owner defaults to the caller."""

    owner_id: UUID | None = None


class ProjectUpdate(APIModel):
    """Partial project update; omitted fields are left untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    repository_url: str | None = Field(default=None, max_length=500)
    default_branch: str | None = Field(default=None, max_length=120)


class ProjectOut(OutModel):
    """Project output with its applications eager-listed."""

    updated_at: datetime
    name: str
    description: str
    repository_url: str
    default_branch: str
    owner_id: UUID | None = None
    # Sequence (covariant) so ProjectDetailOut may narrow items to ApplicationOut.
    applications: Sequence[ApplicationSummary] = Field(default_factory=list)


class ProjectDetailOut(ProjectOut):
    """Project detail; each application carries its latest deployment summary."""

    applications: list[ApplicationOut] = Field(default_factory=list)
