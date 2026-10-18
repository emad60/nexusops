"""One generation's issuance: order → publish → prove → validate → store.

This module is the only place that turns a *request* into certificate material, and
everything it does is ordered so that a failure leaves the platform able to say what
happened and to try again without stranding anything in a customer's DNS:

1. **Leftovers first.** An attempt's very first act is to delete the challenge
   records an earlier attempt of the same generation created and could not confirm
   gone (:meth:`_Attempt.cleanup`). Cleaning up before publishing is what keeps a
   replaced order's value from coexisting with the new one at the same name, and it
   is the same code path a failure runs, so cleanup cannot be the step that only
   happens on the happy path.
2. **A fresh key and a fresh order per attempt.** An attempt *cannot* resume an
   earlier order: the CSR is bound to a private key that exists only in this
   process, and persisting that key across attempts so an order could be resumed
   would mean storing material for a generation that has not been issued — exactly
   what the material guard CHECK forbids (§5.2.2). So an attempt re-orders, and
   :func:`app.services.certificate_order.reset_challenges` replaces the previous
   order's entries while keeping every reference to a record that still has to be
   deleted.
3. **The attempt is stamped before it does anything, and the stamp is durable.**
   A live state (``ORDERING`` … ``VALIDATING``) says a generation has an open order;
   it does not say a worker is running it. The document's attempt pair is what makes
   that answerable, and it is checkpointed — committed, not merely flushed — for the
   same reason: a second worker's transaction has to be able to see it.
4. **Nothing is written that the CA has not answered for.** The generation moves to
   ``ISSUED`` only after a chain is downloaded, parsed, matched against this
   attempt's own key and identifier list, and encrypted under the organization DEK —
   all in this frame, all before the state moves. There is no window in which a row
   claims to have material it does not have.

**Durability.** Every step whose loss would strand something is made durable with a
checkpoint (the worker's ``commit``) rather than a bare flush: the attempt stamp, the
order document, each published record reference, the failure record and the issued
material. A worker killed at any point therefore leaves a row that says which state
it reached, which records it created, and — when it reached none of them — that it
was attempted at all. The checkpoint is a parameter because the transaction belongs
to the caller: a request-scoped caller passes nothing and gets flush semantics, the
worker passes its session's commit.

**What this module deliberately does not do.** It never serves, delivers or installs
the material (§5.4), never renews (§5.6), never revokes (§9.5), and never orders an
identifier set other than the one the certificate records. It also does not retry
*within* an attempt: one attempt is one bounded conversation, and the bounded
backoff in :mod:`app.services.certificate_lifecycle` decides what happens next. The
one exception is the CA's own ``Retry-After``, honored exactly where the client
surfaces it — the platform's backoff never shortens it.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.config import Settings, get_settings
from app.core.dnsname import InvalidName, canonicalize_name
from app.core.errors import AppError, Conflict
from app.core.logging import get_logger
from app.models import Certificate, CertificateGeneration, DnsProvider, Domain
from app.models.enums import (
    AcmeDirectory,
    ActorType,
    CertificateDnsMode,
    CertificateGenerationState,
    DnsProviderKind,
    DomainStatus,
    EventLevel,
)
from app.providers.dns import (
    DnsProviderError,
    DnsRecordProvider,
    DnsWriteAmbiguous,
    TxtRecord,
    records_provider_for,
)
from app.services import (
    acme_account_service,
    alert_service,
    audit_service,
    certificate_lifecycle,
    certificate_order,
    certificate_service,
    dns_propagation,
    event_bus,
    payload_crypto,
)
from app.services.acme import (
    AcmeError,
    AcmeOrder,
    AcmeRateLimited,
    AcmeSession,
    IssuedChain,
    SessionFactory,
    classify_error,
    open_acme_session,
)
from app.services.acme.directory import (
    AcmeDirectoryError,
    directory_for_settings,
    directory_for_url,
)
from app.services.acme_account_service import AcmeAccountKeyUnavailable
from app.services.dek_envelope import org_dek_context
from app.services.dns_provider_service import (
    DnsCredentialUnavailable,
    credentials_for_use,
    require_zone_allowed,
)
from app.services.enqueue import after_commit
from app.services.payload_crypto import (
    PURPOSE_CERTIFICATE_CHAIN,
    PURPOSE_CERTIFICATE_KEY,
    PayloadContext,
    PayloadError,
    encrypt,
)

log = get_logger("nexusops.certificate_issuance")

# --- Refusal codes -------------------------------------------------------------
#
# Every way an attempt stops without a certificate is one of these, or a code the
# ACME seam already classifies. They are stable identifiers an operator can act on;
# the message next to one is prose, and only the code is contractual.

#: The certificate's domain or its stored names are unusable.
CODE_CONTEXT_INCOMPLETE = "CERTIFICATE_CONTEXT_INCOMPLETE"
#: The certificate has no DNS credential to publish a challenge with.
CODE_DNS_CREDENTIAL_MISSING = "CERTIFICATE_DNS_CREDENTIAL_MISSING"
#: The domain is no longer verified, so DNS-01 for its names must not proceed.
CODE_DOMAIN_NOT_VERIFIED = "DOMAIN_NOT_VERIFIED"
#: The generation's recorded directory is not the directory configured now.
CODE_DIRECTORY_CHANGED = "CERTIFICATE_DIRECTORY_CHANGED"
#: The CA accepted an identifier set other than the one the certificate requests.
CODE_ORDER_MISMATCH = "CERTIFICATE_ORDER_MISMATCH"
#: The order document is missing something the attempt needs to act on.
CODE_ORDER_LOST = "CERTIFICATE_ORDER_LOST"
#: The issued chain does not match this attempt's key or identifier list.
CODE_MATERIAL_MISMATCH = "CERTIFICATE_MATERIAL_MISMATCH"
#: The order document was written by a version this code cannot read.
CODE_DOCUMENT_UNSUPPORTED = "CERTIFICATE_ORDER_DOCUMENT_UNSUPPORTED"
#: The attempt raised something this module could not classify.
CODE_ATTEMPT_ERROR = "CERTIFICATE_ATTEMPT_ERROR"
#: A dispatch arrived while another worker is running this generation.
CODE_ATTEMPT_IN_FLIGHT = "CERTIFICATE_ATTEMPT_IN_FLIGHT"
#: The generation is scheduled for later, so there is nothing to attempt yet.
CODE_NOT_DUE = "CERTIFICATE_NOT_DUE"
#: The worker that began an attempt stopped without finishing it.
CODE_WORKER_LOST = "CERTIFICATE_WORKER_LOST"
#: No further attempt is possible for this generation.
CODE_ATTEMPTS_EXHAUSTED = "CERTIFICATE_ATTEMPTS_EXHAUSTED"
#: The attempt placed a manual order and stopped: an operator has to publish the
#: DNS-01 record before anything else may happen. Not a failure and not an
#: issuance — the third outcome of a dispatch (:data:`IssuanceAttempt.waiting`).
CODE_AWAITING_MANUAL = "CERTIFICATE_AWAITING_MANUAL"
#: A manual confirmation arrived for a certificate that is not waiting for one.
CODE_MANUAL_NOT_PENDING = "CERTIFICATE_MANUAL_CHALLENGE_NOT_PENDING"
#: A persisted manual challenge cannot be handed to an operator or acted on.
CODE_MANUAL_CHALLENGE_INVALID = "CERTIFICATE_MANUAL_CHALLENGE_INVALID"
#: The CA's order no longer carries the challenges this platform recorded.
CODE_ORDER_SUPERSEDED = "CERTIFICATE_ORDER_SUPERSEDED"

#: ``last_error`` is a bounded column; the failure text respects it here.
_MAX_ERROR_TEXT = 500

#: The identifier bound one order may carry. Matches the request bound, and is a
#: bound rather than a policy: a hand-edited row cannot turn one attempt into an
#: unbounded sequence of DNS writes and CA calls.
MAX_IDENTIFIERS = 100


@dataclass(frozen=True, slots=True)
class IssuanceAttempt:
    """What one call to :func:`issue_generation` did. Never carries material.

    ``code`` is set for every outcome that is not an issuance — including the two
    that are not failures at all (an attempt already in flight, a generation that is
    not due yet). ``ok`` and ``code`` are separate fields rather than one status for
    exactly that reason: a caller that asked for an attempt and got none has to be
    able to tell that apart from one that tried and failed.
    """

    generation_id: Any
    ok: bool
    state: CertificateGenerationState
    attempt: int = 0
    code: str = ""
    message: str = ""
    retryable: bool = False
    terminal: bool = False
    next_attempt_at: datetime | None = None
    #: The attempt stopped because a human has to act (a manual DNS-01 record has
    #: to be published). Distinct from ``ok`` and from every failure: nothing has
    #: gone wrong, and nothing will happen until an operator confirms.
    waiting: bool = False


@dataclass(frozen=True, slots=True)
class _Material:
    """What an attempt produced, described without carrying any of it.

    A value of this type outlives the frame that stored the material, so it holds
    the parsed validity window and the leaf's fingerprint and **never** the key or
    the chain text: nothing here can be logged, cached or serialized into a payload
    that would carry a private key.
    """

    fingerprint: str
    not_before: datetime
    not_after: datetime


class _AttemptFailure(Exception):
    """A classified reason one attempt did not produce a certificate.

    Carries the ACME seam's vocabulary (``code``, ``detail``, ``retryable``) so the
    failure handling has one shape whether the cause was the CA, a DNS provider, a
    credential, or this platform's own preconditions.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str,
        detail: str = "",
        retryable: bool = False,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.detail = detail
        self.retryable = retryable
        #: The CA's own delay, when it sent one: honored *in addition to* the
        #: platform's backoff, never instead of it (see :func:`_scheduled_retry`).
        self.retry_after_seconds = retry_after_seconds

    def text(self) -> str:
        """The operator-facing one-liner stored in ``last_error``. Bounded."""
        text = self.message if not self.detail else f"{self.message} — {self.detail}"
        return text[:_MAX_ERROR_TEXT]


@dataclass(frozen=True, slots=True)
class ManualChallengeStatus:
    """What one manual DNS-01 certificate currently needs from an operator.

    ``document`` is the carrier because the *shape* of an instruction belongs to
    :mod:`app.services.certificate_order`, and the API serialises it through that
    module's helpers rather than this one's. It holds only public ACME data — the
    record name and the TXT value that has to be published — and it is returned
    exactly once per request, only from the two org-scoped challenge endpoints.
    """

    generation_id: Any
    generation: int
    state: CertificateGenerationState
    certificate_id: Any
    document: dict[str, Any]
    #: The identifiers the certificate requests — what the challenge set authorizes,
    #: echoed from the request rather than from the CA's answer.
    identifiers: tuple[str, ...] = ()
    #: Whether this generation is finished with its records: issued, or failed for
    #: good. Only then are the customer's TXT values obsolete, and only then may the
    #: operator be told they can be removed.
    finished: bool = False
    #: The last authoritative observation recorded for this order, if any.
    observation: dict[str, Any] | None = None
    #: Whether a resume attempt was handed to the worker by this call.
    resume_requested: bool = False


