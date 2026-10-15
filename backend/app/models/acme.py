"""The per-organization ACME account and its protected account key.

One account per **organization per directory** (phase5-design.md §5.4): staging
and production are separate accounts, and the tenant boundary is the account
boundary. The rationale is blast radius, not tidiness — a shared platform account
would let one tenant's issuance exhaust another tenant's rate-limit budget, and
would make every revocation the platform's problem to attribute.

The account key pair is generated control-plane-side and stored
Fernet(**org DEK**) in ``key_ciphertext``, exactly like a DNS credential and like
the certificate material that arrives with it in this slice. Three consequences
the schema states rather than leaves to a comment:

* ``deke_id`` is **NOT NULL** here, and it means what it means on
  ``certificate_generations``: which organization-DEK generation encrypted this
  blob, so a DEK rotation can find the row again (§6.3). Unlike a certificate
  generation — which legitimately exists before any material does — an account row
  only ever exists *with* a key, so there is no nullable-pre-issuance case to
  accommodate and the bound ``deke_id >= 1`` is unconditional (``0`` means "no DEK
  yet" and is never a generation that encrypted anything).
* the account key never reaches ``order_state``, a log, an event or an API read
  model. ACME *order* data (challenge URLs, key authorizations, DNS record
  references) is public and belongs on the generation; the account key is the
  credential that signs for the tenant and lives only here.
* ``directory_url`` is stored per row rather than inferred from the environment, so
  a staging-issued certificate can be recognized as staging from its own record —
  the API exposes the directory with the certificate and the UI labels it (§5.4's
  "no silent fallback" rule, enforced at the data level instead of by convention).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, OrgScoped, TimestampMixin, status_check, uuid_pk
from app.models.enums import AcmeDirectory, CertificateKeyAlgorithm

#: Longest directory URL we store. ACME directories are well under this; the bound
#: exists so a malformed or hostile value cannot be used as a storage amplifier.
MAX_DIRECTORY_URL = 255

#: The account's own URL at the CA (the ``kid`` the JWS is signed with). Longer
#: than a directory URL because it carries the account identifier.
MAX_ACCOUNT_URL = 512


class AcmeAccount(OrgScoped, TimestampMixin, Base):
    """One ACME account: its directory, its CA-side URL, and its wrapped key."""

    __tablename__ = "acme_accounts"
    __table_args__ = (
        status_check("key_algorithm", CertificateKeyAlgorithm),
        # The identity of an account is (organization, directory). Staging and
        # production are two rows, and a duplicate registration for the same pair
        # is a database error rather than a second account at the CA.
        UniqueConstraint("org_id", "directory_url", name="uq_acme_accounts_org_directory"),
        CheckConstraint(
            f"char_length(directory_url) BETWEEN 8 AND {MAX_DIRECTORY_URL}",
            name="directory_url_length",
        ),
        CheckConstraint(
            "char_length(key_fingerprint) = 64",
            name="key_fingerprint_length",
        ),
        # A row without a wrapped key would promise an account the control plane
        # cannot sign for. The DEK generation is mandatory for the same reason:
        # without it a rotation cannot find the row it has to re-encrypt.
        CheckConstraint("deke_id >= 1", name="deke_id_positive"),
        Index("ix_acme_accounts_org_id_created", "org_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    #: The ACME directory this account is registered at. Explicit configuration,
    #: never inferred from ``ENVIRONMENT``: a production issuance that finds no
    #: production configuration fails closed instead of quietly minting a staging
    #: certificate (phase5-design.md §5.4).
    directory_url: Mapped[str] = mapped_column(String(MAX_DIRECTORY_URL), nullable=False)
    #: The CA's account URL, which becomes the JWS ``kid``. NULL until the account
    #: is actually registered (5.3); the row is created by the same code path that
    #: registers it, so it is populated by the time anything signs with it.
    account_url: Mapped[str | None] = mapped_column(String(MAX_ACCOUNT_URL), nullable=True)
    #: Fernet(org DEK) of the account key pair. Write-only; no read model exposes it.
    key_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    #: SHA-256 of the account key's canonical public serialization — display and
    #: change detection, never a decryption oracle.
    key_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    #: Which organization-DEK generation encrypted ``key_ciphertext`` (§6.3).
    deke_id: Mapped[int] = mapped_column(Integer, nullable=False)
    #: The key type generated for this account. Fixed in v1 and never
    #: client-chosen, so a caller cannot request a key the JWS path does not sign.
    key_algorithm: Mapped[CertificateKeyAlgorithm] = mapped_column(
        String(16), default=CertificateKeyAlgorithm.ECDSA_P256, nullable=False
    )
    #: When the issuance path last used this account.
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def directory(self) -> AcmeDirectory | None:
        """Which known directory this account is at; ``None`` when the URL is neither.

        Read from the stored URL rather than from a second column, so a row cannot
        disagree with itself about which CA it belongs to. ``None`` is a real
        answer — a hand-edited or future-CA URL — and it is reported as unknown
        rather than being coerced into staging or production.
        """
        return AcmeDirectory.from_url(self.directory_url)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AcmeAccount {self.directory_url}>"


__all__ = ["MAX_ACCOUNT_URL", "MAX_DIRECTORY_URL", "AcmeAccount"]
