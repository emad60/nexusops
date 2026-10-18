"""The ACME seam: everything issuance needs *from* a certificate authority.

One implementation ships in this slice (:mod:`app.services.acme.library`, wrapping
the maintained ``acme`` package) and **nothing else in the codebase imports that
package**. The seam exists for three reasons worth stating rather than assuming:

1. **The flow is testable without a CA.** The issuance service drives an
   :class:`AcmeSession` — create order, publish, answer, finalize — so the whole
   state machine, the attempt accounting and the persistence ordering can be
   exercised against a fake that returns a real chain. Without this seam the only
   honest test would be a Pebble container, and every failure-path test would then
   need a CA that fails on demand.
2. **Failures are classified once.** A CA answers with an RFC 7807 problem
   document whose ``type`` is an authority-issued code (``caa``, ``rateLimited``,
   ``dns``, ``rejectedIdentifier``, …). That code — not a parsed message, not an
   HTTP status guess — is what decides whether an attempt failed retryably,
   exhausted its budget or must stop. :func:`classify_error` is the only classifier,
   and it lives here so the worker cannot invent a second opinion.
3. **The account key stays in one place.** It is decrypted for an attempt, handed
   to :func:`open_acme_session`, and dropped when the session closes. No other
   signature in the codebase takes it.

What this module deliberately does **not** do: implement RFC 8555, build JWS,
track nonces, or handle key rollover. Those are the library's job, and a
hand-rolled JWS is how a platform signs a request with a key it should not have.

The dataclasses here carry **public ACME data only** — order and challenge URLs, a
token, the TXT record name and value the challenge will be published at. None of
them can carry the account key, a certificate key or a DNS credential, because none
of those are fields.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.models.enums import AcmeDirectory

#: Longest CA-supplied detail we keep. Bounded because it is third-party text that
#: ends up in a column a human reads, and an error message is not a place for a
#: certificate transparency log.
MAX_ERROR_DETAIL = 300

#: Control characters (including newlines) are stripped from stored detail: a
#: multi-line CA message would otherwise be a small injection into a log line and
#: into the API's ``last_error`` field.
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]+")
_WHITESPACE = re.compile(r"\s+")


class AcmeError(RuntimeError):
    """Base class for every ACME failure this platform recognizes.

    ``code`` is stable and sanitized (an operator-facing identifier, never CA free
    text); ``retryable`` says whether *another attempt on this generation* could
    plausibly succeed. It is advice for the state machine, not an instruction: the
    attempt budget still bounds retries, and nothing here can make a generation
    terminal on its own.
    """

    #: Whether a later attempt on the same generation may succeed.
    retryable: bool = False

    def __init__(self, message: str, *, code: str, detail: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.detail = sanitize_detail(detail) if detail else ""

    def __str__(self) -> str:
        return f"{self.code}: {self.message}" + (f" ({self.detail})" if self.detail else "")


class AcmeConfigError(AcmeError):
    """The platform's own configuration or custody is wrong.

    Never retryable: an attempt that failed here would fail identically, and a
    retry would spend budget on a bug. Reaching a production directory from a
    non-production environment is the case this exists for.
    """

    def __init__(
        self, message: str, *, code: str = "ACME_CONFIG_INVALID", detail: str = ""
    ) -> None:
        super().__init__(message, code=code, detail=detail)


class AcmeRejected(AcmeError):
    """The CA refused this request as written; retrying the same request cannot help.

    ``unauthorized``, ``rejectedIdentifier``, ``caa``, ``badCSR``, ``dnssec`` and
    ``malformed`` all land here. The distinction that matters downstream is
    :attr:`AcmeError.retryable` — an operator has to change something (a CAA
    record, the identifiers, the DNS provider's permissions) before this can
    succeed, and the sanitized code tells them which.
    """


class AcmeUnavailable(AcmeError):
    """A transient failure: the CA could not be reached, or could not reach us.

    ``serverInternal``, ``connection``, ``dns``, ``tls``, ``unknownHost`` and
    plain transport timeouts. Retryable within the generation's budget — with the
    caveat the design states: a *serving* failure (the CA could not reach the
    authoritative nameserver) is often the customer's DNS still propagating, which
    is exactly what a bounded retry with backoff is for.
    """

    retryable = True


class AcmeRateLimited(AcmeUnavailable):
    """The CA is rate limiting this account.

    Retryable, and separated from the other transient failures because the CA's
    ``Retry-After`` (when it sends one) must be honored exactly rather than the
    platform's own backoff formula.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "ACME_RATE_LIMITED",
        detail: str = "",
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message, code=code, detail=detail)
        self.retry_after_seconds = retry_after_seconds