# --- Small helpers -------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _dns_mode(certificate: Certificate) -> CertificateDnsMode | None:
    """The certificate's recorded publisher, or ``None`` when it names none.

    ``None`` rather than a default: a stored value this version cannot read must
    never be treated as either mode. Guessing ``automated`` would try to publish a
    customer's record through a credential that may not exist; guessing ``manual``
    would hand an operator instructions for a certificate the platform was supposed
    to publish itself.
    """
    raw = getattr(certificate, "dns_mode", None)
    text = str(getattr(raw, "value", raw) or "")
    for mode in CertificateDnsMode:
        if mode.value == text:
            return mode
    return None


def _actor(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    """Who asked, for the one entry point a human can drive (a manual retry).

    A worker-initiated attempt has no caller and records itself as the system: the
    retry is the operator's act, and everything after it is the platform's.
    """
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


def _aware(value: datetime) -> datetime:
    """*value* with UTC attached when a parser handed back a naive one."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _failure_from(exc: BaseException) -> _AttemptFailure:
    """One classified failure from whatever a step raised.

    The ACME and DNS seams both use ``(message, code, detail, retryable)``; a
    directory refusal carries a code; everything else keeps its own message and is
    **not** marked retryable, because a failure this platform did not classify has
    no evidence saying another attempt would go differently.
    """
    if isinstance(exc, AcmeRateLimited):
        return _AttemptFailure(
            exc.message,
            code=exc.code,
            detail=exc.detail,
            retryable=exc.retryable,
            retry_after_seconds=exc.retry_after_seconds,
        )
    if isinstance(exc, (AcmeError, DnsProviderError)):
        return _AttemptFailure(
            exc.message, code=exc.code, detail=exc.detail, retryable=exc.retryable
        )
    if isinstance(exc, AcmeDirectoryError):
        return _AttemptFailure(exc.message, code=exc.code)
    if isinstance(exc, (DnsCredentialUnavailable, AcmeAccountKeyUnavailable)):
        # Both name a DEK rotation that has not finished. Retryable: the re-encrypt
        # pass rewrites the row, and then this attempt can read its credential.
        return _AttemptFailure(str(exc), code=exc.code, retryable=True)
    if isinstance(exc, PayloadError):
        return _AttemptFailure(str(exc), code="CERTIFICATE_PAYLOAD_ERROR")
    if isinstance(exc, AppError):
        return _AttemptFailure(exc.message, code=exc.code)
    return _AttemptFailure(
        "the attempt failed unexpectedly", code=CODE_ATTEMPT_ERROR, detail=type(exc).__name__
    )


def _scheduled_retry(failure: _AttemptFailure, attempt: int, *, now: datetime) -> datetime | None:
    """When the next attempt is due, or ``None`` once the budget is spent.

    The platform's exponential backoff, extended — never shortened — by the CA's own
    ``Retry-After`` when the client surfaced one. Honoring only the platform's
    formula against a rate limit is how a generation burns its whole budget inside
    the CA's window and ends terminal for no reason.
    """
    if certificate_lifecycle.retry_budget_exhausted(attempt):
        return None
    scheduled = certificate_lifecycle.next_attempt_at(attempt, now=now)
    if failure.retry_after_seconds:
        honored = now + timedelta(seconds=failure.retry_after_seconds)
        if honored > scheduled:
            scheduled = honored
    return scheduled


def _expectations(document: dict[str, Any]) -> tuple[dns_propagation.TxtExpectation, ...]:
    """One TXT expectation per record name the *current* order has to publish.

    Values are grouped by name because one name legitimately holds two challenge
    values (apex and wildcard share ``_acme-challenge.example.com``); entries from a
    replaced order are excluded, since waiting for a value nothing will publish would
    wait out the whole deadline for nothing.
    """
    grouped: dict[str, list[str]] = {}
    for entry in certificate_order.current_entries(document):
        name = str(entry.get("record_name") or "")
        value = str(entry.get("record_value") or "")
        if not name or not value:
            continue
        values = grouped.setdefault(name, [])
        if value not in values:
            values.append(value)
    return tuple(
        dns_propagation.TxtExpectation(name=name, values=tuple(values))
        for name, values in grouped.items()
    )


def _generate_key_and_csr(
    identifiers: tuple[str, ...],
) -> tuple[ec.EllipticCurvePrivateKey, str, bytes]:
    """This attempt's key, its PEM, and the CSR the CA will sign.

    P-256 because the whole delivery path is built for it
    (``CertificateKeyAlgorithm.ECDSA_P256``); the key is generated here and never
    leaves this frame unencrypted.

    The SAN extension carries **every** identifier, including the common name: a CA
    is not required to copy the CN into the SAN, and a certificate covering only part
    of the requested names is refused in :func:`_verify_leaf` rather than at delivery.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    builder = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, identifiers[0])]))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(name) for name in identifiers]),
            critical=False,
        )
    )
    csr = builder.sign(key, hashes.SHA256())
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    return key, key_pem, csr.public_bytes(serialization.Encoding.PEM)


def _leaf_of(fullchain_pem: str) -> x509.Certificate:
    """The leaf of *fullchain_pem*, or a named failure.

    ``fullchain`` is leaf-first by convention and by the client's contract, so the
    first PEM block is the certificate this platform serves. Parsed here rather than
    trusted: every stored fact about the chain (validity window, fingerprint) is
    derived from the parse, so an unparsable answer is a failed attempt instead of a
    row holding material nothing can read.
    """
    begin = "-----BEGIN CERTIFICATE-----"
    end = "-----END CERTIFICATE-----"
    text = fullchain_pem or ""
    if begin not in text or end not in text:
        raise _AttemptFailure(
            "the certificate authority returned no PEM certificate",
            code=CODE_MATERIAL_MISMATCH,
        )
    block = text[text.index(begin) : text.index(end) + len(end)]
    try:
        return x509.load_pem_x509_certificate(block.encode("ascii"))
    except Exception as exc:
        raise _AttemptFailure(
            "the certificate authority returned a certificate that could not be parsed",
            code=CODE_MATERIAL_MISMATCH,
            detail=type(exc).__name__,
        ) from None


def _verify_leaf(
    leaf: x509.Certificate, key: ec.EllipticCurvePrivateKey, identifiers: tuple[str, ...]
) -> None:
    """Refuse a chain that does not answer this attempt's own CSR.

    Two checks, both cheap and both decisive. The public key must be the one this
    attempt generated: a chain for a different key can never be served, and finding
    that out at delivery time would mean shipping a key that cannot sign for the
    certificate. Every requested identifier must be covered by the leaf's SAN or its
    common name: a chain missing one name is one the platform would have to refuse to
    serve after storing it. Both are failures of the *CA's answer*, so both are
    recorded the way any other failed attempt is.
    """
    if leaf.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    ) != key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    ):
        raise _AttemptFailure(
            "the issued certificate does not match the key this attempt generated",
            code=CODE_MATERIAL_MISMATCH,
        )

    covered: set[str] = set()
    try:
        san = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        covered.update(str(name) for name in san.get_values_for_type(x509.DNSName))
    except x509.ExtensionNotFound:
        pass
    try:
        covered.add(str(leaf.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value))
    except IndexError:
        pass
    missing = [name for name in identifiers if name not in covered]
    if missing:
        raise _AttemptFailure(
            "the issued certificate does not cover every identifier that was requested",
            code=CODE_MATERIAL_MISMATCH,
            detail=f"missing: {', '.join(missing[:5])}",
        )


def _identifiers(certificate: Certificate) -> tuple[str, ...]:
    """The order's identifier list: the primary name first, then the SANs.

    Re-canonicalised from the row rather than trusted. The values were canonicalised
    when the request was created, and a stored value that is no longer a valid name —
    a hand-edited row, a name rule that changed — would otherwise be handed to a CA
    and turned into a TXT record name.
    """
    raw = [certificate.primary_cn, *(certificate.sans or [])]
    names: list[str] = []
    for value in raw[:MAX_IDENTIFIERS]:
        try:
            name = canonicalize_name(str(value), allow_wildcard=True)
        except (InvalidName, ValueError) as exc:
            message = getattr(exc, "message", "is not a usable name")
            raise _AttemptFailure(
                f"'{value}' {message}; the certificate cannot be ordered as stored",
                code=CODE_CONTEXT_INCOMPLETE,
            ) from None
        if name not in names:
            names.append(name)
    if not names:
        raise _AttemptFailure(
            "the certificate records no identifier to order", code=CODE_CONTEXT_INCOMPLETE
        )
    return tuple(names)


async def _resolve_context(
    db: AsyncSession,
    generation: CertificateGeneration,
    certificate: Certificate,
    *,
    settings: Settings,
) -> tuple[Domain, DnsProvider | None, dict[str, str], tuple[str, ...], AcmeDirectory]:
    """Everything an attempt needs before it may touch a CA or a customer's zone.

    Resolved *inside* the attempt (never before it is stamped), because a certificate
    whose credential was removed, whose domain lost its proof, or whose directory
    moved is an attempt that failed — and the row has to say so rather than look like
    a dispatch that never happened.

    The DNS credential is resolved **only for automated certificates**. A manual one
    publishes its challenges through the customer, so it needs no credential and is
    refused if it names one: the row would describe two publishers, and picking one
    here would hide that contradiction instead of reporting it.
    """
    domain = await db.get(Domain, certificate.domain_id)
    if domain is None:
        raise _AttemptFailure(
            "the certificate's domain no longer exists", code=CODE_CONTEXT_INCOMPLETE
        )
    if str(getattr(domain.status, "value", domain.status)) != DomainStatus.VERIFIED.value:
        raise _AttemptFailure(
            f"domain '{domain.name}' is no longer verified; DNS-01 cannot be attempted "
            "for a name this organization has not proved control of",
            code=CODE_DOMAIN_NOT_VERIFIED,
        )

    # The certificate names its own credential. An earlier design put one on the
    # Domain too and let a certificate inherit it; no slice ever created that column,
    # so the certificate's reference is the only one that exists and the earlier
    # wording is corrected in phase5-design.md §10.8 rather than guessed at here.
    # A certificate with none is a request that cannot be attempted yet — not a row
    # that quietly signs with a credential nobody selected.
    mode = _dns_mode(certificate)
    if mode is None:
        raise _AttemptFailure(
            "this certificate records no DNS publishing mode this version understands",
            code=CODE_CONTEXT_INCOMPLETE,
        )
    provider_row: DnsProvider | None = None
    credentials: dict[str, str] = {}
    if mode is CertificateDnsMode.MANUAL:
        # The customer publishes; nothing here may reach into their zone. A manual
        # row that still names a credential is refused rather than resolved-and-
        # ignored, because a cleared override and a contradictory row are different
        # facts and only one of them is worth attempting.
        if certificate.dns_provider_id is not None:
            raise _AttemptFailure(
                "this certificate is manual but names a DNS credential; the row describes "
                "two publishers and neither may be chosen for it",
                code=CODE_CONTEXT_INCOMPLETE,
            )
    else:
        if certificate.dns_provider_id is not None:
            provider_row = await db.get(DnsProvider, certificate.dns_provider_id)
        if provider_row is None:
            raise _AttemptFailure(
                "this certificate has no DNS credential: attach one before it can be issued",
                code=CODE_DNS_CREDENTIAL_MISSING,
            )
        # Decrypted once, for this attempt, and passed to the provider calls that
        # need it — nothing stores, caches or logs it.
        credentials = await credentials_for_use(db, provider_row)
    identifiers = _identifiers(certificate)

    selected = directory_for_settings(settings)
    recorded = directory_for_url(generation.directory_url)
    if generation.directory_url and recorded is None:
        raise _AttemptFailure(
            "this generation was ordered at an ACME directory this version does not know",
            code=CODE_DIRECTORY_CHANGED,
        )
    if recorded is not None and recorded is not selected:
        # A generation never changes directory (§3.2): continuing would either sign at
        # a different CA than the row claims or relabel the row. Both are worse than a
        # refusal an operator can act on.
        raise _AttemptFailure(
            f"this generation was ordered at the {recorded.value} directory and issuance is "
            f"now configured for {selected.value}; a retry at a different certificate "
            "authority is a new certificate request",
            code=CODE_DIRECTORY_CHANGED,
        )
    return domain, provider_row, credentials, identifiers, recorded or selected


