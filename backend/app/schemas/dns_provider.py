"""DNS credential schemas — metadata-only reads, write-only secret.

The asymmetry is the point (phase5-design.md §3.4): a caller may send a credential
and may read everything *about* it, but no response model here has a field a
credential value could occupy. ``DnsProviderOut`` enumerates the approved fields
rather than dumping the row, so the ciphertext column cannot leak by default when
someone adds a column to the model — the failure mode this shape exists to prevent.

``credential_fingerprint`` is what an operator sees instead of the token: a stable,
non-reversible handle that answers "is this the credential I pasted before?" and
"did it change?" without the platform ever being able to reveal it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.dns_provider import MAX_ALLOWLISTED_ZONES, MAX_PROVIDER_NAME
from app.models.enums import DnsProviderKind
from app.schemas.base import APIModel, OutModel


class DnsProviderCreate(APIModel):
    """Payload for ``POST /dns-providers``.

    ``credentials`` is a provider-shaped blob (``{"api_token": "..."}`` for
    Cloudflare) validated by that provider before anything is stored: an incomplete
    credential is a 422, never a row that fails later during issuance. The value is
    never echoed, never logged and never returned.
    """

    name: str = Field(min_length=1, max_length=MAX_PROVIDER_NAME)
    kind: str = DnsProviderKind.CLOUDFLARE.value
    #: The credential blob. Bounded by the service (field count and value length) so
    #: it cannot be used as a storage amplifier.
    credentials: dict[str, str] = Field(min_length=1)
    #: Zones this credential may write TXT records in. An empty list authorizes
    #: nothing — the fail-closed reading, chosen deliberately over "no allowlist
    #: means no restriction".
    zone_allowlist: list[str] = Field(default_factory=list, max_length=MAX_ALLOWLISTED_ZONES)
    #: Whether the challenge TXT record is removed once the CA has validated it.
    auto_cleanup: bool = True


class DnsProviderUpdate(APIModel):
    """Payload for ``PATCH /dns-providers/{id}``. Every field is optional.

    Sending ``credentials`` **rotates** the stored secret in place and resets the
    verification result, because the old result described a different value. Sending
    ``null`` for a field is not a value and is ignored, so a partial update cannot
    erase a field by omission.
    """

    name: str | None = Field(default=None, min_length=1, max_length=MAX_PROVIDER_NAME)
    credentials: dict[str, str] | None = None
    zone_allowlist: list[str] | None = Field(default=None, max_length=MAX_ALLOWLISTED_ZONES)
    auto_cleanup: bool | None = None


class DnsProviderOut(OutModel):
    """DNS credential read model. **Metadata only — never the credential.**"""

    updated_at: datetime
    name: str
    #: Which DNS API this credential speaks to.
    kind: DnsProviderKind
    #: Provider-declared, public scope summary from the last verification.
    scopes: dict[str, Any] = Field(default_factory=dict)
    #: Zones this credential may touch. The allowlist as stored, canonical.
    zone_allowlist: list[str] = Field(default_factory=list)
    #: A stable, non-reversible handle for the credential. Display and change
    #: detection only; it is never compared against caller input to decide that a
    #: secret is correct.
    credential_fingerprint: str
    #: Which organization-DEK generation encrypted the credential, so an operator can
    #: see which rows a DEK rotation still has to revisit.
    deke_id: int
    #: Last verification outcome. ``verify_error`` is sanitized and bounded, and
    #: names the failure rather than the credential.
    verified_at: datetime | None = None
    verify_error: str = ""
    auto_cleanup: bool = True
    last_used_at: datetime | None = None
