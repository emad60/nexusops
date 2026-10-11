"""Certificate schemas — the metadata-only read model and the request body.

Two rules shape every model in this module:

1. **Nothing here can hold key material.** Phase 5.1 has no ciphertext column at
   all, but the read models are written to stay that way: they enumerate the
   fields the API exposes instead of dumping the row, so a column added later
   (a wrapped private key, a chain, a DEK generation) cannot leak by default.
2. **A request that has not been issued must not read as if it had.** Statuses
   and their human description are both derived from the generation the
   certificate actually has, and ``issued`` is true only when a generation
   carrying material is the current one — which Phase 5.1 cannot produce.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import (
    CertificateChallengeType,
    CertificateGenerationState,
    CertificateKeyAlgorithm,
    CertificateStatus,
)
from app.schemas.base import APIModel, OutModel


class CertificateCreate(APIModel):
    """Payload for ``POST /certificates`` — a *request*, never an issuance.

    ``identifiers`` is the order's identifier list: the **first** entry is the
    primary common name and the rest are the additional (SAN) identifiers, so an
    apex + wildcard pair is one order (``["example.com", "*.example.com"]``)
    rather than two certificates. The request body has no ``dns_provider_id`` in
    Phase 5.1 on purpose: that column arrives with its table in 5.2, and
    ``extra="forbid"`` makes sending it a 422 rather than a silently ignored key.
    """

    domain_id: UUID
    identifiers: list[str] = Field(min_length=1, max_length=100)
    #: DNS-01 only in v1; anything else is refused by the service with a named
    #: error, because a challenge nobody can serve is worse than a rejection.
    challenge_type: str = "dns-01"
    #: Renewal preference the sweep honors (it never overrides it).
    auto_renew: bool = True


class CertificateUpdate(APIModel):
    """Payload for ``PATCH /certificates/{id}``.

    ``auto_renew`` is the only field a caller may change after creation. Changing
    the identifiers would change what a *certificate* is, which is a new
    generation — and issuing one is not something this phase does.
    """

    auto_renew: bool | None = None


class CertificateGenerationOut(OutModel):
    """One generation's lifecycle metadata. No material, no internal cursors.

    ``order_state`` is deliberately absent: it is the ACME client's working data
    (order URLs, key authorizations, DNS record values) and stays internal, so
    the read model never has to sanitize what a future writer puts in it.
    """

    updated_at: datetime
    certificate_id: UUID
    generation: int
    state: CertificateGenerationState
    attempt_count: int = 0
    next_attempt_at: datetime | None = None
    last_error: str = ""
    #: Whether the failure may be retried automatically. False once the attempt
    #: budget is spent — that generation is terminal and a new one is required.
    retryable: bool = False
    terminal: bool = False
    #: Human-readable, sanitized explanation of ``state``.
    status_detail: str = ""


class CertificateOut(OutModel):
    """Certificate read model (list and detail share it)."""

    updated_at: datetime
    domain_id: UUID
    domain_name: str | None = None
    domain_status: str | None = None
    #: Canonical, same form as ``domains.name``.
    primary_cn: str
    #: Additional identifiers on the order (the SANs).
    sans: list[str] = Field(default_factory=list)
    #: Derived from the current generation — never a stored claim.
    status: CertificateStatus
    challenge_type: CertificateChallengeType
    key_algorithm: CertificateKeyAlgorithm
    auto_renew: bool = True
    #: Unset until a generation is issued; never inferred from the request.
    expires_at: datetime | None = None
    last_error: str = ""
    #: The generation a *new bind* should reference. NULL until an issuance
    #: exists, which is exactly why a Phase 5.1 certificate cannot be bound.
    current_generation_id: UUID | None = None
    #: The newest generation (what the status above is derived from).
    latest_generation: CertificateGenerationOut | None = None
    #: True only when a material-bearing generation is current. Phase 5.1 cannot
    #: set it; the field exists so no client has to infer issuance from a status
    #: string that also means "requested".
    issued: bool = False
    status_detail: str = ""


class CertificateDetailOut(CertificateOut):
    """Detail adds the whole generation history, newest first."""

    generations: list[CertificateGenerationOut] = Field(default_factory=list)