# --- One attempt ---------------------------------------------------------------


class _Attempt:
    """One attempt at one generation, from the first DNS deletion to the last.

    Owns every write the attempt makes to the generation, the certificate and the
    order document. The orchestration around it decides *whether* to attempt; this
    class decides *what an attempt does*, in the order it does it. The context it
    needs (domain, credential, identifiers, directory) is resolved by :meth:`run`,
    after cleanup, so a broken context is recorded as a failed attempt rather than
    as a dispatch that vanished.
    """

    def __init__(
        self,
        *,
        db: AsyncSession,
        generation: CertificateGeneration,
        certificate: Certificate,
        settings: Settings,
        session_factory: SessionFactory,
        provider_factory: Callable[[DnsProviderKind | str], DnsRecordProvider],
        observer: dns_propagation.Observer | None,
        checkpoint: Callable[[], Awaitable[None]] | None,
        document: dict[str, Any],
        attempt: int,
        now: datetime,
    ) -> None:
        self.db = db
        self.generation = generation
        self.certificate = certificate
        self.settings = settings
        self.session_factory = session_factory
        self.provider_factory = provider_factory
        self.observer = observer
        self.checkpoint = checkpoint
        self.document = document
        self.attempt = attempt
        self.now = now
        # Resolved by run(). "No context" is a state a failed attempt legitimately
        # ends in, which is why these are optional rather than required.
        self.domain: Domain | None = None
        self.provider: DnsProvider | None = None
        self.credentials: dict[str, str] = {}
        self.identifiers: tuple[str, ...] = ()
        self.directory: AcmeDirectory | None = None
        self._api_cache: dict[str, DnsRecordProvider] = {}
        #: Set when the attempt stopped because an operator has to publish a record.
        #: :func:`issue_generation` turns it into a waiting outcome, not a failure.
        self.waiting = False

    # -- durability -----------------------------------------------------------

    def _store(self) -> None:
        certificate_order.store(self.generation, self.document)

    async def _checkpoint(self) -> None:
        """Make everything written so far durable, when the caller says how.

        A flush is not durability: a worker killed after a flush loses the order
        document and every record reference with it, which is exactly the state
        recovery needs. The caller owns the transaction, so the *commit* is passed
        in; the flush always happens, so a request-scoped caller still sees a
        consistent session.
        """
        await self.db.flush()
        if self.checkpoint is not None:
            await self.checkpoint()

    # -- state -----------------------------------------------------------------

    def _transition(self, target: CertificateGenerationState) -> None:
        """Move the generation. An illegal move raises: that is a bug, not a failure."""
        self.generation.state = certificate_lifecycle.require_transition(
            self.generation.state, target
        )
        # The certificate's own status is a denormalized view of exactly this
        # mapping, written here so a worker-initiated move cannot leave the row
        # claiming the state it was in before.
        self.certificate.status = certificate_lifecycle.certificate_status_for(target)

    async def begin(self) -> None:
        """Stamp the attempt as running, durably, and enter ``ORDERING``.

        The stamp is what lets a second dispatch tell "another worker is running
        this" from "the worker that ran this is gone", so it has to be visible to
        another transaction — which is why it is the first thing checkpointed. The
        previous attempt's ``last_error`` is cleared here rather than kept: while an
        attempt is running, the newest fact about the generation is that one is.

        A generation already in ``AWAITING_MANUAL`` stays there. Its attempt is a
        *resume of the order it is waiting on*, and moving the row to ``ORDERING``
        for the duration would say an order is being placed when none is — and a
        worker killed in that window would look like a lost order rather than a
        waiting one. The attempt stamp is what tells the two apart.
        """
        if (
            certificate_lifecycle.coerce_state(self.generation.state)
            is not CertificateGenerationState.AWAITING_MANUAL
        ):
            self._transition(CertificateGenerationState.ORDERING)
        self.generation.attempt_count = self.attempt
        self.generation.next_attempt_at = None
        self.generation.last_error = ""
        self.certificate.last_error = ""
        certificate_order.begin_attempt(self.document)
        self._store()
        await self._checkpoint()

    # -- the flow --------------------------------------------------------------

    async def run(self) -> _Material | None:
        """Drive one attempt to material — or to the point where a human must act.

        ``None`` with :attr:`waiting` set is the manual DNS-01 stop: the order is
        placed, the instructions are stored, and the attempt ends *deliberately*
        because publishing the record is the customer's act (see :meth:`_run_manual`).
        Everything else that returns ``None`` without ``waiting`` is a bug the
        caller records as a failure.
        """
        # (1) Anything an earlier attempt of this generation left behind, deleted
        #     before this attempt publishes anything at the same names. It does not
        #     need the context below, and it must run even when the context turns
        #     out to be unusable — an orphaned record is owed regardless.
        await self.cleanup()
        if self._is_manual():
            return await self._run_manual()
        certificate_order.reset_challenges(self.document)
        self._store()

        (
            self.domain,
            self.provider,
            self.credentials,
            self.identifiers,
            self.directory,
        ) = await _resolve_context(
            self.db, self.generation, self.certificate, settings=self.settings
        )
        directory = self.directory

        account = await acme_account_service.account_for(
            self.db, None, org_id=self.generation.org_id, directory=directory
        )
        key, key_pem, csr_pem = _generate_key_and_csr(self.identifiers)

        # The account key's plaintext exists only as an argument to the session
        # factory and inside the session, which drops it on close: no binding to the
        # tenant's CA credential survives in this frame.
        session = self.session_factory(
            directory=directory,
            account_key_pem=await acme_account_service.account_key(self.db, account),
            account_url=account.account_url,
        )
        chain: IssuedChain | None = None
        async with session as acme:
            await acme_account_service.mark_used(self.db, account)
            if account.account_url is None:
                # First issuance at this directory: the account has a key but no
                # CA-side identity yet, and the order that follows needs one.
                account_url = await acme.register_account(
                    contact_email=self.settings.acme_account_email or None
                )
                await acme_account_service.record_registration(
                    self.db, account, account_url=account_url
                )
            await self._create_order(acme, csr_pem)
            await self._publish()
            await self._confirm_propagation()
            self._transition(CertificateGenerationState.CHALLENGE_PUBLISHED)
            self._store()
            await self._checkpoint()

            await self._answer(acme)
            # Recorded *before* polling: the CA starts validating as soon as the
            # answer lands, so a worker that dies here really was waiting on the CA,
            # and the state has to say so for the recovery path to be honest.
            self._transition(CertificateGenerationState.VALIDATING)
            self._store()
            await self._checkpoint()
            await self._await_validation(acme)

            chain = await acme.finalize_order(
                csr_pem=csr_pem,
                timeout_seconds=float(self.settings.certificate_finalization_timeout_seconds),
            )

        if chain is None:  # pragma: no cover - the session either finalizes or raises
            raise _AttemptFailure(
                "the certificate authority returned no chain", code=CODE_MATERIAL_MISMATCH
            )
        # Stored outside the session block on purpose: a transport failure while the
        # session closes must not be able to undo an issuance the CA already made.
        material = await self._store_material(chain.fullchain_pem, key=key, key_pem=key_pem)
        await self._checkpoint()
        await self.cleanup()
        return material

    def _api(self, kind: DnsProviderKind | str) -> DnsRecordProvider:
        """The provider implementation for *kind*, built once per attempt."""
        key = str(kind)
        api = self._api_cache.get(key)
        if api is None:
            api = self.provider_factory(kind)
            self._api_cache[key] = api
        return api

    async def _create_order(self, session: AcmeSession, csr_pem: bytes) -> AcmeOrder:
        """Place the order, and record it before anything is published for it."""
        order = await session.create_order(csr_pem=csr_pem, identifiers=self.identifiers)
        return await self._record_order(session, order, mode=certificate_order.MODE_AUTOMATED)

    async def _record_order(
        self, session: AcmeSession, order: AcmeOrder, *, mode: str
    ) -> AcmeOrder:
        """Check the CA's answer, then store the order and its challenges, durably.

        Shared by both publishing modes: whether the record is written by this
        platform or by the customer, an order for a different identifier set or an
        order with no dns-01 challenge is refused before anything is recorded — and
        what gets recorded has to be the *same* shape either way, so a resumed
        attempt reads one document format.
        """
        requested = {name.lower() for name in self.identifiers}
        accepted = {name.lower() for name in order.identifiers}
        if accepted and accepted != requested:
            # An order authorizing *more* than was asked for would let the CA mint
            # names this certificate never requested; one authorizing less cannot be
            # finalized into a usable chain. The counts are the platform's own public
            # data — no identifier from the CA's answer is echoed back.
            raise _AttemptFailure(
                "the certificate authority returned an order for a different identifier set",
                code=CODE_ORDER_MISMATCH,
                detail=f"requested {len(requested)}, authorized {len(accepted)}",
            )
        # Both the document and the row record the directory: the document is what
        # a resumed attempt reads, and the row is what the provenance CHECK requires
        # before a material-bearing state may be written (§5.3). Recording it here,
        # when the order is placed, means the attempt cannot reach ``ISSUED`` without
        # having already said which CA answered.
        directory_url = session.directory.url()
        self.generation.directory_url = directory_url
        certificate_order.set_order(
            self.document,
            directory_url=directory_url,
            order_url=order.order_url,
            mode=mode,
            expires_at=order.expires_at,
            # For an automated challenge this is the TTL of the record this
            # platform creates. For a manual one it is only a *recommendation*
            # shown to the operator: the record is theirs, and the platform neither
            # sets nor changes it.
            txt_ttl=self.settings.certificate_dns_ttl_seconds,
        )
        certificate_order.record_challenges(
            self.document, order.challenges, mode=mode, order_url=order.order_url
        )
        self._store()
        if not certificate_order.current_entries(self.document):
            raise _AttemptFailure(
                "the order carried no dns-01 challenge to answer", code=CODE_ORDER_LOST
            )
        await self._checkpoint()
        return order

    # -- manual DNS-01 ---------------------------------------------------------

    def _is_manual(self) -> bool:
        """Whether the customer publishes this certificate's challenges.

        Read from the certificate on every attempt rather than from the document:
        the document records who published a *challenge* (and is what cleanup must
        obey), while the certificate records who publishes this certificate's
        challenges *now*, which is the question the flow branches on.
        """
        return _dns_mode(self.certificate) is CertificateDnsMode.MANUAL

    async def _run_manual(self) -> _Material | None:
        """Place an order and stop, or finish an order the operator has answered.

        The manual path is one attempt split in two by a human act, and the split is
        forced rather than chosen: the key pair that will be certified exists only in
        the attempt that generated it, and the material guard forbids storing it for
        a generation nothing has issued yet. So the attempt that places the order
        cannot be the attempt that finalizes it, and the order — pure, public ACME
        data — is the only thing carried between them (:meth:`_resume_manual_order`).

        Nothing here ever writes to, or deletes from, the customer's zone: the record
        is theirs, published with their own tooling, and the platform's only role is
        to say (truthfully) when the authoritative servers agree it is there.
        """
        (
            self.domain,
            self.provider,
            self.credentials,
            self.identifiers,
            self.directory,
        ) = await _resolve_context(
            self.db, self.generation, self.certificate, settings=self.settings
        )
        directory = self.directory
        assert directory is not None  # set by _resolve_context

        account = await acme_account_service.account_for(
            self.db, None, org_id=self.generation.org_id, directory=directory
        )
        session = self.session_factory(
            directory=directory,
            account_key_pem=await acme_account_service.account_key(self.db, account),
            account_url=account.account_url,
        )
        key: ec.EllipticCurvePrivateKey | None = None
        key_pem = ""
        chain: IssuedChain | None = None
        async with session as acme:
            await acme_account_service.mark_used(self.db, account)
            if account.account_url is None:
                account_url = await acme.register_account(
                    contact_email=self.settings.acme_account_email or None
                )
                await acme_account_service.record_registration(
                    self.db, account, account_url=account_url
                )
            order = await self._resume_manual_order(acme)
            if order is None:
                # Fresh instructions were just written. Stop, deliberately.
                return await self._await_operator()
            if not certificate_order.manual_ready(self.document):
                # The order is open, but this attempt has nothing it may do: the
                # confirmation is incomplete (a retry that arrived after a failed
                # observation, or a dispatch that raced the operator). Re-ordering
                # here would throw away a record the customer already published.
                return await self._await_operator()
            # The authoritative observation, and the only thing that lets the CA be
            # told this challenge is ready. ``manual_ready`` said an observation had
            # passed at some point; this is the one immediately before the answer.
            await self._confirm_propagation()
            self._transition(CertificateGenerationState.CHALLENGE_PUBLISHED)
            self._store()
            await self._checkpoint()

            await self._answer(acme)
            self._transition(CertificateGenerationState.VALIDATING)
            self._store()
            await self._checkpoint()
            await self._await_validation(acme)

            # The key is generated *here*, after validation: the CSR that opened the
            # order was a throwaway used only to name the identifiers, and the key
            # that will sign for the certificate has no reason to exist before the
            # order is ready to be finalized.
            key, key_pem, csr_pem = _generate_key_and_csr(self.identifiers)
            chain = await acme.finalize_order(
                csr_pem=csr_pem,
                timeout_seconds=float(self.settings.certificate_finalization_timeout_seconds),
            )

        if chain is None or key is None:  # pragma: no cover - the session finalizes or raises
            raise _AttemptFailure(
                "the certificate authority returned no chain", code=CODE_MATERIAL_MISMATCH
            )
        material = await self._store_material(chain.fullchain_pem, key=key, key_pem=key_pem)
        await self._checkpoint()
        # Deliberately *no* provider cleanup: every record of this order was created
        # by the customer, and the order document says so (``cleanup`` is
        # ``not_required`` for a manual entry). The operator is given removal
        # instructions instead — see ``certificate_order.cleanup_instructions``.
        return material

    async def _await_operator(self) -> _Material | None:
        """End the attempt waiting for a human, holding no worker and no CA session.

        ``AWAITING_MANUAL`` is a live state: the order is open and the generation is
        resumable. It is also the state that makes ``next_attempt_at`` irrelevant —
        nothing is scheduled, because the thing that has to happen next is not the
        platform's to do.
        """
        if (
            certificate_lifecycle.coerce_state(self.generation.state)
            is not CertificateGenerationState.AWAITING_MANUAL
        ):
            self._transition(CertificateGenerationState.AWAITING_MANUAL)
        certificate_order.finish_attempt(self.document)
        self.generation.next_attempt_at = None
        self.generation.last_error = ""
        self.certificate.last_error = ""
        self.certificate.status = certificate_lifecycle.certificate_status_for(
            CertificateGenerationState.AWAITING_MANUAL
        )
        self._store()
        await self._checkpoint()
        self.waiting = True
        return None

    async def _place_manual_order(self, acme: AcmeSession) -> AcmeOrder:
        """Place the order the operator will publish for, and record its challenges.

        The CSR sent to the CA exists only to name the identifiers: RFC 8555 derives
        an order's identifier list from it and this client offers no other way to
        ask. Its key is discarded immediately, so an order waiting for an operator
        stores no material at all — which is what the generation's material guard
        requires, and what keeps the manual path from becoming a way to persist a
        private key before anything has been issued.
        """
        if certificate_order.current_entries(self.document):
            # A replaced or expired order's instructions can no longer be answered.
            # Nothing is owed for them: this platform never created those records.
            certificate_order.reset_challenges(self.document)
            self._store()
        _discarded_key, _discarded_pem, csr_pem = _generate_key_and_csr(self.identifiers)
        order = await acme.create_order(csr_pem=csr_pem, identifiers=self.identifiers)
        await self._record_order(acme, order, mode=certificate_order.MODE_MANUAL)
        for entry in certificate_order.manual_current(self.document):
            problem = certificate_order.manual_entry_problem(entry)
            if problem:
                raise _AttemptFailure(
                    "the certificate authority returned a challenge this workflow cannot "
                    f"ask an operator to publish: {problem}",
                    code=CODE_MANUAL_CHALLENGE_INVALID,
                )
        return order

    async def _resume_manual_order(self, acme: AcmeSession) -> AcmeOrder | None:
        """The order this generation is waiting on, if it can still be finished.

        ``None`` means a new order was placed (and its instructions are now the ones
        in the document). An order whose challenge set differs from the recorded one
        is re-placed rather than resumed: the operator answered a specific question,
        and answering a different one would report success for a record they never
        published.

        Only an order the CA *refuses as unusable* is replaced quietly. A transport
        failure is not: it propagates, the attempt is recorded as failed, and the
        retry resumes the same order from the same document.
        """
        stored = certificate_order.manual_current(self.document)
        order_url = str(self.document.get("order_url") or "")
        if (
            not stored
            or not order_url
            or certificate_order.order_expired(self.document, now=self.now)
            or any(certificate_order.manual_entry_problem(entry) for entry in stored)
        ):
            await self._place_manual_order(acme)
            return None
        try:
            resumed = await acme.resume_order(order_url=order_url)
        except AcmeError as exc:
            if exc.code != "ACME_ORDER_UNUSABLE":
                raise
            await self._place_manual_order(acme)
            return None

        expected = {name.lower() for name in self.identifiers}
        if resumed.identifiers and {name.lower() for name in resumed.identifiers} != expected:
            raise _AttemptFailure(
                "the certificate authority's order no longer covers this certificate's identifiers",
                code=CODE_ORDER_MISMATCH,
            )
        recorded = {str(entry.get("challenge_url") or ""): entry for entry in stored}
        current = {challenge.challenge_url: challenge for challenge in resumed.challenges}
        if set(recorded) != set(current) or any(
            str(recorded[url].get("record_value") or "") != current[url].record_value
            for url in recorded
        ):
            certificate_order.reset_challenges(self.document)
            await self._place_manual_order(acme)
            return None
        if resumed.expires_at is not None:
            self.document["order_expires_at"] = resumed.expires_at.isoformat()
            self._store()
        return resumed

    async def _publish(self) -> None:
        """Create one TXT record per current-order challenge, durably referenced.

        The order of the two writes is the point: the record is created in the
        customer's zone *first* and its reference is stored and committed immediately
        after. A crash between the two leaves a record this platform cannot name —
        avoidable only by making the record's TTL short — whereas storing the
        reference first would point cleanup at a record that may not exist and hide
        the real one behind a dangling id.
        """
        assert self.provider is not None  # set by run() before this is reached
        api = self._api(self.provider.kind)
        for entry in certificate_order.pending_publication(self.document):
            ref = str(entry.get("ref") or "")
            name = str(entry.get("record_name") or "")
            value = str(entry.get("record_value") or "")
            if not ref or not name or not value:
                raise _AttemptFailure(
                    "the order recorded a challenge with no record name or value",
                    code=CODE_ORDER_LOST,
                )
            # Before any provider call: the allowlist is the only thing standing
            # between a stored credential and a write in a zone it must not touch.
            require_zone_allowed(self.provider, name)
            resolution = await api.resolve_zone(self.credentials, name)
            if resolution.zone is None:
                raise _AttemptFailure(
                    f"the DNS credential cannot resolve a zone for '{name}'",
                    code="DNS_ZONE_UNRESOLVED",
                    detail=resolution.reason,
                )
            record = await self._create_record(
                api, zone_id=resolution.zone.id, name=name, value=value, ref=ref
            )
            certificate_order.update_challenge(
                self.document,
                ref,
                record_id=record.id,
                zone_id=record.zone_id,
                provider_id=str(self.provider.id),
                published_at=certificate_order.now_iso(),
                cleanup=certificate_order.CLEANUP_PENDING,
                cleanup_error="",
            )
            self._store()
            await self._checkpoint()

    async def _create_record(
        self, api: DnsRecordProvider, *, zone_id: str, name: str, value: str, ref: str
    ) -> TxtRecord:
        """Create the record, reconciling an ambiguous outcome by observation.

        ``DnsWriteAmbiguous`` means the write may or may not have landed. Retrying
        blindly would create a second record this platform has no reference to and
        would therefore never delete; adopting the one the zone actually holds keeps
        the zone and the stored reference in agreement, which is what cleanup needs.
        """
        try:
            return await api.create_txt(
                self.credentials,
                zone_id=zone_id,
                name=name,
                value=value,
                ttl=self.settings.certificate_dns_ttl_seconds,
            )
        except DnsWriteAmbiguous as ambiguous:
            found = await api.find_txt(self.credentials, zone_id=zone_id, name=name, value=value)
            if not found:
                raise _AttemptFailure(
                    "the DNS provider did not confirm the challenge record was created and "
                    "no such record is in the zone",
                    code=ambiguous.code,
                    detail=ambiguous.detail,
                    retryable=True,
                ) from None
            certificate_order.update_challenge(
                self.document,
                ref,
                error=(
                    "the create response was lost; adopted the record the zone already held "
                    f"({len(found)} matched)"
                ),
            )
            return found[0]

    async def _confirm_propagation(self) -> None:
        """Wait until *every* current-order value is visible at the authoritative NS.

        Polling happens off the event loop: the wait sleeps between DNS rounds, and
        sleeping on the worker's loop would also stall the checkpoints and the event
        frames queued on it. A record this platform cannot see is one the CA will not
        see either, so this is the step that turns a successful write into a
        challenge that can actually validate.
        """
        expectations = _expectations(self.document)
        if not expectations:
            raise _AttemptFailure(
                "the order recorded no challenge record to prove", code=CODE_ORDER_LOST
            )
        result = await asyncio.to_thread(
            dns_propagation.wait_for_txt_records,
            expectations,
            timeout_seconds=float(self.settings.certificate_propagation_timeout_seconds),
            observer=self.observer,
        )
        unsatisfied = set(result.pending_names)
        for entry in certificate_order.current_entries(self.document):
            ref = str(entry.get("ref") or "")
            if str(entry.get("record_name") or "") in unsatisfied:
                certificate_order.update_challenge(self.document, ref, error=result.detail)
            elif entry.get("mode") == certificate_order.MODE_MANUAL:
                # ``observed_at`` only. The operator's confirmation is a different
                # fact and is written only by the confirmation endpoint; deriving it
                # from our own observation would erase the distinction the design
                # rests on (§5.3) and make a retry look like a fresh request.
                certificate_order.update_challenge(
                    self.document, ref, observed_at=certificate_order.now_iso(), error=""
                )
            elif not entry.get("confirmed_at"):
                certificate_order.update_challenge(
                    self.document, ref, confirmed_at=certificate_order.now_iso()
                )
        certificate_order.record_observation(
            self.document,
            status=result.status,
            detail=result.detail,
            attempts=result.attempts,
            nameservers=dns_propagation.nameserver_summary(result),
        )
        self._store()
        if result.ok:
            return
        raise _AttemptFailure(
            "the challenge record is not visible at the authoritative nameservers yet",
            code=f"DNS_{result.status}",
            detail=result.detail,
            # A name with no authoritative delegation is a configuration problem that
            # waiting cannot fix; every other status is propagation outlasting the
            # deadline, which another attempt can plausibly outlast too.
            retryable=result.status != dns_propagation.STATUS_NO_AUTHORITATIVE_NS,
        )

    async def _answer(self, session: AcmeSession) -> None:
        """Tell the CA that every current-order challenge is ready for validation."""
        entries = certificate_order.current_entries(self.document)
        if not entries:
            raise _AttemptFailure("the order recorded no challenge to answer", code=CODE_ORDER_LOST)
        for entry in entries:
            challenge_url = str(entry.get("challenge_url") or "")
            if not challenge_url:
                raise _AttemptFailure(
                    "the order recorded a challenge with no URL", code=CODE_ORDER_LOST
                )
            await session.accept_challenge(challenge_url=challenge_url)

    async def _await_validation(self, session: AcmeSession) -> None:
        """Poll every distinct authorization to its verdict.

        The CA's answer, not ours: a failed authorization carries the reason as an
        authority-issued code, which :func:`classify_error` turns into the same
        failure vocabulary the rest of the attempt uses. Authorizations are polled
        once each even when several challenges share one (apex and wildcard share an
        identifier), because that is what the CA actually validates.
        """
        authorizations: dict[str, list[str]] = {}
        for entry in certificate_order.current_entries(self.document):
            url = str(entry.get("authorization_url") or "")
            if url:
                authorizations.setdefault(url, []).append(str(entry.get("ref") or ""))
        if not authorizations:
            raise _AttemptFailure(
                "the order recorded no authorization to validate", code=CODE_ORDER_LOST
            )
        for url, refs in authorizations.items():
            state = await session.poll_authorization(
                authorization_url=url,
                timeout_seconds=float(self.settings.certificate_validation_timeout_seconds),
            )
            if state.invalid:
                for ref in refs:
                    certificate_order.update_challenge(
                        self.document, ref, error=state.error_detail or state.error_code
                    )
                self._store()
                failure = classify_error(state.error_code, state.error_detail)
                raise _AttemptFailure(
                    failure.message,
                    code=failure.code,
                    detail=failure.detail,
                    retryable=failure.retryable,
                )
            if not state.valid:
                # Still pending when our deadline passed: our own timeout, so the
                # failure says that instead of implying the CA refused something.
                raise _AttemptFailure(
                    "the certificate authority did not finish validating the challenge in time",
                    code="ACME_VALIDATION_TIMEOUT",
                    retryable=True,
                )
            for ref in refs:
                certificate_order.update_challenge(
                    self.document, ref, validated_at=certificate_order.now_iso()
                )
        self._store()
        await self._checkpoint()

    async def _store_material(
        self, fullchain_pem: str, *, key: ec.EllipticCurvePrivateKey, key_pem: str
    ) -> _Material:
        """Verify, encrypt and store the material, then move to ``ISSUED``.

        Every check runs before the first write: the leaf has to answer this
        attempt's key and identifier list, the validity window has to be sane, and
        both ciphertexts have to come from one DEK generation — so either the row
        gets a complete, verifiable material set or it gets nothing at all.
        """
        leaf = _leaf_of(fullchain_pem)
        _verify_leaf(leaf, key, self.identifiers)
        not_before = _aware(leaf.not_valid_before_utc)
        not_after = _aware(leaf.not_valid_after_utc)
        if not_after <= self.now:
            raise _AttemptFailure(
                "the certificate authority returned a certificate that is already expired",
                code=CODE_MATERIAL_MISMATCH,
            )
        fingerprint = payload_crypto.fingerprint(
            leaf.public_bytes(serialization.Encoding.DER), kind="certificate.leaf"
        )

        async with org_dek_context(self.db, self.generation.org_id) as dek:
            deke_id = dek.generation
            key_ciphertext = encrypt(
                dek.fernet,
                PayloadContext(
                    org_id=self.generation.org_id,
                    purpose=PURPOSE_CERTIFICATE_KEY,
                    record_id=self.generation.id,
                    deke_id=deke_id,
                ),
                key_pem.encode("ascii"),
            )
            chain_ciphertext = encrypt(
                dek.fernet,
                PayloadContext(
                    org_id=self.generation.org_id,
                    purpose=PURPOSE_CERTIFICATE_CHAIN,
                    record_id=self.generation.id,
                    deke_id=deke_id,
                ),
                fullchain_pem.encode("utf-8"),
            )

        self._transition(CertificateGenerationState.ISSUED)
        self.generation.key_ciphertext = key_ciphertext
        self.generation.chain_ciphertext = chain_ciphertext
        self.generation.fingerprint = fingerprint
        self.generation.not_before = not_before
        self.generation.not_after = not_after
        self.generation.issued_at = self.now
        self.generation.deke_id = deke_id
        self.generation.last_error = ""
        self.generation.next_attempt_at = None
        # The certificate becomes current here and only here, and because this
        # generation carries material. Superseding a *previous* current generation is
        # renewal's job (§5.6); nothing in this slice can produce a second
        # material-bearing generation for one certificate.
        self.certificate.status = certificate_lifecycle.certificate_status_for(
            CertificateGenerationState.ISSUED
        )
        self.certificate.expires_at = not_after
        self.certificate.current_generation_id = self.generation.id
        self.certificate.last_error = ""
        self.document["finalized_at"] = certificate_order.now_iso()
        certificate_order.finish_attempt(self.document)
        self._store()
        await self.db.flush()
        log.info(
            "certificate_issued",
            certificate=str(self.certificate.id),
            generation=self.generation.generation,
            fingerprint=fingerprint,
        )
        return _Material(fingerprint=fingerprint, not_before=not_before, not_after=not_after)

    # -- failure ---------------------------------------------------------------

    async def fail(self, failure: _AttemptFailure) -> bool:
        """Record the failure and schedule the retry; report whether it is terminal.

        Both halves are written together: the state the attempt ended in, the reason
        a human will read, and *whether there is another attempt* — because a row
        that says ``FAILED`` without saying whether anything will try again is what
        makes an operator guess.
        """
        scheduled = _scheduled_retry(failure, self.attempt, now=self.now)
        self._transition(CertificateGenerationState.FAILED)
        self.generation.last_error = failure.text()
        self.generation.next_attempt_at = scheduled
        self.certificate.last_error = failure.text()
        self.certificate.status = certificate_lifecycle.certificate_status_for(
            CertificateGenerationState.FAILED
        )
        certificate_order.finish_attempt(self.document)
        self._store()
        await self._checkpoint()
        return scheduled is None

    # -- cleanup ---------------------------------------------------------------

    async def cleanup(self) -> None:
        """Delete every TXT record this generation created and cannot confirm gone.

        Idempotent and total: it runs at the start of an attempt, after a successful
        issuance, and after a failure, and it never raises for a provider's sake. A
        deletion that cannot be confirmed is recorded as ``unresolved`` with the
        reason and retried by the next attempt, which is the only honest way to
        report "we could not tell whether it is still there" — see
        :mod:`app.services.certificate_order`.
        """
        pending = certificate_order.pending_cleanup(self.document)
        if not pending:
            return
        for entry in pending:
            await self._delete_record(entry)
        self._store()
        await self._checkpoint()
        leftover = certificate_order.cleanup_incomplete(self.document)
        if leftover:
            log.warning(
                "challenge_record_cleanup_incomplete",
                certificate=str(self.certificate.id),
                generation=self.generation.generation,
                records=len(leftover),
            )

    async def _delete_record(self, entry: dict[str, Any]) -> None:
        """Delete one record by its reference, recording the outcome truthfully."""
        ref = str(entry.get("ref") or "")
        attempts = int(entry.get("cleanup_attempts") or 0) + 1
        provider_row = await self._publisher(entry)
        if provider_row is None:
            certificate_order.update_challenge(
                self.document,
                ref,
                cleanup=certificate_order.CLEANUP_UNRESOLVED,
                cleanup_attempts=attempts,
                cleanup_error=(
                    "the DNS credential that published this record is no longer available"
                ),
            )
            return
        try:
            credentials = await credentials_for_use(self.db, provider_row)
        except Exception as exc:
            certificate_order.update_challenge(
                self.document,
                ref,
                cleanup=certificate_order.CLEANUP_UNRESOLVED,
                cleanup_attempts=attempts,
                cleanup_error=f"the credential could not be read ({type(exc).__name__})",
            )
            return
        try:
            gone = await self._api(provider_row.kind).delete_txt(
                credentials,
                zone_id=str(entry.get("zone_id") or ""),
                record_id=str(entry.get("record_id") or ""),
            )
        except DnsProviderError as exc:
            certificate_order.update_challenge(
                self.document,
                ref,
                cleanup=certificate_order.CLEANUP_UNRESOLVED,
                cleanup_attempts=attempts,
                cleanup_error=f"{exc.code}: {exc.message}",
            )
            return
        except Exception as exc:
            certificate_order.update_challenge(
                self.document,
                ref,
                cleanup=certificate_order.CLEANUP_UNRESOLVED,
                cleanup_attempts=attempts,
                cleanup_error=f"the delete call failed ({type(exc).__name__})",
            )
            return
        certificate_order.update_challenge(
            self.document,
            ref,
            cleanup=(
                certificate_order.CLEANUP_DONE if gone else certificate_order.CLEANUP_UNRESOLVED
            ),
            cleanup_attempts=attempts,
            cleanup_error=(
                "" if gone else "the DNS provider did not confirm the challenge record was deleted"
            ),
        )

    async def _publisher(self, entry: dict[str, Any]) -> DnsProvider | None:
        """The credential that published one record, resolved by its stored id.

        By id, not "the certificate's credential": an override can change between the
        attempt that created a record and the attempt that deletes it, and a record
        created in zone A cannot be deleted with a credential that only reaches zone B.
        """
        raw = str(entry.get("provider_id") or "")
        if not raw:
            # An entry with no recorded publisher can only come from this attempt
            # (the current credential) or from a document older than this field.
            return self.provider
        try:
            provider_id = uuid.UUID(raw)
        except ValueError:
            return None
        return await self.db.get(DnsProvider, provider_id)


