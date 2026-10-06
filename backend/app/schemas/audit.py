"""Schemas for the read-only audit log API.

The audit table is append-only; these are pure read models.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import OutModel


class AuditOut(OutModel):
    """One audit trail entry (no write routes ever exist for this resource).

    ``org_id`` is reported explicitly. The listing is already filtered to the
    caller's organization, so it is not how isolation is achieved — it is how a
    security event identifies *which* tenant it belongs to when the trail is
    exported, correlated or handed to an auditor. It is ``None`` only for the
    genuinely instance-level events (a failed login for an address with no
    account), which are written under the system scope and are invisible to
    every tenant.
    """

    org_id: UUID | None = None
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
