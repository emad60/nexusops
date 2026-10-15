"""Customer DNS credentials — the control-plane-only half of DNS-01.

A **dedicated table**, deliberately not a reuse of anything that already exists
(phase5-design.md §5.3): the deployment-resolvable secret store delivers its
values *to nodes*, so a customer's DNS API token must never live there — putting
it there would conflate "may be delivered to a node" with "control-plane-only
CA/DNS credential". Notification channels have no zone scope and no
``verify_creds``; a generic ``integrations`` table has exactly one consumer.

Ownership and the custody rule:

* the row is ``OrgScoped``, so it participates in the session guard, the RLS
  policies and the explicit ``org_id`` predicates every tenant table uses;
* the credential blob is Fernet(**org DEK**) in ``credentials_ciphertext``. The
  DEK comes from :mod:`app.services.dek_envelope` for the duration of one
  operation and is never cached, so accepting a credential without a working KEK
  provider is impossible rather than merely discouraged (Phase 5.2.2 lands after
  5.2.1's envelope for exactly that reason);
* **no read path returns ``credentials_ciphertext``** — the API exposes metadata
  only (``name``, ``kind``, ``scopes``, ``zone_allowlist``, ``verified_at``,
  ``credential_fingerprint``), asserted by a response-allowlist test, so the
  column cannot leak by default when a new field is added.

``zone_allowlist`` is the second half of the protection: the credential may only
touch the zones listed there, and the check happens **before** any provider call,
so a wrong or over-broad token cannot be used to write records in a zone the
customer did not authorize.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, OrgScoped, TimestampMixin, status_check, uuid_pk
from app.models.enums import DnsProviderKind

#: Longest operator-chosen label for a provider row.
MAX_PROVIDER_NAME = 120

#: How many zones one credential may be allowlisted for. A bound, not a policy:
#: it keeps a runaway write from turning the allowlist into a megabyte of JSON.
MAX_ALLOWLISTED_ZONES = 200

#: Length of a lower-case hex SHA-256. The fingerprint is display + change
#: detection only — never a decryption oracle, and never compared for equality
#: against attacker-supplied input to conclude "the secret is correct".
FINGERPRINT_LENGTH = 64


class DnsProvider(OrgScoped, TimestampMixin, Base):
    """One stored DNS credential plus the scope it is allowed to touch."""

    __tablename__ = "dns_providers"
    __table_args__ = (
        status_check("kind", DnsProviderKind),
        # Names are an operator-facing handle, so they are unique per tenant: two
        # rows called "Cloudflare production" would make every later reference
        # (a certificate's ``dns_provider_id``, an audit entry) ambiguous.
        UniqueConstraint("org_id", "name", name="uq_dns_providers_org_name"),
        CheckConstraint("char_length(name) BETWEEN 1 AND 120", name="name_length"),
        CheckConstraint(
            f"char_length(credential_fingerprint) = {FINGERPRINT_LENGTH}",
            name="credential_fingerprint_length",
        ),
        CheckConstraint(
            "jsonb_typeof(zone_allowlist) = 'array' AND jsonb_array_length(zone_allowlist) <= "
            f"{MAX_ALLOWLISTED_ZONES}",
            name="zone_allowlist_shape",
        ),
        CheckConstraint("jsonb_typeof(scopes) = 'object'", name="scopes_shape"),
        # The credential blob is encrypted under a real DEK generation, so this is
        # never 0: ``0`` means "no DEK yet" at the envelope level. Without it a DEK
        # rotation could not find the rows it has to re-encrypt (§6.3), and the
        # ciphertext's context binding could not be reconstructed.
        CheckConstraint("deke_id >= 1", name="deke_id_positive"),
        Index("ix_dns_providers_org_kind", "org_id", "kind"),
        Index("ix_dns_providers_deke_id", "deke_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    #: Operator label. Not a secret, safe to log and to show in an error.
    name: Mapped[str] = mapped_column(String(MAX_PROVIDER_NAME), nullable=False)
    #: Which API this credential speaks to. A CHECK over :class:`DnsProviderKind`,
    #: so a row can never name a provider the control plane cannot call.
    kind: Mapped[DnsProviderKind] = mapped_column(
        String(32), default=DnsProviderKind.CLOUDFLARE, nullable=False
    )
    #: Fernet(org DEK) of the credential blob. Write-only: set on create/rotate,
    #: read only by the issuance path that has already checked the allowlist.
    credentials_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    #: SHA-256 of the canonical serialization of the *plaintext* blob, so an
    #: operator can tell a rotated credential from the one they pasted before
    #: without the platform being able to reveal it. Display + change detection.
    credential_fingerprint: Mapped[str] = mapped_column(String(FINGERPRINT_LENGTH), nullable=False)
    #: Which organization-DEK generation encrypted ``credentials_ciphertext``.
    #: §6.2 requires it "on each ciphertext row" (the §3.4 table omits it, which
    #: §6.2's rule supersedes): it is the ``deke_id`` a rotation looks for and the
    #: generation the payload's context binding is checked against.
    deke_id: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Provider-declared scope summary as returned by ``verify_creds`` — e.g.
    #: ``{"zone_id": ..., "zone_name": ..., "permissions": ["dns_records:edit"]}``.
    #: Public metadata; never contains the token.
    scopes: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    #: Zones this credential is permitted to touch. A challenge name that is not
    #: covered here is refused before the provider is called.
    zone_allowlist: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    #: Last ``verify_creds()`` result. ``verify_error`` is sanitized and bounded:
    #: it names the failure, never the credential.
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verify_error: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    #: Whether the TXT record is removed once the CA has validated the challenge.
    #: Operator-controlled: a stuck record is visible, and an operator debugging a
    #: DNS problem may legitimately want to keep it.
    auto_cleanup: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default=text("true")
    )
    #: When the issuance path last used this credential (rotated credentials age
    #: out visibly rather than silently).
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<DnsProvider {self.name} {self.kind}>"


__all__ = ["MAX_ALLOWLISTED_ZONES", "MAX_PROVIDER_NAME", "DnsProvider"]