# --- Orchestration -------------------------------------------------------------


def _refusal(
    generation: CertificateGeneration,
    document: dict[str, Any],
    *,
    certificate: Certificate | None,
) -> IssuanceAttempt | None:
    """Why this call will not attempt, or ``None`` when it should.

    Checked before the attempt is stamped, because none of these is an attempt: the
    generation is already material-bearing or terminal, the document is from a
    version this code cannot read, or the budget is spent. Recording a *failure* for
    one of them would overwrite the reason an operator needs with a new one.
    """
    state = certificate_lifecycle.coerce_state(generation.state)
    if state is None:
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=CertificateGenerationState.FAILED,
            attempt=generation.attempt_count,
            code=CODE_DOCUMENT_UNSUPPORTED,
            message="the generation carries a state this version does not know",
        )
    if certificate_order.version(document) != certificate_order.DOCUMENT_VERSION:
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=state,
            attempt=generation.attempt_count,
            code=CODE_DOCUMENT_UNSUPPORTED,
            message=(
                "the recorded order was written by a different version of this platform and "
                "cannot be read safely"
            ),
        )
    if certificate_lifecycle.material_required(state):
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=state,
            attempt=generation.attempt_count,
            code="CERTIFICATE_ALREADY_ISSUED",
            message="this generation has already been issued",
            terminal=certificate_lifecycle.is_terminal(state, generation.attempt_count),
        )
    if state is CertificateGenerationState.FAILED and certificate_lifecycle.is_terminal(
        state, generation.attempt_count
    ):
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=state,
            attempt=generation.attempt_count,
            code=CODE_ATTEMPTS_EXHAUSTED,
            message=(
                "the attempt budget for this generation is spent; request a new certificate "
                "to try again"
            ),
            terminal=True,
        )
    if state not in (
        *CertificateGenerationState.live_pre_issuance(),
        CertificateGenerationState.FAILED,
    ):
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=state,
            attempt=generation.attempt_count,
            code="CERTIFICATE_STATE_NOT_ATTEMPTABLE",
            message=f"a generation in state {state.value} cannot be attempted",
            terminal=certificate_lifecycle.is_terminal(state, generation.attempt_count),
        )
    if certificate is None:
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=state,
            attempt=generation.attempt_count,
            code=CODE_CONTEXT_INCOMPLETE,
            message="the certificate this generation belongs to no longer exists",
        )
    return None


