"""The DNS-credential seam: what the control plane needs *from* a DNS API.

Phase 5.2.2 ships exactly one thing through this seam: **credential
verification**. ``verify_creds()`` answers "is this credential usable, and which
zones can it see?" — it is run on save and again before use, so a broken token is
visible on the provider row instead of surfacing as a failed issuance minutes
later (phase5-design.md §5.3).

The three record methods the DNS-01 flow needs (``create_txt``, ``delete_txt``,
``propagation_check``) are deliberately **not** here. They belong to the issuance
slice: writing TXT records is the first thing in this platform that modifies a
customer's DNS, so it ships with the order/challenge flow that owns the record
reference used for cleanup (§5.3 — "cleanup deletes by that reference, not by
re-deriving the name"), not with credential storage.

What this module is *not*: a plugin registry. There is one implementation per
:class:`~app.models.enums.DnsProviderKind`, selected by an explicit mapping, with
no discovery, no import-by-name and no fallback.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.models.enums import DnsProviderKind


class DnsCredentialError(ValueError):
    """The credential blob is malformed for its provider kind.

    Raised before anything is stored: a credential missing ``api_token`` is the
    caller's mistake (a 422), not a provider outage to record on the row.
    """

    def __init__(self, message: str, *, code: str = "DNS_CREDENTIAL_INVALID") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(frozen=True, slots=True)
class CredentialCheck:
    """What a verification attempt learned. Never carries the credential.

    ``ok`` is the only field a caller may branch on for authority. ``scopes`` is
    provider-declared, public metadata that is shown to the operator and stored on
    the row; ``warnings`` are observations that are useful but not failures — a
    zone the operator allowlisted that this token cannot actually see is the
    common one, and it is far better surfaced here than mid-issuance.
    """

    ok: bool
    scopes: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    error: str = ""


class DnsCredentialProvider(Protocol):
    """One DNS API, seen from the control plane's credential side."""

    name: str
    #: Credential keys this provider requires. Validated before storage, so an
    #: incomplete blob never reaches the database.
    required_fields: tuple[str, ...]

    async def verify_creds(self, credentials: Mapping[str, str]) -> CredentialCheck: ...


def provider_for(kind: DnsProviderKind | str) -> DnsCredentialProvider:
    """The implementation for *kind*. Explicit mapping; unknown ⇒ a hard error."""
    resolved = DnsProviderKind(kind)
    if resolved is DnsProviderKind.CLOUDFLARE:
        # Imported here rather than at module scope so the seam stays importable
        # (and testable with a fake) without pulling in an HTTP client.
        from app.providers.dns.cloudflare import CloudflareDnsProvider

        return CloudflareDnsProvider()
    raise DnsCredentialError(  # pragma: no cover - unreachable while the enum is one member
        f"no DNS credential provider is implemented for kind {resolved!r}",
        code="DNS_PROVIDER_KIND_UNSUPPORTED",
    )


__all__ = [
    "CredentialCheck",
    "DnsCredentialError",
    "DnsCredentialProvider",
    "provider_for",
]
