"""Application API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import APIModel, OutModel
from app.schemas.deployment import LatestDeploymentSummary

MAX_BUILD_CONFIG_KEYS = 50


class ApplicationBase(APIModel):
    """Shared application fields; ``build_config`` is a free-form dict."""

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=5000)
    repository_url: str = Field(default="", max_length=500)
    build_config: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Free-form build settings (dockerfile path, target platform, ...). "
            "Shallow-validated only. Never place secret VALUES here — reference "
            "them via environment config instead."
        ),
    )

    @field_validator("build_config")
    @classmethod
    def _shallow_validate(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > MAX_BUILD_CONFIG_KEYS:
            raise ValueError(f"build_config supports at most {MAX_BUILD_CONFIG_KEYS} keys")
        for key in value:
            if not isinstance(key, str) or not key.strip():
                raise ValueError("build_config keys must be non-empty strings")
        return value


class ApplicationCreate(ApplicationBase):
    """Payload to register an application under a project."""


class ApplicationUpdate(APIModel):
    """Partial application update; omitted fields are left untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    repository_url: str | None = Field(default=None, max_length=500)
    build_config: dict[str, Any] | None = None


class ApplicationSummary(OutModel):
    """Application as embedded in project outputs (no deployment summary)."""

    updated_at: datetime
    project_id: UUID
    name: str
    slug: str
    description: str
    repository_url: str
    build_config: dict[str, Any]
    current_version: str | None = None


class ApplicationOut(ApplicationSummary):
    """Full application output with its latest deployment summary, if any."""

    latest_deployment: LatestDeploymentSummary | None = None