async def issue_generation(
    db: AsyncSession,
    generation: CertificateGeneration,
    *,
    certificate: Certificate | None = None,
    settings: Settings | None = None,
    now: datetime | None = None,
    session_factory: SessionFactory | None = None,
    provider_factory: Callable[[DnsProviderKind | str], DnsRecordProvider] | None = None,
    observer: dns_propagation.Observer | None = None,
    checkpoint: Callable[[], Awaitable[None]] | None = None,
) -> IssuanceAttempt:
    """Run at most one issuance attempt for *generation*, and say what happened.

    Safe to call concurrently and repeatedly, which is what makes it safe to enqueue
    from a request, from the sweep and from a manual retry:

    * a dispatch that arrives while another worker is running this generation is
      refused (:data:`CODE_ATTEMPT_IN_FLIGHT`) without touching the row;
    * a dispatch that arrives after a worker died recovers the abandoned attempt —
      recording that the platform lost a worker, not that a CA refused anything —
      and continues immediately;
    * a dispatch that arrives before the backoff has elapsed is refused
      (:data:`CODE_NOT_DUE`) without touching the row.

    The seams are parameters so the flow can be exercised without a CA, a zone or a
    real resolver: a fake session factory, a fake DNS provider and a fake DNS
    observer run the same code the worker runs.
    """
    settings = settings or get_settings()
    now = now or _utcnow()
    document = certificate_order.load(generation)
    if certificate is None:
        certificate = await db.get(Certificate, generation.certificate_id)

    refusal = _refusal(generation, document, certificate=certificate)
    if refusal is not None:
        return refusal
    assert certificate is not None  # narrowed by _refusal

    state = certificate_lifecycle.assert_state(generation.state)
    if state in CertificateGenerationState.live_pre_issuance():
        if certificate_order.attempt_in_flight(
            document, now=now, ttl_seconds=float(settings.certificate_order_ttl_seconds)
        ):
            return IssuanceAttempt(
                generation_id=generation.id,
                ok=False,
                state=state,
                attempt=generation.attempt_count,
                code=CODE_ATTEMPT_IN_FLIGHT,
                message="another worker is running an attempt for this generation",
            )
        if state is not CertificateGenerationState.PENDING and (
            # Everything except the manual wait: a live state with no running
            # attempt is a worker that stopped holding it.
            state is not CertificateGenerationState.AWAITING_MANUAL
            # The manual wait is the exception, and only when nothing is stamped:
            # its attempt ended deliberately (``finish_attempt``) because the next
            # move is the operator's. A *stamped* attempt under it is a resume whose
            # worker died, which is exactly the loss this branch exists to recover.
            or certificate_order.attempt_unfinished(document)
        ):
            # A live state with no running attempt: the worker that entered it
            # stopped. The attempt it began is already counted, so this is a failure
            # to record, and the order it left is replaced by the next attempt's.
            await _record_abandoned(db, generation, certificate, document, now=now)
            await _flush_and_checkpoint(db, checkpoint)
            state = CertificateGenerationState.FAILED
            if certificate_lifecycle.retry_budget_exhausted(generation.attempt_count):
                return IssuanceAttempt(
                    generation_id=generation.id,
                    ok=False,
                    state=state,
                    attempt=generation.attempt_count,
                    code=CODE_ATTEMPTS_EXHAUSTED,
                    message=(
                        "the attempt budget for this generation is spent; request a new "
                        "certificate to try again"
                    ),
                    terminal=True,
                )

    if state is CertificateGenerationState.AWAITING_MANUAL and not certificate_order.manual_ready(
        document
    ):
        # The order is open and nothing is due: the record has not been confirmed as
        # published (or has not been *seen* published) yet. An attempt here would
        # wait out a whole propagation deadline and then spend one of five attempts
        # failing, for a record the operator is still about to create — so the
        # dispatch is refused without touching the row.
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=state,
            attempt=generation.attempt_count,
            code=CODE_AWAITING_MANUAL,
            message=(
                "this generation is waiting for an operator to publish its dns-01 challenge "
                "record; nothing is attempted until it is confirmed and observed"
            ),
            waiting=True,
        )

    if generation.next_attempt_at is not None and generation.next_attempt_at > now:
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=state,
            attempt=generation.attempt_count,
            code=CODE_NOT_DUE,
            message="this generation is not due an attempt yet",
            next_attempt_at=generation.next_attempt_at,
        )

    runner = _Attempt(
        db=db,
        generation=generation,
        certificate=certificate,
        settings=settings,
        session_factory=session_factory or open_acme_session,
        provider_factory=provider_factory or records_provider_for,
        observer=observer,
        checkpoint=checkpoint,
        document=document,
        attempt=generation.attempt_count + 1,
        now=now,
    )
    await runner.begin()

    material: _Material | None = None
    failure: _AttemptFailure | None = None
    try:
        material = await runner.run()
    except _AttemptFailure as exc:
        failure = exc
    except (AcmeError, AcmeDirectoryError, DnsProviderError, AppError) as exc:
        failure = _failure_from(exc)
    except Exception as exc:
        # Recorded with the class name only: an unexpected message can quote a
        # request, a URL or a credential. The traceback goes to the worker's log.
        log.error(
            "issuance_attempt_crashed",
            certificate=str(certificate.id),
            generation=generation.generation,
            error=type(exc).__name__,
        )
        failure = _AttemptFailure(
            "the issuance attempt failed unexpectedly",
            code=CODE_ATTEMPT_ERROR,
            detail=type(exc).__name__,
            retryable=True,
        )

    if material is None and runner.waiting:
        # The manual stop: the order is placed and the instructions are durable, so
        # this is an outcome with information for an operator rather than a failure.
        # Nothing is scheduled — the next move is theirs.
        await _publish_awaiting_manual(
            db, certificate, generation, attempt=runner.attempt, document=runner.document
        )
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=CertificateGenerationState.AWAITING_MANUAL,
            attempt=runner.attempt,
            code=CODE_AWAITING_MANUAL,
            message=(
                "the order is placed and waiting for its dns-01 challenge record to be "
                "published and confirmed"
            ),
            waiting=True,
        )

    if failure is not None or material is None:
        failure = failure or _AttemptFailure(
            "the attempt produced no result", code=CODE_ATTEMPT_ERROR, retryable=True
        )
        terminal = await runner.fail(failure)
        # The failure is durable before cleanup runs, so a slow or broken DNS call
        # cannot cost the record of what went wrong.
        await _publish_failure(
            db, certificate, generation, failure, attempt=runner.attempt, terminal=terminal
        )
        await runner.cleanup()
        return IssuanceAttempt(
            generation_id=generation.id,
            ok=False,
            state=CertificateGenerationState.FAILED,
            attempt=runner.attempt,
            code=failure.code,
            message=failure.text(),
            retryable=not terminal,
            terminal=terminal,
            next_attempt_at=generation.next_attempt_at,
        )

    directory = runner.directory
    assert directory is not None  # set by run() before it can produce material
    await _publish_success(
        db,
        certificate,
        generation,
        material,
        directory=directory,
        attempt=runner.attempt,
    )
    return IssuanceAttempt(
        generation_id=generation.id,
        ok=True,
        state=CertificateGenerationState.ISSUED,
        attempt=runner.attempt,
        message=f"issued from the {directory.value} directory",
    )