class AcmeTimeout(AcmeError):
    """An attempt's own wall-clock deadline passed.

    Our deadline, not the CA's verdict: the challenge may still validate. Retryable
    — and the reason every wait in this subsystem is bounded by a deadline that a
    worker's soft time limit can contain.
    """

    retryable = True


class AcmeProtocolError(AcmeError):
    """The response was not a well-formed ACME answer.

    A missing ``Location`` on an account the CA just created, a challenge that is
    not ``dns-01``, an order with no finalize URL. Not retryable as-is: the same
    request would get the same malformed answer, and a retry loop against a broken
    CA is how a rate limit is reached.
    """

    def __init__(
        self, message: str, *, code: str = "ACME_PROTOCOL_ERROR", detail: str = ""
    ) -> None:
        super().__init__(message, code=code, detail=detail)


def sanitize_detail(detail: str) -> str:
    """Bound and flatten third-party text before it is stored or displayed.

    The CA's ``detail`` is the most useful thing in a failure and the least
    trustworthy: it is free text from a remote service that ends up in a database
    column, an event payload and an API response. So it is flattened (no control
    characters, no newlines), whitespace-collapsed and truncated — never re-quoted,
    never interpolated into a format string.
    """
    collapsed = _WHITESPACE.sub(" ", _CONTROL_CHARS.sub(" ", detail or "")).strip()
    return collapsed[:MAX_ERROR_DETAIL]


#: The CA error codes this platform maps to a *rejection* — the request must change.
REJECTION_CODES: frozenset[str] = frozenset(
    {
        "badCSR",
        "badPublicKey",
        "badSignatureAlgorithm",
        "caa",
        "dnssec",
        "invalidContact",
        "malformed",
        "rejectedIdentifier",
        "unauthorized",
        "unsupportedContact",
        "unsupportedIdentifier",
        "alreadyRevoked",
        "badRevocationReason",
        "accountDoesNotExist",
        "externalAccountRequired",
    }
)

#: Transient codes: the CA or the DNS it consulted failed this time.
TRANSIENT_CODES: frozenset[str] = frozenset(
    {"connection", "dns", "serverInternal", "tls", "unknownHost", "badNonce"}
)


def classify_error(error_code: str, detail: str = "") -> AcmeError:
    """Turn a CA-issued error code into the failure class it belongs to.

    The input is the problem document's ``type`` suffix (``caa``, ``rateLimited``)
    if we have one, or a code the library itself compares against. Unknown codes
    become a *retryable* transient failure only when they arrived as a server-side
    error — an unrecognized code is not evidence the request was wrong, and
    treating it as a rejection would strand a generation that a retry would fix.
    """
    code = (error_code or "").strip()
    if code == "rateLimited":
        return AcmeRateLimited(
            "the certificate authority is rate limiting this account",
            code="ACME_RATE_LIMITED",
            detail=detail,
        )
    if code in REJECTION_CODES:
        return AcmeRejected(
            f"the certificate authority refused the request ({code})",
            code=f"ACME_{code.upper()}",
            detail=detail,
        )
    if code in TRANSIENT_CODES:
        return AcmeUnavailable(
            f"the certificate authority could not complete the request ({code})",
            code=f"ACME_{code.upper()}",
            detail=detail,
        )
    return AcmeUnavailable(
        "the certificate authority returned an unrecognized error",
        code="ACME_UNCLASSIFIED",
        detail=detail,
    )


@dataclass(frozen=True, slots=True)
class AcmeChallenge:
    """One ``dns-01`` challenge, resolved to what has to be published.

    Every field is public by construction: ``record_value`` is published in DNS and
    ``token`` is handed to the CA in the clear. The account key that *derives*
    ``record_value`` is not here and is not derivable from it.
    """

    #: The identifier the CA is authorizing. The CA strips the wildcard prefix, so
    #: this is ``example.com`` for both ``example.com`` and ``*.example.com``.
    identifier: str
    #: Whether the CA marked the authorization as a wildcard one.
    wildcard: bool
    authorization_url: str
    challenge_url: str
    token: str
    #: ``_acme-challenge.<identifier>`` — built by the library's own DNS01 helper.
    record_name: str
    #: base64url(SHA-256(key authorization)) — the TXT value.
    record_value: str
    #: ``keyAuthorization``, kept because it is what the CA expects in the answer
    #: body and what a human debugging the flow compares against.
    key_authorization: str
    status: str


