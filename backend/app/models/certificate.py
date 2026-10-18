"""Certificates and their generations — the Phase 5 metadata foundation.

Two tenant-owned tables, one relationship spine:
**Organization → Domain → Certificate → CertificateGeneration**.

Phase 5.1 shipped the *identity and lifecycle* half of the certificate subsystem;
Phase 5.2.2 added the material half; Phase 5.3 adds issuance, which is what finally
writes one of these rows end to end — through the ACME seam
(:mod:`app.services.acme`), with the DNS-01 challenge published to the customer's
own zone through the DNS seam (:mod:`app.providers.dns`). The delivery half is still
absent (Phase 5.4), so nothing here leaves the control plane's database beyond
metadata:

* ``certificates`` carries the identity — which verified domain the certificate
  is for, its primary common name, its additional identifiers, the challenge
  type, the renewal preference — plus a **derived** status, the denormalized
  expiry the list/sweep reads, the DNS credential its challenges are published
  with (5.2.2, added *with* the table it references), and the suspension pair set
  when ownership of an identifier is lost.
* ``certificate_generations`` carries one ACME order + one key pair. Its ``state``
  CHECK is now the **full** vocabulary
  (:class:`~app.models.enums.CertificateGenerationState`), because the envelope
  that protects the material exists (5.2.1) and the material columns ship in the
  same migration as the widening. The two halves are tied together by the
  **material guard CHECK**: a generation in any post-issuance state must carry
  ``key_ciphertext``, ``chain_ciphertext``, ``deke_id``, ``issued_at``,
  ``not_before`` and ``not_after``, so a material-less ``ISSUED`` row is
  unrepresentable rather than merely discouraged, and ``deke_id`` is never a
  placeholder for a key that is not there.

Four structural promises live in the schema rather than in prose:

* ``uq_certificates_org_cn`` — one certificate row per name per organization;
  renewal reuses the row with a new generation.
* ``uq_cert_generations_one_live`` — **at most one in-flight generation per
  certificate**, enforced by a partial unique index, so two concurrent issuance
  requests are a database error instead of two racing orders.
* ``uq_certificate_generations_cert_number`` — generation numbers are unique and
  monotonic per certificate, so a rewound or duplicated renewal is refused.
* ``ck_certificate_generations_material_guard`` — material and ``deke_id`` are
  mandatory in every state that outlives the order (see above).
* ``ck_certificate_generations_directory_known`` +
  ``..._directory_required`` — the provenance pair Phase 5.3 adds: the directory a
  generation was ordered at is always one of the vocabulary's URLs, and every
  material-bearing generation has one. "Staging, not publicly trusted" is derived
  from this column alone.

Deletion: a generation is removed only with its certificate (``ON DELETE
CASCADE``); a domain that still has certificates cannot be deleted at all
(``ON DELETE RESTRICT``) — withdrawing the name a certificate was issued for
would strand material that the CA still considers valid — and neither can a DNS
provider a certificate still names, for the same reason: a rebind to another
credential changes which token the platform signs with, and that must be an
operator's explicit act rather than a deletion's side effect.
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
    Text,
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
    AcmeDirectory,
    CertificateChallengeType,
    CertificateGenerationState,
    CertificateKeyAlgorithm,
    CertificateRevocationState,
    CertificateStatus,
)

#: Longest identifier list we accept on one order (mirrors the design's bound).
MAX_IDENTIFIERS = 100

#: Length of a lower-case hex SHA-256 fingerprint of an issued leaf certificate.
FINGERPRINT_LENGTH = 64


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


def pre_issuance_predicate() -> str:
    """The states in which a generation carries no material *by construction*.

    :meth:`live_pre_issuance` plus ``FAILED``: a spent attempt has no material
    either. Every other state is material-bearing, so the guard CHECK's ``OR``
    branch is exactly :meth:`CertificateGenerationState.material_bearing`.
    """
    states = ", ".join(
        f"'{state.value}'"
        for state in (
            *CertificateGenerationState.live_pre_issuance(),
            CertificateGenerationState.FAILED,
        )
    )
    return f"state IN ({states})"


def material_guard_predicate() -> str:
    """The SQL of ``ck_certificate_generations_material_guard``.

    Derived from the enum so the two cannot drift: a generation is either in a
    pre-issuance state (no material expected) or it must carry its private key,
    its chain, the DEK generation that encrypted them and the validity window the
    CA returned. This is the constraint the migration sequence relies on
    (phase5-design.md §3.7): ``deke_id`` is nullable because pre-issuance rows
    legitimately have none, and it is *mandatory* the moment the state stops
    being pre-issuance — so there is no window in which an issued generation can
    lack its key material or its DEK generation.
    """
    return (
        f"{pre_issuance_predicate()} OR (key_ciphertext IS NOT NULL "
        "AND chain_ciphertext IS NOT NULL AND deke_id IS NOT NULL "
        "AND issued_at IS NOT NULL AND not_before IS NOT NULL AND not_after IS NOT NULL)"
    )


def known_directory_urls() -> tuple[str, ...]:
    """Every ACME directory URL a generation may record, from the vocabulary.

    Read from :class:`~app.models.enums.AcmeDirectory` rather than listed here, so
    a fourth directory cannot be added to the enum and then be refusable by the
    database — the two would disagree, and the disagreement would show up as a
    CHECK violation on the first issuance at the new CA rather than as a compile
    error. A URL *outside* the vocabulary remains unrepresentable, which is the
    point: a hand-edited ``directory_url`` must not be able to claim a CA this
    platform cannot reason about (phase5-design.md §5.4's "no silent fallback").
    """
    return tuple(member.url() for member in AcmeDirectory)


def directory_known_predicate() -> str:
    """``directory_url`` is NULL or names a directory in the vocabulary.

    The ``NULL`` branch exists because every pre-issuance row has no directory yet:
    the directory is chosen when an attempt starts, and a ``PENDING`` generation
    that has never been attempted legitimately has none. The second CHECK
    (:func:`directory_required_predicate`) closes the other half.
    """
    urls = ", ".join(f"'{url}'" for url in known_directory_urls())
    return f"directory_url IS NULL OR directory_url IN ({urls})"


def directory_required_predicate() -> str:
    """A generation that outlives the order must name the CA that issued it.

    The counterpart of the material guard on the *provenance* axis: holding
    material is not enough to be a certificate, because a caller has to be able to
    tell whether the result is publicly trusted (§5.4's "a staging-issued
    certificate is never presented as a production certificate"). Combined with
    :func:`directory_known_predicate` this makes an issued generation with an
    unknown or absent directory unrepresentable, not merely impolite.
    """
    return f"{pre_issuance_predicate()} OR directory_url IS NOT NULL"


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
        # The suspension pair is set and cleared as one fact (§9.3): a suspension
        # without a reason is an incident nobody can explain later, and a reason
        # without a timestamp is a note pretending to be state.
        CheckConstraint(
            "(suspended_at IS NULL) = (suspension_reason = '')",
            name="suspension_pair_valid",
        ),
        Index("ix_certificates_domain_id", "domain_id"),
        Index("ix_certificates_org_status", "org_id", "status"),
        # The renewal sweep: which issued certificates are close to expiry.
        Index("ix_certificates_expiry_sweep", "status", "expires_at"),
        # Which certificates a DNS credential is in use by (also the lookup the
        # provider's RESTRICT delete consults).
        Index("ix_certificates_dns_provider_id", "dns_provider_id"),
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
    #: The DNS provider this certificate's challenges are published with.
    #: Nullable because a request may be recorded before its credential is chosen;
    #: issuance refuses such a certificate (``CERTIFICATE_DNS_CREDENTIAL_MISSING``)
    #: until ``PATCH /certificates/{id}`` attaches one.
    #: ``RESTRICT`` because deleting a credential a certificate still names would
    #: silently change which token the platform signs with — the renewal would
    #: keep working, against a different zone, which is the worst kind of failure.
    dns_provider_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("dns_providers.id", ondelete="RESTRICT"), nullable=True
    )
    #: Set when ownership of an identifier is lost (``domain_ownership_lost``) or
    #: an operator suspends the certificate, cleared when it is rebound or
    #: revoked. Suspension is *not* deletion: the material stays, the identifiers
    #: stop being served, and the reason is recoverable from the row.
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspension_reason: Mapped[str] = mapped_column(String(64), default="", nullable=False)

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
        status_check("revocation_state", CertificateRevocationState),
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
        # The DEK-rotation lookup (§6.3): which rows are still encrypted at a
        # generation the rotation has to revisit.
        Index("ix_certificate_generations_deke_id", "deke_id"),
        CheckConstraint("generation >= 1", name="generation_positive"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
        # The constraint this whole slice exists to make true: material cannot be
        # absent in a state that outlives the order.
        CheckConstraint(material_guard_predicate(), name="material_guard"),
        # ``deke_id`` is nullable (pre-issuance rows have none) but is never 0: a
        # real DEK is generation 1 or later, and the guard already requires it for
        # every material-bearing state.
        CheckConstraint("deke_id IS NULL OR deke_id >= 1", name="deke_id_positive"),
        # The provenance axis (Phase 5.3). Two constraints rather than one, because
        # they fail for different reasons and the operator reads them differently: a
        # row claiming an unlisted directory is corrupt or hand-edited, while a
        # material-bearing row with no directory is a partially applied issuance
        # that must never be mistaken for a certificate. Together they are the exact
        # rule `directory_url` exists for.
        CheckConstraint(directory_known_predicate(), name="directory_known"),
        CheckConstraint(directory_required_predicate(), name="directory_required"),
        CheckConstraint(
            f"fingerprint IS NULL OR char_length(fingerprint) = {FINGERPRINT_LENGTH}",
            name="fingerprint_length",
        ),
        # A validity window that ends before it starts is not a certificate; it is
        # a corrupted row that would make the expiry sweep fire immediately.
        CheckConstraint(
            "not_after IS NULL OR not_before IS NULL OR not_after > not_before",
            name="validity_window",
        ),
        # Generation-level suspension is set and cleared as one fact, like the
        # certificate's pair (§9.3): a generation suspended without a reason is an
        # incident nobody can explain, and a reason without a timestamp is a note
        # pretending to be state.
        CheckConstraint(
            "(suspended_at IS NULL) = (suspension_reason = '')",
            name="suspension_pair_valid",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    certificate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("certificates.id", ondelete="CASCADE"), nullable=False
    )
    #: Monotonic per certificate; what a delivery binds to.
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    #: The full state machine since Phase 5.2.2. Post-issuance states are
    #: material-bearing, which the guard CHECK enforces. See
    #: :class:`~app.models.enums.CertificateGenerationState`.
    state: Mapped[CertificateGenerationState] = mapped_column(
        String(24), default=CertificateGenerationState.PENDING, nullable=False
    )
    #: ACME order/challenge URLs, the published TXT record references and the
    #: cleanup state — **public ACME data only, never the account key, never a DNS
    #: credential**. Written and read through :mod:`app.services.certificate_order`,
    #: which owns the shape; the column is JSONB so the progress a crashed attempt
    #: has to be able to resume from survives the crash (phase5-design.md §5.3's
    #: ``dns_record_ref``, §5.5's stuck-state recovery).
    order_state: Mapped[dict[str, Any]] = json_column()
    #: Which ACME directory this generation's order was created at, as the CA's own
    #: directory URL. Set when the attempt starts (before the material exists) so a
    #: failed or abandoned attempt still says which CA it spoke to, and required by
    #: CHECK from the moment the generation carries material: the API derives
    #: "staging, not publicly trusted" from this and from nothing else
    #: (phase5-design.md §5.4). A generation never changes directory — the URL is
    #: written once per generation, and a retry at a different directory is a new
    #: generation, which is what keeps a staging order from becoming a production
    #: certificate halfway through.
    directory_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    #: Bounded backoff cursors of *this* generation's attempts.
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # --- material (Phase 5.2.2) ----------------------------------------------
    # Everything below is written by issuance (5.3) and read by delivery (5.4).
    # None of it is exposed by a read model: ``certificate.read`` returns
    # metadata, and material leaves the control plane only through a delivery
    # claim response (§7.2), never through this table's serializers.

    #: Fernet(org DEK) of the PKCS#8 private key.
    key_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Fernet(org DEK) of the full chain.
    chain_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: SHA-256 of the leaf DER — display and change detection (bundle identity,
    #: drift), never a decryption oracle.
    fingerprint: Mapped[str | None] = mapped_column(String(FINGERPRINT_LENGTH), nullable=True)
    #: The CA's validity window, copied from the issued material. ``not_after`` is
    #: what the renewal sweep and the expiry monitor reason about.
    not_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    not_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Which organization-DEK generation encrypted the material, so a DEK rotation
    #: can find the rows it must re-encrypt (§6.3) — and so a row states which key
    #: guards it without the key itself being readable. Never a placeholder: the
    #: guard CHECK requires it in every state that has material.
    deke_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    #: When the CA returned the chain.
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: When the CA acknowledged the revocation (``state = REVOKED``).
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: The CA axis, deliberately separate from ``state`` (§2.2): the
    #: security-relevant step (stop serving this material) is never gated on the
    #: CA answering, so a ``REVOCATION_FAILED`` generation can still be superseded
    #: and removed from every node.
    revocation_state: Mapped[CertificateRevocationState] = mapped_column(
        String(24),
        default=CertificateRevocationState.NOT_REQUESTED,
        nullable=False,
        server_default=CertificateRevocationState.NOT_REQUESTED.value,
    )
    #: Generation-level suspension: a shared generation may be suspended for some
    #: of its identifiers only (§9.3). Set and cleared together, like the
    #: certificate's pair.
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspension_reason: Mapped[str] = mapped_column(String(64), default="", nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<CertificateGeneration #{self.generation} {self.state}>"