async def _manual_state(
    db: AsyncSession, certificate: Certificate
) -> tuple[CertificateGeneration, CertificateGenerationState, dict[str, Any]]:
    """The generation whose manual challenge this certificate is working on.

    Three refusals, each saying a different thing: the certificate's challenges are
    published automatically (there is nothing for an operator to do), it has no
    generation, or its generation records no manual challenge. Answering any of them
    with a challenge value would be handing out somebody else's instruction — or an
    instruction for an order that no longer exists.
    """
    if _dns_mode(certificate) is not CertificateDnsMode.MANUAL:
        raise Conflict(
            "This certificate's dns-01 challenges are published automatically; there is no "
            "manual challenge to act on.",
            code=CODE_MANUAL_NOT_PENDING,
        )
    generation = await certificate_service.latest_generation(db, certificate.id)
    if generation is None:
        raise Conflict(
            "This certificate has no issuance attempt to act on.",
            code="CERTIFICATE_NO_GENERATION",
        )
    state = certificate_lifecycle.coerce_state(generation.state)
    if state is None:
        raise Conflict(
            "This certificate's generation carries a state this version does not know.",
            code=CODE_CONTEXT_INCOMPLETE,
        )
    document = certificate_order.load(generation)
    if not certificate_order.manual_current(document):
        raise Conflict(
            "No manual dns-01 challenge is recorded for this certificate's current order.",
            code=CODE_ORDER_LOST,
        )
    return generation, state, document


