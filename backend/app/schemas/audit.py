"""Schemas for the read-only audit log API.

The audit table is append-only; these are pure read models.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import OutModel


class AuditOut(OutModel):
    """One audit trail entry (no write routes ever exist for this resource)."""

    actor_id: UUID | None = None
    actor_email: str
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str = ""
    user_agent: str = ""
    result: str
    # Stored column is `metadata` in SQL; the ORM attribute is `metadata_`
    # (the bare name collides with the reserved declarative `.metadata`).
    # Validate from the attribute ONLY: accepting "metadata" for validation
    # makes from_attributes read the declarative Base's MetaData object,
    # which 500s every non-empty listing. The wire key stays `metadata`
    # through the serialization alias.
    metadata_: dict[str, Any] = Field(
        default_factory=dict,
        serialization_alias="metadata",
    )
