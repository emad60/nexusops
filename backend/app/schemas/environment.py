"""Deployment-environment API schemas.

``config`` holds secret REFERENCES only (values shaped like
``${secret:KEY_NAME}``); raw secret values are never accepted here — the
deployment engine resolves references server-side at execution time.
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import APIModel, OutModel

MAX_ENV_CONFIG_KEYS = 50
MAX_ENV_VALUE_LENGTH = 512
_SECRET_REFERENCE_RE = re.compile(r"^\$\{secret:([A-Za-z0-9_]+)\}$")


class EnvironmentBase(APIModel):
    """Shared environment fields."""

    name: str = Field(min_length=1, max_length=64)
    server_id: UUID | None = Field(
        default=None,
        description="Target server (existence-checked). NULL means engine-local run.",
    )
    healthcheck_path: str = Field(default="", max_length=300)
    auto_deploy: bool = False
    config: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Environment settings. Values that reference secrets MUST use the "
            "'${secret:KEY_NAME}' form; raw secret values are rejected."
        ),
    )

    @field_validator("config")
    @classmethod
    def _validate_config(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > MAX_ENV_CONFIG_KEYS:
            raise ValueError(f"config supports at most {MAX_ENV_CONFIG_KEYS} keys")
        for key, item in value.items():
            if not key.strip():
                raise ValueError("config keys must be non-empty strings")
            if len(item) > MAX_ENV_VALUE_LENGTH:
                raise ValueError(f"config value for '{key}' exceeds {MAX_ENV_VALUE_LENGTH} chars")
            if "${secret:" in item and not _SECRET_REFERENCE_RE.fullmatch(item):
                raise ValueError(f"config value for '{key}' must look like ${{secret:KEY_NAME}}")
        return value


class EnvironmentCreate(EnvironmentBase):
    """Payload to create an environment under an application."""


class EnvironmentUpdate(APIModel):
    """Partial environment update; omitted fields are left untouched."""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    server_id: UUID | None = None
    healthcheck_path: str | None = Field(default=None, max_length=300)
    auto_deploy: bool | None = None
    config: dict[str, str] | None = None


class EnvironmentOut(OutModel):
    """Environment output. ``config`` contains references, never values."""

    updated_at: datetime
    application_id: UUID
    name: str
    slug: str
    server_id: UUID | None = None
    healthcheck_path: str
    auto_deploy: bool
    config: dict[str, str]