async def manual_challenge(db: AsyncSession, certificate: Certificate) -> ManualChallengeStatus:
    """What this certificate's manual challenge needs from an operator. **Read-only.**

    No DNS is contacted and nothing is written: this is the persisted instruction and
    the last observation, so a dashboard can render the exact record to publish and
    say truthfully how the last check went. A fresh check is what the confirmation
    call does.
    """
    generation, state, document = await _manual_state(db, certificate)
    return ManualChallengeStatus(
        generation_id=generation.id,
        generation=generation.generation,
        state=state,
        certificate_id=certificate.id,
        document=document,
        identifiers=_identifiers(certificate),
        # "Finished with its records" is the issuance *or* a generation that will
        # not be attempted again: only then is the customer's value obsolete.
        finished=state is CertificateGenerationState.ISSUED
        or certificate_lifecycle.is_terminal(state, generation.attempt_count),
        observation=certificate_order.observation(document),
    )


async def confirm_manual_publication(
    db: AsyncSession,
    certificate: Certificate,
    ctx: AuthContext | None = None,
    *,
    refs: Sequence[str] | None = None,
    request: Request | None = None,
    observer: dns_propagation.Observer | None = None,
) -> ManualChallengeStatus:
    """Record an operator's confirmation and **recheck authoritative DNS once**.

    The confirmation is a request to look, and this is the looking: one bounded round
    against the authoritative servers, judged by the same policy the automated path
    uses (:func:`app.services.dns_propagation.check_once`). It is deliberately not a
    full attempt — nothing is ordered, nothing is answered and no attempt is spent —
    because the ordinary case is an operator pressing the button seconds after
    publishing, before the zone has caught up.

    Two things this cannot do, and neither is negotiable:

    * it never marks the challenge validated or the certificate issued — the CA's
      authorization is the only verdict on that;
    * it never skips the observation. Even when the round passes, the resume attempt
      observes again immediately before it answers the CA, so a record removed in
      between is caught rather than assumed.

    A resume attempt is dispatched only when the round passed *and* every manual
    challenge of the order is confirmed and observed. Repeated calls are idempotent:
    the second confirmation of a challenge keeps its first timestamp, and the
    observation is simply run again.
    """
    generation, state, document = await _manual_state(db, certificate)
    if state is not CertificateGenerationState.AWAITING_MANUAL:
        raise Conflict(
            f"This certificate is not waiting for a manual challenge (state {state.value}). "
            "Confirmation applies only while issuance is waiting for the record to be "
            "published.",
            code=CODE_MANUAL_NOT_PENDING,
        )

    entries = certificate_order.manual_current(document)
    by_ref = {str(entry.get("ref") or ""): entry for entry in entries}
    if refs:
        unknown = [ref for ref in refs if ref not in by_ref]
        if unknown:
            raise Conflict(
                "This certificate has no challenge with that reference.",
                code="CERTIFICATE_CHALLENGE_NOT_FOUND",
            )
        targets = [by_ref[ref] for ref in refs]
    else:
        # No refs means "everything I have not confirmed yet"; once everything is
        # confirmed it means "check again", which is what a retry of the observation
        # is, and must not be a 409.
        targets = [entry for entry in entries if not entry.get("confirmed_at")] or entries

    for entry in targets:
        problem = certificate_order.manual_entry_problem(entry)
        if problem:
            raise Conflict(
                f"The recorded challenge cannot be acted on: {problem}. Request a new "
                "certificate instead.",
                code=CODE_MANUAL_CHALLENGE_INVALID,
            )

    just_confirmed: list[str] = []
    for entry in targets:
        ref = str(entry.get("ref") or "")
        _confirmed, changed = certificate_order.confirm_published(document, ref)
        if changed:
            just_confirmed.append(ref)

    result = await asyncio.to_thread(
        dns_propagation.check_once, _expectations(document), observer=observer
    )
    certificate_order.record_observation(
        document,
        status=result.status,
        detail=result.detail,
        attempts=result.attempts,
        nameservers=dns_propagation.nameserver_summary(result),
    )
    if result.ok:
        # The order's whole expectation set passed, so every challenge of it was
        # seen: this is the observation ``manual_ready`` asks for, recorded once for
        # the order rather than guessed per challenge.
        stamp = certificate_order.now_iso()
        for entry in entries:
            certificate_order.update_challenge(
                document, str(entry.get("ref") or ""), observed_at=stamp, error=""
            )
    certificate_order.store(generation, document)
    await db.flush()

    resume_requested = bool(result.ok and certificate_order.manual_ready(document))
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="CERTIFICATE_CHALLENGE_CONFIRMED",
        message=(
            f"The dns-01 challenge for {certificate.primary_cn} was confirmed and rechecked "
            f"({result.status})"
        ),
        level=EventLevel.INFO,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            # References and the judged status only: the record value is not an
            # event field, and neither is any per-server answer beyond a count.
            "references": just_confirmed,
            "propagation_status": result.status,
            "nameservers": len(result.nameserver_answers),
            "resume_requested": resume_requested,
        },
        org_id=generation.org_id,
    )
    await audit_service.record(
        db,
        ctx,
        action="certificate.challenge_confirmed",
        resource_type="certificate",
        resource_id=certificate.id,
        metadata={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "references": just_confirmed,
            "propagation_status": result.status,
        },
        org_id=generation.org_id,
        request=request,
    )
    log.info(
        "certificate_manual_challenge_confirmed",
        certificate=str(certificate.id),
        generation=generation.generation,
        propagation=result.status,
        references=len(just_confirmed),
        resume=resume_requested,
    )
    if resume_requested:
        enqueue_generation(db, generation.id)
    return ManualChallengeStatus(
        generation_id=generation.id,
        generation=generation.generation,
        state=CertificateGenerationState.AWAITING_MANUAL,
        certificate_id=certificate.id,
        document=document,
        identifiers=_identifiers(certificate),
        observation=certificate_order.observation(document),
        resume_requested=resume_requested,
    )


async def request_retry(
    db: AsyncSession,
    certificate: Certificate,
    ctx: AuthContext | None = None,
    *,
    request: Request | None = None,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> CertificateGeneration:
    """Make the certificate's newest generation attemptable *now*, or refuse it.

    A retry is not an attempt: it touches no CA, publishes nothing and changes no
    state — it pulls the next attempt's schedule forward and hands the work back to
    the same worker path, so a manual retry and a scheduled one run identical code.
    What it refuses, it refuses with a reason: an issued or terminal generation has
    nothing left to attempt, and a generation whose attempt is genuinely running is
    already being worked on.

    A *live* generation with no running attempt is allowed through on purpose: that
    is the shape of a dispatch the broker lost, and making an operator wait for the
    sweep to notice is worse than enqueueing the work again — which
    :func:`issue_generation` turns into a no-op when it turns out to be running
    after all.
    """
    settings = settings or get_settings()
    now = now or _utcnow()
    generation = await certificate_service.latest_generation(db, certificate.id)
    if generation is None:
        raise Conflict(
            "This certificate has no issuance attempt to retry.",
            code="CERTIFICATE_NO_GENERATION",
        )
    state = certificate_lifecycle.coerce_state(generation.state)
    document = certificate_order.load(generation)

    if state is None or certificate_lifecycle.material_required(state):
        raise Conflict(
            "This certificate has already been issued; retrying would not change it.",
            code="CERTIFICATE_ALREADY_ISSUED",
        )
    if state is CertificateGenerationState.FAILED:
        if certificate_lifecycle.retry_budget_exhausted(generation.attempt_count):
            raise Conflict(
                f"Issuance for this certificate has already spent its "
                f"{certificate_lifecycle.MAX_ISSUE_ATTEMPTS} attempts. Request a new "
                "certificate instead of retrying this one.",
                code=CODE_ATTEMPTS_EXHAUSTED,
            )
    elif state in CertificateGenerationState.live_pre_issuance():
        if certificate_order.attempt_in_flight(
            document, now=now, ttl_seconds=float(settings.certificate_order_ttl_seconds)
        ):
            raise Conflict(
                "An issuance attempt for this certificate is already running.",
                code=CODE_ATTEMPT_IN_FLIGHT,
            )
    else:
        raise Conflict(
            f"Issuance for this certificate is in state {state.value} and cannot be retried.",
            code="CERTIFICATE_STATE_NOT_ATTEMPTABLE",
        )

    generation.next_attempt_at = now
    await db.flush()
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="CERTIFICATE_ISSUANCE_RETRIED",
        message=(
            f"Another issuance attempt was requested for {certificate.primary_cn} "
            f"(attempt {generation.attempt_count} of "
            f"{certificate_lifecycle.MAX_ISSUE_ATTEMPTS})"
        ),
        level=EventLevel.INFO,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "attempts": generation.attempt_count,
        },
        org_id=certificate.org_id,
    )
    await audit_service.record(
        db,
        ctx,
        action="certificate.issuance_retried",
        resource_type="certificate",
        resource_id=certificate.id,
        metadata={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "attempts": generation.attempt_count,
        },
        org_id=certificate.org_id,
        request=request,
    )
    # The schedule is pulled forward *and* the work is handed over, in that order
    # and in one transaction: a retry that only moved the timestamp would wait for
    # the sweep, which is the delay the operator was trying to avoid.
    enqueue_generation(db, generation.id)
    log.info(
        "certificate_issuance_retry_requested",
        certificate=str(certificate.id),
        generation=str(generation.id),
        attempt_count=generation.attempt_count,
    )
    return generation


