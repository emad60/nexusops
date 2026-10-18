"""Certificate schemas — the metadata-only read model and the request body.

Two rules shape every model in this module:

1. **Nothing here can hold key material.** The read models enumerate the fields
   the API exposes instead of dumping the row, so a column added later (a wrapped
   private key, a chain, an ACME account key) cannot leak by default. Since 5.2.2
   those columns exist and the rule is what keeps them out of every response —
   ``key_ciphertext``, ``chain_ciphertext`` and ``deke_id`` are simply not named
   here, and ``order_state`` is excluded on the same grounds (it holds the ACME
   client's working data, including challenge values).
2. **A request that has not been issued must not read as if it had.** Statuses
   and their human description are both derived from the generation the
   certificate actually has, and ``issued`` is true only when a generation
   carrying material is the current one.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import (
    AcmeDirectory,
    CertificateChallengeType,
    CertificateGenerationState,
    CertificateKeyAlgorithm,
    CertificateRevocationState,
    CertificateStatus,
)
from app.schemas.base import APIModel, OutModel


class CertificateCreate(APIModel):
    """Payload for ``POST /certificates`` — a *request*, never an issuance.

    ``identifiers`` is the order's identifier list: the **first** entry is the
    primary common name and the rest are the additional (SAN) identifiers, so an
    apex + wildcard pair is one order (``["example.com", "*.example.com"]``)
    rather than two certificates.

    ``dns_provider_id`` names the credential the DNS-01 challenge is published
    with. It is optional at request time — a certificate may be recorded before an
    operator has stored a credential — but issuance refuses one that names none, so
    ``PATCH /certificates/{id}`` is how it is attached afterwards. The id must name
    a row in the caller's own organization — a foreign id is a 404, never a stored
    reference that would later publish a challenge with someone else's credential.
    """

    domain_id: UUID
    identifiers: list[str] = Field(min_length=1, max_length=100)
    #: DNS-01 only in v1; anything else is refused by the service with a named
    #: error, because a challenge nobody can serve is worse than a rejection.
    challenge_type: str = "dns-01"
    #: Renewal preference the sweep honors (it never overrides it).
    auto_renew: bool = True
    #: The DNS credential this certificate's challenges are published with.
    dns_provider_id: UUID | None = None


class CertificateUpdate(APIModel):
    """Payload for ``PATCH /certificates/{id}``.

    Two fields a caller may change after creation. ``auto_renew`` is a preference;
    ``dns_provider_id`` is which credential may publish this certificate's
    challenges (null clears it, leaving the certificate unissuable until one is
    attached). Neither changes what the certificate *is*: different identifiers
    would be a new generation, and issuing one is not something this phase does.

    The two fields treat an explicit ``null`` differently, and deliberately:
    ``null`` for ``auto_renew`` is not a value, so it is ignored rather than
    recorded as a change, while ``null`` for ``dns_provider_id`` is exactly a
    value — it clears an override.
    """

    auto_renew: bool | None = None
    dns_provider_id: UUID | None = None


class CertificateGenerationOut(OutModel):
    """One generation's lifecycle metadata. No material, no internal cursors.

    ``order_state`` is deliberately absent: it is the ACME client's working data
    (order URLs, key authorizations, DNS record values) and stays internal, so
    the read model never has to sanitize what a future writer puts in it. The
    material columns (``key_ciphertext``, ``chain_ciphertext``, ``deke_id``) are
    absent for the stronger reason: they exist now, and no response may carry one.
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
    #: The CA's validity window, once issued. Metadata about the material — never
    #: the material. ``not_after`` is what the renewal sweep reasons about.
    not_before: datetime | None = None
    not_after: datetime | None = None
    issued_at: datetime | None = None
    #: SHA-256 of the leaf, for display and drift checks (which certificate is
    #: installed on a node). Never a decryption oracle.
    fingerprint: str | None = None
    #: The CA axis, kept separate from ``state`` so "the authority never answered"
    #: is visible as its own fact rather than folded into the lifecycle.
    revocation_state: CertificateRevocationState = CertificateRevocationState.NOT_REQUESTED
    #: Which certificate authority this generation's order was placed with, as the
    #: directory URL recorded on the row. Written *before* material exists, so a
    #: failed or abandoned attempt still says which CA it spoke to, and never
    #: rewritten: a retry at another directory is a new generation, which is what
    #: keeps a staging order from becoming a production certificate halfway
    #: through. NULL means no order was ever placed.
    directory_url: str | None = None
    #: The same value as a known directory, or NULL when this version does not
    #: recognise the URL it finds.
    directory: AcmeDirectory | None = None
    #: Whether a certificate from that directory is trusted by a browser: False for
    #: staging and for the test CA, and False for an unrecognised URL — only
    #: production is publicly trusted, so the safe reading needs no special case.
    #: Says nothing about whether material exists; ``issued`` on the certificate is
    #: that question, and a failed attempt at production is publicly-trusted *and*
    #: unissued.
    publicly_trusted: bool = False


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
    #: True only when a material-bearing generation is current. False while a
    #: request has only been ordered, so no client has to infer issuance from a
    #: status string that also means "requested".
    issued: bool = False
    #: The credential this certificate's challenges may be published with. NULL
    #: means none is attached, which is a request issuance refuses to attempt.
    dns_provider_id: UUID | None = None
    status_detail: str = ""


class CertificateDetailOut(CertificateOut):
    """Detail adds the whole generation history, newest first."""

    generations: list[CertificateGenerationOut] = Field(default_factory=list)
