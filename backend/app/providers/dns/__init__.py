"""The DNS seam: what the control plane needs *from* a DNS API.

Two halves, and the split is deliberate rather than incidental:

* :class:`DnsCredentialProvider` — **credential verification**. ``verify_creds()``
  answers "is this credential usable, and which zones can it see?" It ships with
  credential storage (Phase 5.2.2) and runs on save and before use, so a broken
  token is visible on the provider row instead of surfacing as a failed issuance
  minutes later (phase5-design.md §5.3).
* :class:`DnsRecordProvider` — **issuance operations**: resolve the zone a record
  belongs to, create a TXT record, find one this platform already created, and
  delete it by the reference the create returned. Ship with the DNS-01 flow
  (Phase 5.3) because writing a TXT record is the first thing here that modifies a
  customer's DNS, and because cleanup has to delete *by reference* — "never delete
  every TXT record at a name", and never re-derive the name and hope (§5.3).

The two are separate protocols, obtained from separate functions, so that no
credential-verification call site can acquire the ability to write a record, and so
the existing verification fakes stay valid: a test that only cares about
``verify_creds`` does not have to implement the record operations.

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


# --- The record seam (Phase 5.3) ------------------------------------------------


class DnsProviderError(RuntimeError):
    """A provider call failed. ``code`` is stable; the message is sanitized.

    Sanitized means two things, both load-bearing: no credential value can appear
    in it (the adapter only ever formats statuses, provider codes and record
    names), and no third-party free text is passed through unbounded. This object is
    what becomes a ``last_error`` column, an event payload and an API field.

    ``retryable`` is advice for the attempt budget, not an instruction — the state
    machine still bounds retries.
    """

    #: Whether another attempt at the same operation could plausibly succeed.
    retryable: bool = False

    def __init__(self, message: str, *, code: str, detail: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.code}: {self.message}" + (f" ({self.detail})" if self.detail else "")


class DnsProviderUnavailable(DnsProviderError):
    """The provider could not be reached, or answered with a server-side failure.

    Retryable: a DNS API having a bad minute is the normal case, and a bounded
    retry with backoff is the right response.
    """

    retryable = True


class DnsProviderRejected(DnsProviderError):
    """The provider refused the request as written.

    An invalid token, insufficient permissions, a read-only token, a zone the token
    cannot see, a record the API rejects as malformed. Retrying the same request
    cannot help: an operator has to change the credential or the zone allowlist, and
    the sanitized code says which. (The token is *not* re-verified here — that is
    ``verify_creds``'s job — this is the failure the write itself reported.)
    """

    def __init__(
        self, message: str, *, code: str = "DNS_PROVIDER_REJECTED", detail: str = ""
    ) -> None:
        super().__init__(message, code=code, detail=detail)


class DnsWriteAmbiguous(DnsProviderError):
    """A TXT creation may or may not have happened remotely.

    The case the design calls out explicitly (§5.3, "handle an ambiguous API timeout
    safely"): the request was sent, the response was lost (a timeout, a connection
    reset, a 5xx after the write committed). The record may now exist in the
    customer's zone, so this is **not** a plain retryable failure — retrying blind
    creates a second resource, and the cleanup path would then have no way to know
    which one it made.

    It carries the coordinates recovery needs (:meth:`app.providers.dns.find_txt`)
    and is resolved by observing the zone rather than by guessing. It is therefore
    also deliberately *not* a subclass of :class:`DnsProviderUnavailable`: the
    caller must reconcile before it may retry.
    """

    retryable = False

    def __init__(
        self,
        message: str,
        *,
        code: str = "DNS_WRITE_AMBIGUOUS",
        detail: str = "",
        name: str = "",
        value: str = "",
    ) -> None:
        super().__init__(message, code=code, detail=detail)
        #: The record coordinates, so recovery can look for exactly this record. The
        #: value is public DNS data (it is the ACME challenge value) and the name is
        #: public; neither is a credential.
        self.name = name
        self.value = value


@dataclass(frozen=True, slots=True)
class ZoneRef:
    """One zone a credential can write in, as the provider names it."""

    #: The provider's own identifier. Opaque here on purpose: it is passed back to
    #: the provider and never parsed, compared or predicted.
    id: str
    #: The zone's canonical (lower-case, no trailing dot) name.
    name: str


@dataclass(frozen=True, slots=True)
class ZoneResolution:
    """Which zone holds a record name — or why that could not be established.

    ``zone is None`` is a real outcome with a reason, not an error: a record name
    outside every zone the credential can see is a configuration problem the
    operator has to fix, and the reason says so instead of raising something the
    caller would have to interpret.
    """

    zone: ZoneRef | None
    #: Sanitized, operator-facing explanation when ``zone`` is None.
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.zone is not None


@dataclass(frozen=True, slots=True)
class TxtRecord:
    """A reference to **one** TXT record this platform created.

    The reference, not the name, is what cleanup uses (§5.3), and the difference is
    the whole reason the type exists: a challenge name legitimately holds several
    TXT values at once (``example.com`` and ``*.example.com`` share
    ``_acme-challenge.example.com``), so "delete the TXT record at this name" is not
    a safe operation and this platform never performs it.
    """

    #: The provider's record identifier.
    id: str
    zone_id: str
    #: The record's owner name, as the provider stored it.
    name: str
    #: The TXT value that was written. Public DNS data; kept so recovery can tell
    #: *this* record from a customer's unrelated one at the same name.
    value: str


class DnsRecordProvider(Protocol):
    """One DNS API, seen from the control plane's issuance side.

    Every method takes the decrypted credential as an argument and returns a result;
    none of them stores, caches or logs it. Implementations must be safe to call
    concurrently for different records — the issuance task is per generation, and two
    generations may run at once for the same organization.
    """

    name: str

    async def resolve_zone(self, credentials: Mapping[str, str], name: str) -> ZoneResolution:
        """The zone that holds *name*, or a reason it could not be determined."""
        ...

    async def create_txt(
        self,
        credentials: Mapping[str, str],
        *,
        zone_id: str,
        name: str,
        value: str,
        ttl: int,
    ) -> TxtRecord:
        """Create one TXT record and return its reference.

        Raises :class:`DnsWriteAmbiguous` when the outcome is unknown — never a bare
        transport error, which the caller would reasonably retry.
        """
        ...

    async def find_txt(
        self, credentials: Mapping[str, str], *, zone_id: str, name: str, value: str
    ) -> tuple[TxtRecord, ...]:
        """Every TXT record at *name* whose value equals *value*.

        The reconciliation primitive: after an ambiguous create, the platform can ask
        the zone whether the record it was trying to make exists, and adopt it, rather
        than creating a second one. Filtering by value is what keeps a customer's
        unrelated TXT records at the same name out of the result.
        """
        ...

    async def delete_txt(
        self, credentials: Mapping[str, str], *, zone_id: str, record_id: str
    ) -> bool:
        """Delete one record **by its reference**. Returns whether it is gone.

        ``True`` means "this record is not there any more", including when the
        provider reports it already absent — cleanup that treats "already deleted"
        as failure would retry forever. ``False`` is not a quiet success either: it
        means the record could not be confirmed gone, which the caller records
        truthfully rather than reporting cleanup as complete.
        """
        ...


def _provider_class(kind: DnsProviderKind | str) -> type:
    """The implementation class for *kind*. Explicit mapping; unknown ⇒ hard error.

    Imported inside the function rather than at module scope so the seam stays
    importable (and testable with a fake) without pulling in an HTTP client.
    """
    resolved = DnsProviderKind(kind)
    if resolved is DnsProviderKind.CLOUDFLARE:
        from app.providers.dns.cloudflare import CloudflareDnsProvider

        return CloudflareDnsProvider
    raise DnsCredentialError(  # pragma: no cover - unreachable while the enum is one member
        f"no DNS provider is implemented for kind {resolved!r}",
        code="DNS_PROVIDER_KIND_UNSUPPORTED",
    )


def provider_for(kind: DnsProviderKind | str) -> DnsCredentialProvider:
    """The credential-verification implementation for *kind*.

    Separate from :func:`records_provider_for` rather than one object doing both: a
    call site that verifies a credential has no business holding a method that writes
    a record. This is the function the existing verification path and its fakes use,
    and it keeps working unchanged for a fake that implements only ``verify_creds``.
    """
    return _provider_class(kind)()


def records_provider_for(kind: DnsProviderKind | str) -> DnsRecordProvider:
    """The issuance-operations implementation for *kind*.

    The one function that yields the ability to modify a customer's DNS. It is called
    from the issuance path only, with a credential that has already passed the zone
    allowlist check — the flow's ordering, not this function's, is what makes that
    true, which is why the check lives in the service and runs before this is ever
    reached.
    """
    return _provider_class(kind)()


__all__ = [
    "CredentialCheck",
    "DnsCredentialError",
    "DnsCredentialProvider",
    "DnsProviderError",
    "DnsProviderRejected",
    "DnsProviderUnavailable",
    "DnsRecordProvider",
    "DnsWriteAmbiguous",
    "TxtRecord",
    "ZoneRef",
    "ZoneResolution",
    "provider_for",
    "records_provider_for",
]
