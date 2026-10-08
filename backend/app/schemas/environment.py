"""Deployment-environment API schemas (Phase 2: **project-scoped**).

An environment belongs to a *project*, not an application. ``config`` holds the
environment's **overrides** over the project configuration; both are flat
string→string maps whose values may be ``${secret:KEY}`` references. Raw secret
values are never accepted or returned here — the deployment engine resolves
references server-side.

``environment_type`` is descriptive (dev/staging/prod) and never an
authorization dimension.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import EnvironmentType
from app.schemas.base import APIModel, OutModel
from app.services.config_service import validate_config

#: Accepted spellings for ``environment_type``, normalised to the stored enum.
#: Both the terse form (``dev``) and the SPA label (``development``) are accepted
#: case-insensitively, so a client never has to guess the storage casing.
_ENVIRONMENT_TYPE_ALIASES: dict[str, str] = {
    "DEV": "DEV",
    "DEVELOPMENT": "DEV",
    "STAGING": "STAGING",
    "STAGE": "STAGING",
    "PROD": "PROD",
    "PRODUCTION": "PROD",
}


def _normalise_environment_type(value: object) -> object:
    if isinstance(value, EnvironmentType):
        return value
    if isinstance(value, str):
        mapped = _ENVIRONMENT_TYPE_ALIASES.get(value.strip().upper())
        if mapped is not None:
            return mapped
    return value


class EnvironmentBase(APIModel):
    """Shared environment fields."""

    name: str = Field(min_length=1, max_length=64)
    environment_type: EnvironmentType = Field(
        default=EnvironmentType.DEV,
        description="DEV / STAGING / PROD. Descriptive only — never gates access.",
    )
    server_id: UUID | None = Field(
        default=None,
        description="Target node (existence-checked). NULL means engine-local run.",
    )
    healthcheck_path: str = Field(default="", max_length=300)
    auto_deploy: bool = False
    config: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Environment overrides over the project config: a flat string→string "
            "map. Values that reference secrets MUST use the '${secret:KEY_NAME}' "
            "form; raw secret values are rejected."
        ),
    )

    @field_validator("environment_type", mode="before")
    @classmethod
    def _validate_environment_type(cls, value: object) -> object:
        return _normalise_environment_type(value)

    @field_validator("config")
    @classmethod
    def _validate_config(cls, value: dict[str, str]) -> dict[str, str]:
        return validate_config(value, label="config")


class EnvironmentCreate(EnvironmentBase):
    """Payload to create an environment under a project."""


class EnvironmentUpdate(APIModel):
    """Partial environment update; omitted fields are left untouched.

    Config is validated here too — the create path is not the only way in
    (secrets-architecture.md §1.4 recorded the old gap).
    """

    name: str | None = Field(default=None, min_length=1, max_length=64)
    environment_type: EnvironmentType | None = None
    server_id: UUID | None = None
    healthcheck_path: str | None = Field(default=None, max_length=300)
    auto_deploy: bool | None = None
    config: dict[str, str] | None = None

    @field_validator("environment_type", mode="before")
    @classmethod
    def _validate_environment_type(cls, value: object) -> object:
        if value is None:
            return None
        return _normalise_environment_type(value)

    @field_validator("config")
    @classmethod
    def _validate_config(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        return validate_config(value, label="config")


class EnvironmentOut(OutModel):
    """Environment output. ``config`` contains references, never values."""

    updated_at: datetime
    project_id: UUID
    name: str
    slug: str
    environment_type: EnvironmentType
    server_id: UUID | None = None
    healthcheck_path: str
    auto_deploy: bool
    config: dict[str, str]


class EnvironmentDetailOut(EnvironmentOut):
    """Environment detail.

    Keeps the project base configuration, the environment overrides and the
    merged ``effective_config`` visibly separate, so the UI never has to guess
    which layer a value came from. ``secret_references`` lists key **names** an
    environment names — names are not secrets; values are never exposed.
    """

    project_config: dict[str, str] = Field(default_factory=dict)
    effective_config: dict[str, str] = Field(default_factory=dict)
    secret_references: list[str] = Field(default_factory=list)
    application_count: int = 0
    deployment_count: int = 0
    secret_count: int = 0
