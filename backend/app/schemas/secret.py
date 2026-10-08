"""Schemas for the secrets manager.

Metadata only: no schema in this module may ever carry plaintext values or
ciphertext. The plaintext is accepted on create/rotate and never returned.
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import APIModel, OutModel

#: Secret keys: uppercase start, then uppercase/digits/underscore/dot/dash,
#: ending alphanumeric (1..160 total length).
SECRET_KEY_PATTERN = r"^[A-Z][A-Z0-9_.-]{0,158}[A-Z0-9]$"  # noqa: S105 - regex, not a credential

SECRET_VALUE_MIN_LENGTH = 1
SECRET_VALUE_MAX_LENGTH = 65536

#: Environment-config interpolation form: ``${secret:KEY}``.
SECRET_REF_PATTERN = re.compile(r"\$\{secret:([A-Z][A-Z0-9_.-]{0,158}[A-Z0-9])\}")


class SecretCreate(APIModel):
    """Create-secret payload. ``value`` is encrypted at rest and never echoed.

    Scope is chosen by which ids are present, most specific first:
    ``environment_id`` (that environment) > ``project_id`` (whole project) >
    neither (organization-wide).
    """

    key: str = Field(
        pattern=SECRET_KEY_PATTERN,
        min_length=2,
        max_length=160,
        description="Uppercase secret key, e.g. DB_PASSWORD",
    )
    value: str = Field(
        min_length=SECRET_VALUE_MIN_LENGTH,
        max_length=SECRET_VALUE_MAX_LENGTH,
        description="Plaintext value; stored Fernet-encrypted",
    )
    project_id: UUID | None = None
    environment_id: UUID | None = Field(
        default=None,
        description="Environment scope; implies ``project_id`` and is validated against it.",
    )
    description: str = Field("", max_length=300)


class SecretRotate(APIModel):
    """Rotate-secret payload with the replacement value."""

    value: str = Field(
        min_length=SECRET_VALUE_MIN_LENGTH,
        max_length=SECRET_VALUE_MAX_LENGTH,
        description="New plaintext value; stored Fernet-encrypted",
    )


class SecretRollback(APIModel):
    """Roll a secret back to a previous version, non-destructively.

    The target version's value is re-appended as a **new** version; no historical
    version is rewritten or deleted.
    """

    version: int = Field(
        ge=1,
        description="Existing version number to make current (a new version is appended)",
    )


class SecretOut(OutModel):
    """Secret metadata — deliberately excludes any value-bearing field."""

    key: str
    version: int
    digest: str
    description: str = ""
    project_id: UUID | None = None
    environment_id: UUID | None = None
    rotated_at: datetime | None = None
    rotated_by_email: str | None = None
    updated_at: datetime


class SecretVersionOut(OutModel):
    """One immutable version's **metadata**. Never carries ciphertext or value."""

    secret_id: UUID
    version: int
    digest: str
    created_by_email: str | None = None
    created_at: datetime
