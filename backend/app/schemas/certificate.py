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
    CertificateDnsMode,
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

    ``dns_mode`` says **who publishes** the DNS-01 record, and it is required
    rather than derived: ``automated`` (the default, this platform writes it through
    ``dns_provider_id``) or ``manual`` (the customer writes it, and no credential is
    involved at all). A manual request naming a ``dns_provider_id`` is refused — the
    two halves of the row would describe different publishers.

    ``dns_provider_id`` names the credential the DNS-01 challenge is published
    with. It is optional at request time — a certificate may be recorded before an
    operator has stored a credential — but automated issuance refuses one that names
    none, so ``PATCH /certificates/{id}`` is how it is attached afterwards. The id
    must name a row in the caller's own organization — a foreign id is a 404, never
    a stored reference that would later publish a challenge with someone else's
    credential.
    """

    domain_id: UUID
    identifiers: list[str] = Field(min_length=1, max_length=100)
    #: DNS-01 only in v1; anything else is refused by the service with a named
    #: error, because a challenge nobody can serve is worse than a rejection.
    challenge_type: str = "dns-01"
    #: Who publishes the challenge record. Explicit, never inferred from a missing
    #: credential: "no credential attached" is also the state of an automated
    #: request whose credential has not been stored yet.
    dns_mode: str = CertificateDnsMode.AUTOMATED.value
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
    #: means none is attached, which a *manual* certificate requires and an
    #: automated one cannot be attempted without.
    dns_provider_id: UUID | None = None
    #: Who publishes the challenge record. Read by an operator to know whose job
    #: the next step is; never inferred from ``dns_provider_id`` being NULL.
    dns_mode: CertificateDnsMode = CertificateDnsMode.AUTOMATED
    status_detail: str = ""


class CertificateDetailOut(CertificateOut):
    """Detail adds the whole generation history, newest first."""

    generations: list[CertificateGenerationOut] = Field(default_factory=list)


class ManualChallengeRecordOut(APIModel):
    """One DNS-01 record an operator has to publish.

    The only place a challenge **value** appears in any API response, and it is
    reachable only through the two organization-scoped challenge endpoints for a
    certificate that is currently waiting. Never part of the certificate read model,
    an event payload, an audit entry or a log line.
    """

    reference: str
    #: The identifier this challenge authorizes (``example.com``, ``*.example.com``).
    identifier: str
    wildcard: bool = False
    #: The exact name to publish at, e.g. ``_acme-challenge.example.com``.
    record_name: str
    #: The exact TXT value to publish. Presented so an operator can copy it; opaque
    #: to everything else.
    record_value: str
    record_type: str = "TXT"
    #: A recommendation only. The record belongs to the customer, who chooses its TTL.
    recommended_ttl: int | None = None
    #: The operator has said this record is published. A request to recheck, **not**
    #: proof of propagation and not a verdict on the challenge.
    confirmed: bool = False
    confirmed_at: datetime | None = None
    #: This platform has seen the value at the authoritative servers.
    observed: bool = False
    observed_at: datetime | None = None
    #: The CA's authorization succeeded. The only verdict that counts.
    validated: bool = False
    validated_at: datetime | None = None
    #: Why this challenge cannot be acted on, when the persisted data no longer has
    #: the shape the flow produced. Empty when it can.
    problem: str = ""


class ManualNameserverAnswerOut(APIModel):
    """One authoritative server's answer in the last observation. Never its values."""

    server: str
    status: str = ""
    #: Whether that server served every value expected of it.
    serves_expected: bool = False


class ManualObservationOut(APIModel):
    """The last authoritative observation, as stored.

    Carries the judged status, the detail and a per-server summary — deliberately
    **not** the TXT values the servers returned, because a name may hold other
    services' records (SPF, site verification) and this workflow has no use for them.
    """

    status: str = ""
    detail: str = ""
    checked_at: datetime | None = None
    attempts: int = 0
    nameservers: list[ManualNameserverAnswerOut] = Field(default_factory=list)


class ManualCleanupRecordOut(APIModel):
    """One name whose challenge value(s) are no longer needed."""

    record_name: str
    #: Exactly the values this workflow asked for. Remove only these.
    remove_values: list[str] = Field(default_factory=list)
    #: True when several challenge values share the name (apex + wildcard), so the
    #: operator knows the name is not "the challenge record" as a whole.
    shared_name: bool = False


class ManualCleanupOut(APIModel):
    """What to do with customer-published records. **This platform never deletes them.**"""

    required: bool = False
    records: list[ManualCleanupRecordOut] = Field(default_factory=list)
    note: str = ""


class ManualChallengeOut(APIModel):
    """What one manual DNS-01 certificate currently needs from an operator.

    ``state`` is the generation's lifecycle state, so a caller can tell "never
    ordered" from "waiting" from "finished". ``resume_requested`` reports whether a
    confirmation handed an attempt to the worker — it is **not** a claim that a
    certificate was issued, which only ``CERTIFICATE_ISSUED`` says.
    """

    certificate_id: UUID
    generation: int
    state: CertificateGenerationState
    #: The names the certificate request covers, and therefore what the challenge
    #: set authorizes. Echoed from the certificate, not from the CA's answer.
    identifiers: list[str] = Field(default_factory=list)
    records: list[ManualChallengeRecordOut] = Field(default_factory=list)
    #: True only when every record is confirmed *and* was seen at the authoritative
    #: servers. Decides whether an attempt is worth starting; never whether DNS is
    #: checked, which every attempt does for itself.
    ready: bool = False
    observation: ManualObservationOut | None = None
    cleanup: ManualCleanupOut | None = None
    resume_requested: bool = False
    #: The order's own expiry, when the CA sent one. An expired order cannot be
    #: resumed, so the next attempt re-orders and re-issues instructions.
    order_expires_at: datetime | None = None


class ManualChallengeConfirmIn(APIModel):
    """Payload for ``POST /certificates/{id}/challenge/confirm``.

    ``references`` narrows the confirmation to specific challenge records. Empty
    means "everything not yet confirmed" — and once everything is confirmed, it means
    "check again", which is the retry path and is not an error.

    This body says the operator *published* the record. It is a request to re-observe
    DNS: it never marks the challenge validated, never marks the certificate issued
    and never skips the platform's own authoritative check.
    """

    references: list[str] = Field(default_factory=list, max_length=100)
