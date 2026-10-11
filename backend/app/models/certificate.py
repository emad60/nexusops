"""Certificates and their generations — the Phase 5 metadata foundation.

Two tenant-owned tables, one relationship spine:
**Organization → Domain → Certificate → CertificateGeneration**.

Phase 5.1 ships the *identity and lifecycle* half of the certificate subsystem
and nothing else. No ACME client, no DNS provider, no key envelope, no key
material, no delivered configuration: those are the later slices (5.2 to 5.5),
and the schema says so rather than describing them:

* ``certificates`` carries the identity — which verified domain the certificate
  is for, its primary common name, its additional identifiers, the challenge
  type, the renewal preference — plus a **derived** status and the denormalized
  expiry the list/sweep reads.
* ``certificate_generations`` carries one ACME order + one key pair. Its ``state``
  CHECK is limited to the pre-issuance vocabulary
  (:class:`~app.models.enums.CertificateGenerationState`), so an ``ISSUED``
  generation — one that would have to carry a private key — cannot exist before
  the envelope that protects the material does. There is no ``deke_id`` column
  and no placeholder value for one.

Three structural promises live in the schema rather than in prose:

* ``uq_certificates_org_cn`` — one certificate row per name per organization;
  renewal reuses the row with a new generation.
* ``uq_cert_generations_one_live`` — **at most one in-flight generation per
  certificate**, enforced by a partial unique index, so two concurrent issuance
  requests are a database error instead of two racing orders.
* ``uq_certificate_generations_cert_number`` — generation numbers are unique and
  monotonic per certificate, so a rewound or duplicated renewal is refused.

Deletion: a generation is removed only with its certificate (``ON DELETE
CASCADE``), and a domain that still has certificates cannot be deleted at all
(``ON DELETE RESTRICT``) — withdrawing the name a certificate was issued for
would strand material that the CA still considers valid.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (
    Base,
    OrgScoped,
    TimestampMixin,
    json_column,
    status_check,
    uuid_pk,
)
from app.models.enums import (
    CertificateChallengeType,
    CertificateGenerationState,
    CertificateKeyAlgorithm,
    CertificateStatus,
)

#: Longest identifier list we accept on one order (mirrors the design's bound).
MAX_IDENTIFIERS = 100


def one_live_generation_predicate() -> str:
    """The SQL predicate of ``uq_cert_generations_one_live``.

    Built from :meth:`CertificateGenerationState.live_pre_issuance` so the index
    and the state machine cannot drift: adding a live state to the enum widens
    the index in the same change.
    """
    states = ", ".join(
        f"'{state.value}'" for state in CertificateGenerationState.live_pre_issuance()
    )
    return f"state IN ({states})"


class Certificate(OrgScoped, TimestampMixin, Base):
    """One requested certificate: an identity, its lifecycle view, no material."""

    __tablename__ = "certificates"
    __table_args__ = (
        status_check("status", CertificateStatus),
        status_check("challenge_type", CertificateChallengeType),
        status_check("key_algorithm", CertificateKeyAlgorithm),
        # One certificate row per name per organization. A renewal does not
        # create a second row; it creates a second generation of this one.
        UniqueConstraint("org_id", "primary_cn", name="uq_certificates_org_cn"),
        CheckConstraint("char_length(primary_cn) BETWEEN 4 AND 253", name="primary_cn_length"),
        # The array shape only. Element canonicality (lowercase, punycode, no IP
        # literal) is enforced on every write through ``canonicalize_name`` —
        # SQL cannot run IDNA, and a constraint that pretended to would be worse
        # than one that states its limit.
        CheckConstraint(
            "jsonb_typeof(sans) = 'array' AND jsonb_array_length(sans) <= 100",
            name="sans_shape",
        ),
        Index("ix_certificates_domain_id", "domain_id"),
        Index("ix_certificates_org_status", "org_id", "status"),
        # The renewal sweep: which issued certificates are close to expiry.
        Index("ix_certificates_expiry_sweep", "status", "expires_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    #: The name this certificate is for. RESTRICT: a certificate is issued for a
    #: name, so deleting the domain would orphan material the CA still honours.
    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domains.id", ondelete="RESTRICT"), nullable=False
    )
    #: Canonical primary common name (same form as ``domains.name``).
    primary_cn: Mapped[str] = mapped_column(String(253), nullable=False)
    #: *Additional* identifiers on the order, canonical. An apex + wildcard pair
    #: is one certificate with the wildcard here, not two certificates.
    sans: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    #: The certificate-level view, **derived** from the current generation by
    #: :mod:`app.services.certificate_lifecycle` on read. Phase 5.1 can only
    #: produce ``PENDING`` or ``FAILED`` — nothing has been issued yet.
    status: Mapped[CertificateStatus] = mapped_column(
        String(24), default=CertificateStatus.PENDING, nullable=False
    )
    #: The generation a *new bind* should reference. NULL until a generation is
    #: issued: a request that has not produced material has no current
    #: generation, and saying otherwise would let a route bind to nothing.
    #:
    #: ``use_alter`` because this reference and ``certificate_generations``' own
    #: ``certificate_id`` point at each other: the constraint is created by an
    #: ``ALTER TABLE`` after both tables exist (the migration does exactly that).
    #: Without the flag SQLAlchemy's table sorter hits an unresolvable cycle and
    #: stops considering the foreign keys of every table in that cycle group for
    #: schema comparison — which would silently weaken the drift test for
    #: unrelated tables (routes, monitors, roles, users).
    current_generation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("certificate_generations.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    challenge_type: Mapped[CertificateChallengeType] = mapped_column(
        String(8), default=CertificateChallengeType.DNS_01, nullable=False
    )
    #: Renewal preference. The sweep skips ``False``; it never overrides it.
    auto_renew: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default=text("true")
    )
    #: Fixed in v1 (``ecdsa-p256``): never client-chosen, so a caller cannot ask
    #: for a key type the delivery path does not implement.
    key_algorithm: Mapped[CertificateKeyAlgorithm] = mapped_column(
        String(16), default=CertificateKeyAlgorithm.ECDSA_P256, nullable=False
    )
    #: Denormalized from the current generation's ``notAfter`` for list/sort.
    #: Unset until a generation is issued — never guessed from the request.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Sanitized, bounded reason the newest generation failed. Never key material,
    #: never an ACME account key, never another organization's data.
    last_error: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Certificate {self.primary_cn} {self.status}>"


class CertificateGeneration(OrgScoped, TimestampMixin, Base):
    """One ACME order + one key pair. Renewal inserts a new row, never mutates one.

    Keeping generations separate is what makes "an older generation must not
    replace a newer one" representable (§8.5) instead of being a comparison the
    code has to remember to perform.
    """

    __tablename__ = "certificate_generations"
    __table_args__ = (
        status_check("state", CertificateGenerationState),
        # Generation numbers are monotonic per certificate; this is the backstop
        # against a rewound or duplicated renewal.
        UniqueConstraint(
            "certificate_id", "generation", name="uq_certificate_generations_cert_number"
        ),
        # At most one in-flight generation per certificate. ``FAILED`` is outside
        # the predicate on purpose, so a retry can insert its own row.
        Index(
            "uq_cert_generations_one_live",
            "certificate_id",
            unique=True,
            postgresql_where=text(one_live_generation_predicate()),
        ),
        # The retry/sweep cursor: which generation is due an attempt next.
        Index("ix_certificate_generations_sweep", "state", "next_attempt_at"),
        CheckConstraint("generation >= 1", name="generation_positive"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    certificate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("certificates.id", ondelete="CASCADE"), nullable=False
    )
    #: Monotonic per certificate; what a delivery binds to.
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Pre-issuance only in Phase 5.1. See
    #: :class:`~app.models.enums.CertificateGenerationState`.
    state: Mapped[CertificateGenerationState] = mapped_column(
        String(24), default=CertificateGenerationState.PENDING, nullable=False
    )
    #: ACME order/challenge URLs, key authorizations, DNS record names/values —
    #: **public ACME data only, never the account key**. Populated by the
    #: issuance slice (5.3); always ``{}`` in 5.1.
    order_state: Mapped[dict[str, Any]] = json_column()
    last_error: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    #: Bounded backoff cursors of *this* generation's attempts.
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<CertificateGeneration #{self.generation} {self.state}>"