def enqueue_generation(db: AsyncSession, generation_id: uuid.UUID) -> None:
    """Hand one generation to the worker, but only once *db* commits.

    Inline is a race, and the race is not theoretical: the worker's first read is
    the row this call is about to write, so a task that starts before the commit
    finds a generation that is not there yet, records "missing", and leaves the
    request untouched until the sweep rescues it — minutes later, for a request the
    caller was told had been accepted. Rollback drops the callback, so a request
    that failed never queues an attempt for a row that never existed.

    The broker is not an error source for the caller: an enqueue that cannot reach
    it is logged and dropped, and the sweep dispatches whatever is due. That is
    what the sweep is for, and it is why a broker restart is a delay rather than a
    lost issuance.
    """
    after_commit(db, "certificate_issuance", lambda: _enqueue_issuance(generation_id))


async def _enqueue_issuance(generation_id: uuid.UUID) -> None:
    """Dispatch the worker task. Deliberately the only place that names it.

    Indirected through this function rather than called at each site so a test can
    record the handoff instead of performing it (the deployments suite does the
    same for its own task), and so broker downtime is handled in exactly one
    place.
    """
    try:
        from app.tasks.certificates import issue_certificate

        issue_certificate.delay(str(generation_id))
    except Exception as exc:
        log.warning(
            "certificate_enqueue_failed",
            generation_id=str(generation_id),
            error=type(exc).__name__,
        )


async def _flush_and_checkpoint(
    db: AsyncSession, checkpoint: Callable[[], Awaitable[None]] | None
) -> None:
    await db.flush()
    if checkpoint is not None:
        await checkpoint()


async def _record_abandoned(
    db: AsyncSession,
    generation: CertificateGeneration,
    certificate: Certificate,
    document: dict[str, Any],
    *,
    now: datetime,
) -> None:
    """Record that an attempt's worker stopped without finishing it.

    Deliberately *not* a reason to give up: the attempt is counted (it was begun),
    the reason is recorded so an operator can see that the platform lost a worker
    rather than that a CA refused something, and the generation becomes due
    immediately — a broker restart should not cost a customer a five-minute backoff
    they never earned. The budget still bounds the loop, so a genuinely crash-looping
    attempt ends up terminal instead of spinning forever.
    """
    generation.state = certificate_lifecycle.require_transition(
        generation.state, CertificateGenerationState.FAILED
    )
    generation.last_error = (
        "the worker running this attempt stopped without finishing it; nothing was issued "
        "and another attempt is being made"
    )[:_MAX_ERROR_TEXT]
    generation.next_attempt_at = now
    certificate.status = certificate_lifecycle.certificate_status_for(
        CertificateGenerationState.FAILED
    )
    certificate.last_error = generation.last_error
    certificate_order.finish_attempt(document)
    certificate_order.store(generation, document)
    await db.flush()
    log.warning(
        "issuance_attempt_abandoned",
        certificate=str(certificate.id),
        generation=generation.generation,
        attempt=generation.attempt_count,
    )
    await event_bus.publish(
        db,
        type="CERTIFICATE_ISSUANCE_FAILED",
        message=(
            f"Issuance attempt {generation.attempt_count} for {certificate.primary_cn} lost "
            "its worker and is being retried"
        ),
        level=EventLevel.WARNING,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "attempt": generation.attempt_count,
            "code": CODE_WORKER_LOST,
            "retryable": True,
        },
        org_id=generation.org_id,
    )


async def _publish_awaiting_manual(
    db: AsyncSession,
    certificate: Certificate,
    generation: CertificateGeneration,
    *,
    attempt: int,
    document: dict[str, Any],
) -> None:
    """Announce that issuance is waiting for a human — **without a challenge value**.

    An event is readable by anything subscribed to the bus, so it carries what an
    operator needs to know that something is waiting (the certificate, the attempt,
    how many records and at which names) and never the TXT value itself. That value
    has exactly one exit from this platform: the authenticated, organization-scoped
    challenge endpoint.
    """
    instructions = certificate_order.manual_instructions(document)
    record_names = sorted({str(entry.get("record_name") or "") for entry in instructions})
    await event_bus.publish(
        db,
        type="CERTIFICATE_AWAITING_MANUAL",
        message=(
            f"Certificate {certificate.primary_cn} is waiting for its dns-01 challenge "
            f"record{'' if len(instructions) == 1 else 's'} to be published"
        ),
        level=EventLevel.INFO,
        actor_type=ActorType.SYSTEM,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "attempt": attempt,
            "record_names": record_names,
            "records": len(instructions),
        },
        org_id=generation.org_id,
    )
    log.info(
        "certificate_awaiting_manual_challenge",
        certificate=str(certificate.id),
        generation=generation.generation,
        records=len(instructions),
    )


async def _publish_failure(
    db: AsyncSession,
    certificate: Certificate,
    generation: CertificateGeneration,
    failure: _AttemptFailure,
    *,
    attempt: int,
    terminal: bool,
) -> None:
    """Announce one failed attempt, and page an operator when it was the last one.

    Two events rather than one with a flag: an attempt that will be retried is
    information, and a generation that has stopped is a request nobody is working on
    any more. The alert is created for the terminal case only, because an alert per
    attempt across a five-attempt backoff is how an operator learns to ignore alerts.
    """
    await event_bus.publish(
        db,
        type="CERTIFICATE_ISSUANCE_FAILED",
        message=(
            f"Issuance attempt {attempt} of {certificate_lifecycle.MAX_ISSUE_ATTEMPTS} for "
            f"{certificate.primary_cn} failed ({failure.code})"
        ),
        level=EventLevel.WARNING,
        actor_type=ActorType.SYSTEM,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "attempt": attempt,
            "code": failure.code,
            "retryable": not terminal,
            "terminal": terminal,
            "next_attempt_at": (
                generation.next_attempt_at.isoformat() if generation.next_attempt_at else None
            ),
        },
        org_id=generation.org_id,
    )
    if not terminal:
        log.warning(
            "issuance_attempt_failed",
            certificate=str(certificate.id),
            generation=generation.generation,
            attempt=attempt,
            code=failure.code,
        )
        return

    await event_bus.publish(
        db,
        type="CERTIFICATE_FAILED",
        message=(
            f"Issuance failed for {certificate.primary_cn}: the attempt budget "
            f"({certificate_lifecycle.MAX_ISSUE_ATTEMPTS}) is spent ({failure.code})"
        ),
        level=EventLevel.ERROR,
        actor_type=ActorType.SYSTEM,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "attempts": attempt,
            "code": failure.code,
        },
        org_id=generation.org_id,
    )
    await alert_service.create_alert(
        db,
        event_type="CERTIFICATE_FAILED",
        severity=alert_service.severity_for_event("CERTIFICATE_FAILED"),
        title=f"Certificate issuance failed for {certificate.primary_cn}",
        body=(
            f"Attempt {attempt} of {certificate_lifecycle.MAX_ISSUE_ATTEMPTS} failed "
            f"({failure.code}) and no further attempt is scheduled for this generation. "
            "Nothing has been issued and nothing is being served. Fix the cause and request "
            "issuance again."
        ),
        source="certificate",
        resource_type="certificate",
        resource_id=str(certificate.id),
    )
    log.error(
        "issuance_failed",
        certificate=str(certificate.id),
        generation=generation.generation,
        attempt=attempt,
        code=failure.code,
    )


async def _publish_success(
    db: AsyncSession,
    certificate: Certificate,
    generation: CertificateGeneration,
    material: _Material,
    *,
    directory: AcmeDirectory,
    attempt: int,
) -> None:
    """Record the issuance: an event, an audit entry and a log line. No material."""
    await event_bus.publish(
        db,
        type="CERTIFICATE_ISSUED",
        message=f"Certificate issued for {certificate.primary_cn} by the {directory.label}",
        actor_type=ActorType.SYSTEM,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "attempt": attempt,
            # Metadata about the material, never the material: the fingerprint is a
            # non-reversible handle, and the window is what a renewal reasons about.
            "fingerprint": material.fingerprint,
            "not_before": material.not_before.isoformat(),
            "not_after": material.not_after.isoformat(),
            "directory": directory.value,
            "directory_url": directory.url(),
        },
        org_id=generation.org_id,
    )
    await audit_service.record(
        db,
        None,
        action="certificate.issued",
        resource_type="certificate",
        resource_id=certificate.id,
        metadata={
            "primary_cn": certificate.primary_cn,
            "generation": generation.generation,
            "fingerprint": material.fingerprint,
            "not_after": material.not_after.isoformat(),
            "directory": directory.value,
        },
        org_id=generation.org_id,
    )
    log.info(
        "certificate_issuance_recorded",
        certificate=str(certificate.id),
        generation=generation.generation,
        directory=directory.value,
    )


__all__ = [
    "CODE_ATTEMPTS_EXHAUSTED",
    "CODE_ATTEMPT_ERROR",
    "CODE_ATTEMPT_IN_FLIGHT",
    "CODE_AWAITING_MANUAL",
    "CODE_CONTEXT_INCOMPLETE",
    "CODE_DIRECTORY_CHANGED",
    "CODE_DNS_CREDENTIAL_MISSING",
    "CODE_DOCUMENT_UNSUPPORTED",
    "CODE_DOMAIN_NOT_VERIFIED",
    "CODE_MANUAL_CHALLENGE_INVALID",
    "CODE_MANUAL_NOT_PENDING",
    "CODE_MATERIAL_MISMATCH",
    "CODE_NOT_DUE",
    "CODE_ORDER_LOST",
    "CODE_ORDER_MISMATCH",
    "CODE_WORKER_LOST",
    "MAX_IDENTIFIERS",
    "IssuanceAttempt",
    "ManualChallengeStatus",
    "confirm_manual_publication",
    "enqueue_generation",
    "issue_generation",
    "manual_challenge",
    "request_retry",
]