@dataclass(frozen=True, slots=True)
class AcmeOrder:
    """A fresh order and its authorizations, as public data."""

    order_url: str
    status: str
    challenges: tuple[AcmeChallenge, ...]
    expires_at: datetime | None = None
    #: Identifiers the CA accepted, in CA order. Compared against the requested
    #: list: an order that authorizes *more* than was asked for is refused.
    identifiers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AuthorizationState:
    """One authorization's status after a poll."""

    status: str
    #: CA-issued error code when the authorization failed (``caa``, ``dns`` …).
    error_code: str = ""
    error_detail: str = ""
    #: Seconds the CA's ``Retry-After`` asked for, if it sent one.
    retry_after_seconds: float | None = None

    @property
    def pending(self) -> bool:
        return self.status == "pending"

    @property
    def valid(self) -> bool:
        return self.status == "valid"

    @property
    def invalid(self) -> bool:
        return self.status == "invalid"


@dataclass(frozen=True, slots=True)
class IssuedChain:
    """What finalization returned: PEM chain text plus nothing else.

    The chain is public material (it is served to browsers); the private key that
    matches it is never part of this object — it lives in the caller's frame and is
    encrypted before it is stored.
    """

    fullchain_pem: str
    order_url: str
    #: The CA's own ``notBefore``/``notAfter`` are read from the leaf by the caller;
    #: not duplicated here, so there is exactly one parse of the material.
    metadata: dict[str, Any] = field(default_factory=dict)


class AcmeSession(Protocol):
    """One attempt's conversation with a CA, for one account.

    Method calls are sequential and each is awaited before the next. Implementations
    may hold per-attempt state (the account handle, the order resource, the nonce
    pool); they must not hold anything that outlives the attempt, and they must
    never write the account key anywhere.
    """

    directory: AcmeDirectory

    async def register_account(self, *, contact_email: str | None = None) -> str:
        """Register (or discover) this account and return its CA-side URL (``kid``)."""
        ...

    async def create_order(self, *, csr_pem: bytes, identifiers: tuple[str, ...]) -> AcmeOrder:
        """Create an order for *identifiers* and return its authorizations."""
        ...

    async def resume_order(self, *, order_url: str) -> AcmeOrder:
        """Re-open an order this session did not create, by its recorded URL.

        The manual DNS-01 path needs it: the attempt that placed the order is not
        the attempt that finalizes it, because an operator publishes the challenge
        record in between. What comes back is the CA's current view of the same
        order — same challenge URLs, same tokens — so an answer the operator was
        already handed stays the answer the CA expects.
        """
        ...

    async def accept_challenge(self, *, challenge_url: str) -> None:
        """Tell the CA a challenge is ready to be validated."""
        ...

    async def poll_authorization(
        self, *, authorization_url: str, timeout_seconds: float
    ) -> AuthorizationState:
        """Poll one authorization until it is not ``pending``, or the deadline passes."""
        ...

    async def finalize_order(self, *, csr_pem: bytes, timeout_seconds: float) -> IssuedChain:
        """Finalize the current order and download the issued chain."""
        ...

    async def close(self) -> None:
        """Drop the account key and any transport state this session held."""
        ...


class AcmeProvider(Protocol):
    """The one thing the flow needs from a CA implementation: a session."""

    directory: AcmeDirectory

    def open_session(
        self, *, account_key_pem: str, account_url: str | None
    ) -> AbstractAsyncContextManager[AcmeSession]: ...


def provider_for(directory: AcmeDirectory) -> AcmeProvider:
    """The ACME implementation for *directory*.

    An explicit mapping with one entry, exactly like the DNS-provider seam: no
    discovery, no import-by-name, no fallback. All three directories use the same
    maintained client — that is the point of ``AcmeDirectory`` carrying its URLs —
    so the mapping exists to keep the seam explicit rather than to dispatch
    behavior.
    """
    from app.services.acme.library import LibraryAcmeProvider

    return LibraryAcmeProvider(directory)


#: The shape the issuance service depends on, so a test can substitute a fake
#: without touching this module's internals.
SessionFactory = Callable[..., AbstractAsyncContextManager[AcmeSession]]


def open_acme_session(
    *, directory: AcmeDirectory, account_key_pem: str, account_url: str | None
) -> AbstractAsyncContextManager[AcmeSession]:
    """Open one attempt's ACME session. The only entry point issuance uses."""
    return provider_for(directory).open_session(
        account_key_pem=account_key_pem, account_url=account_url
    )


__all__ = [
    "MAX_ERROR_DETAIL",
    "REJECTION_CODES",
    "TRANSIENT_CODES",
    "AcmeChallenge",
    "AcmeConfigError",
    "AcmeError",
    "AcmeOrder",
    "AcmeProtocolError",
    "AcmeProvider",
    "AcmeRateLimited",
    "AcmeRejected",
    "AcmeSession",
    "AcmeTimeout",
    "AcmeUnavailable",
    "AuthorizationState",
    "IssuedChain",
    "SessionFactory",
    "classify_error",
    "open_acme_session",
    "provider_for",
    "sanitize_detail",
]
