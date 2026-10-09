"""Operator-facing schemas for organization-scoped enrollment tokens.

The raw token is returned exactly once (``EnrollmentTokenCreated``). Every later
read returns ``EnrollmentTokenOut``, which has no token field at all — the
listing endpoint cannot leak a value that never existed server-side.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field, computed_field

from app.models.enums import EnrollmentTokenState
from app.schemas.base import APIModel, OutModel

#: Short-lived by default; an enrollment token is a bootstrap credential.
DEFAULT_TTL_SECONDS = 3600
MAX_TTL_SECONDS = 7 * 86400


class EnrollmentTokenCreate(APIModel):
    """Mint one enrollment token in the caller's active organization."""

    name: str = Field(default="", max_length=120)
    note: str = Field(default="", max_length=500)
    expires_in_seconds: int = Field(default=DEFAULT_TTL_SECONDS, ge=60, le=MAX_TTL_SECONDS)
    #: Optional placeholder node to claim on enrollment. When set, the token is
    #: bound to that node's organization and enrollment claims it rather than
    #: creating a new row.
    node_id: UUID | None = None


class EnrollmentTokenOut(OutModel):
    """Token metadata — never the token itself."""

    org_id: UUID
    name: str
    note: str
    single_use: bool
    expires_at: datetime
    revoked_at: datetime | None = None
    used_at: datetime | None = None
    used_by_node_id: UUID | None = None
    node_id: UUID | None = None
    created_by_id: UUID | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def state(self) -> EnrollmentTokenState:
        """Derived lifecycle state: revoked wins over used wins over expired."""
        if self.revoked_at is not None:
            return EnrollmentTokenState.REVOKED
        if self.used_at is not None:
            return EnrollmentTokenState.USED
        if self.expires_at <= datetime.now(UTC):
            return EnrollmentTokenState.EXPIRED
        return EnrollmentTokenState.ACTIVE


class EnrollmentTokenCreated(EnrollmentTokenOut):
    """The one response that carries the raw token."""

    token: str
    install_hint: str
