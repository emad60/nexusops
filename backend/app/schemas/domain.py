"""Domain schemas: create/list/detail plus the DNS instructions a user must publish.

The verification token is deliberately *not* part of the ordinary read model.
It is returned by the create response and by the detail endpoint only for callers
holding ``domain.manage`` while the name is still awaiting (or has lost) proof —
after that it is not retrievable, because a token that outlives its usefulness is
only a replay primitive.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import DomainStatus
from app.schemas.base import APIModel, OutModel


class DomainCreate(APIModel):
    """Payload for ``POST /domains``.

    ``name`` is passed through the canonicaliser; it is never stored raw.
    ``project_id`` is organization-scoped grouping only.
    """

    name: str = Field(min_length=4, max_length=253)
    project_id: UUID | None = None


class DomainVerificationOut(APIModel):
    """Exactly the record an authorized domain manager has to publish."""

    record_name: str
    record_type: str = "TXT"
    record_value: str
    #: Whether the value still has to be published (`pending`/`unverified`/…).
    active: bool = True


class DomainReachabilityOut(APIModel):
    """Best-effort A/AAAA check against the serving node — a warning, not a gate."""

    hostname: str | None = None
    addresses: list[str] = Field(default_factory=list)
    expected_addresses: list[str] = Field(default_factory=list)
    resolves_to_node: bool | None = None
    checked_at: datetime | None = None
    warning: str | None = None


class DomainOut(OutModel):
    """Domain read model (list and detail share it)."""

    updated_at: datetime
    project_id: UUID | None = None
    project_name: str | None = None
    name: str
    status: DomainStatus
    #: Derived from ``status`` by the endpoint (no DB column), so it carries a
    #: default and is always overwritten in the serializer.
    verified: bool = False
    verified_at: datetime | None = None
    last_checked_at: datetime | None = None
    proof_lost_at: datetime | None = None
    stale_expires_at: datetime | None = None
    attempt_count: int = 0
    last_error: str = ""
    ns_snapshot: list[str] = Field(default_factory=list)
    verification: DomainVerificationOut | None = None
    reachability: DomainReachabilityOut | None = None
    route_count: int = 0
    enabled_route_count: int = 0


class DomainDetailOut(DomainOut):
    """Detail adds the routes this name answers for."""

    routes: list[Any] = Field(default_factory=list)
