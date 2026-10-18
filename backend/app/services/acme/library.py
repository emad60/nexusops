"""The ``acme`` package behind :mod:`app.services.acme` — the only import of it.

Everything RFC 8555 here belongs to the library: the directory, nonce and
``Replay-Nonce`` handling, the JWS envelope, the order state machine, the
``Retry-After`` parser. This module is an **adapter**, and the two things it adds are
the two the library deliberately leaves to its caller:

* **Bounded waiting.** ``ClientV2.poll()`` performs exactly one POST-as-GET and
  returns the response, so the loop, its deadline and the honoring of
  ``Retry-After`` are ours. Every wait is bounded by a wall-clock deadline the
  Celery soft time limit can contain, and the CA's ``Retry-After`` is used exactly
  (through the library's own ``ClientV2.retry_after``), never replaced by a fixed
  sleep.
* **Blocking work off the event loop.** The client is synchronous, so every call runs
  in a worker thread through :func:`asyncio.to_thread`. This code only ever runs
  inside a Celery worker, whose entry point already owns an event loop
  (:func:`app.tasks._util.run_async`), so nothing here can stall an API request.

Two safety properties that are *not* delegated to the library:

* the account key is loaded from PEM for one attempt, used to build the client, and
  dropped when the session closes. It is never persisted, logged, or put in an order.
* an unrecognized exception is reported by **class name only**. Third-party exception
  text is attacker-influenced input from the network, and a JWS-signed request is
  exactly the object whose ``repr`` must never reach a log or a database column.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

import josepy as jose
from acme import challenges, client, messages
from acme import errors as acme_errors
from cryptography.hazmat.primitives import serialization

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import AcmeDirectory
from app.services.acme import (
    AcmeChallenge,
    AcmeConfigError,
    AcmeOrder,
    AcmeProtocolError,
    AcmeSession,
    AcmeTimeout,
    AcmeUnavailable,
    AuthorizationState,
    IssuedChain,
    classify_error,
    sanitize_detail,
)
from app.services.acme.directory import AcmeDirectoryError, assert_issuance_allowed

log = get_logger("nexusops.acme.library")

#: Per-request HTTP timeout for the synchronous client. Well under an attempt's
#: deadline: a hung socket must not consume the whole challenge budget.
HTTP_TIMEOUT_SECONDS = 30

#: Sent as ``User-Agent``. Some CAs use it to attribute traffic; it carries nothing
#: tenant-specific and nothing that identifies a key.
USER_AGENT = "nexusops-control-plane"

#: Fallback spacing between authorization polls when the CA sent no ``Retry-After``.
DEFAULT_POLL_SECONDS = 5.0

#: Bound on a single poll sleep, whatever ``Retry-After`` asked for. A CA asking for
#: 30 minutes is honored *by the deadline check* — the attempt ends and the backoff
#: formula takes over — rather than by holding a worker for thirty minutes.
MAX_POLL_SLEEP_SECONDS = 60.0

#: The account key's algorithm. Fixed together with the account's P-256 key in
#: :mod:`app.services.acme_account_service`: a JWK and an algorithm that disagree
#: produce signatures the CA cannot verify.
ACCOUNT_KEY_ALGORITHM = jose.ES256

T = TypeVar("T")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _finalize_deadline(timeout_seconds: float) -> datetime:
    """The deadline ``acme`` expects: **naive local time**, at least one second out.

    ``acme``'s ``poll_finalization`` compares the value with
    ``datetime.datetime.now()``. Keeping the rule in one function means the
    inevitable question — "aware or naive?" — has one answer that can be asserted
    directly, instead of being re-derived (and re-broken) inside a network call.
    """
    return datetime.now() + timedelta(seconds=max(timeout_seconds, 1.0))


def _status_text(value: Any) -> str:
    """An ACME status as the plain string this module compares and stores.

    ``acme.messages.Status`` is **not** a string: it is a ``josepy`` constant whose
    ``str()`` is ``"Status(valid)"``. Passing that through meant a freshly polled
    authorization never compared equal to ``STATUS_PENDING``, so the poll loop
    returned on its first round with a status no caller recognized: a successfully
    validated challenge read as a local validation timeout, and a refusal read as
    neither. ``.name`` is the canonical member name (``"valid"``); the ``str()``
    of a *plain* string is itself, so both shapes normalise to one vocabulary.
    Found by the Pebble integration test (``test_certificate_pebble``) — a fake
    session returning literal strings could not expose it.
    """
    name = getattr(value, "name", None)
    if isinstance(name, str) and name:
        return name.lower()
    text = str(value).strip()
    if text.startswith("Status(") and text.endswith(")"):
        return text[len("Status(") : -1].lower()
    return text.lower()


def _classify(exc: Exception) -> Exception:
    """Map a library or transport exception onto this platform's failure vocabulary.

    Returning an object rather than raising keeps the translation in one place and
    lets the caller ``raise ... from None``: the original traceback of a signed
    request is not something to keep.
    """
    if isinstance(exc, messages.Error):
        detail = sanitize_detail(str(exc.detail or ""))
        raw_code = exc.code or str(exc.typ).rsplit(":", maxsplit=1)[-1]
        return classify_error(raw_code or "", detail)
    if isinstance(exc, acme_errors.IssuanceError):
        return _classify(exc.error)
    if isinstance(exc, acme_errors.TimeoutError):
        return AcmeTimeout(
            "the certificate authority did not answer within this attempt's deadline",
            code="ACME_POLL_TIMEOUT",
        )
    if isinstance(exc, acme_errors.BadNonce):
        return AcmeUnavailable(
            "the certificate authority rejected a request nonce; the attempt must be repeated",
            code="ACME_BAD_NONCE",
        )
    if isinstance(exc, acme_errors.ValidationError):
        # The CA could not verify a challenge. Often the authoritative nameservers had
        # not converged for the *CA's* resolver yet, so this is retryable within
        # budget — the attempt already re-queried the zone before saying "ready".
        return AcmeUnavailable(
            "the certificate authority could not validate a challenge",
            code="ACME_VALIDATION_FAILED",
        )
    if isinstance(exc, acme_errors.NonceError):
        return AcmeUnavailable(
            "the certificate authority's nonce exchange failed", code="ACME_NONCE_ERROR"
        )
    # Deliberately name-only: this text reaches a database column and an API response,
    # and the exception may be a transport error wrapping a signed request.
    return AcmeUnavailable(
        "the ACME request failed", code="ACME_REQUEST_FAILED", detail=type(exc).__name__
    )


def _execute(function: Any, *args: Any, **kwargs: Any) -> Any:
    """Run one blocking client call, translating any failure.

    Every call a session makes goes through here, so there is exactly one place where
    a library exception becomes an :class:`~app.services.acme.AcmeError`, and no raw
    library exception can escape into the worker's failure handler.
    """
    try:
        return function(*args, **kwargs)
    except Exception as exc:  # translated below into a named, sanitized failure
        raise _classify(exc) from None


class _LibrarySession:
    """One attempt's ACME conversation over the maintained client.

    Concurrency: methods are sequential by contract (the flow awaits each one), and
    the client's mutable state — nonce pool, account handle, order resource — is only
    touched inside the worker thread a call runs in. There is no lock because there is
    no concurrent caller: a session is created per attempt and never shared.
    """

    def __init__(
        self, directory: AcmeDirectory, *, account_key_pem: str, account_url: str | None
    ) -> None:
        self.directory = directory
        self._account_key_pem = account_key_pem
        self._account_url = account_url
        self._key: jose.JWKEC | None = None
        self._net: client.ClientNetwork | None = None
        self._client: client.ClientV2 | None = None
        #: The order resource from ``create_order``, kept in memory for finalization.
        #: Public data plus the CSR; never the certificate key.
        self._orderr: messages.OrderResource | None = None
        #: The challenges this attempt created, by challenge URL, so
        #: ``accept_challenge`` can only ever answer a challenge in this order.
        self._challenges: dict[str, messages.ChallengeBody] = {}
        self._authz: dict[str, messages.AuthorizationResource] = {}

    # --- lifecycle ---------------------------------------------------------

    async def __aenter__(self) -> _LibrarySession:
        await asyncio.to_thread(self._connect)
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()

    def _connect(self) -> None:
        """Build the key, the transport and the client. Blocking."""
        settings = get_settings()
        # The same gate the settings validator applies, re-applied where the socket is
        # opened: a production directory reached from a test or a development process
        # is not recoverable — real rate limits, real certificates for names nobody
        # asked for.
        try:
            assert_issuance_allowed(self.directory, settings=settings)
        except AcmeDirectoryError as exc:
            raise AcmeConfigError(
                f"issuance from the '{self.directory.value}' directory is not allowed in "
                "this environment",
                code=exc.code,
            ) from None

        private_key = serialization.load_pem_private_key(
            self._account_key_pem.encode("utf-8"), password=None
        )
        self._key = jose.JWKEC(key=private_key)
        # TLS verification is relaxed for exactly one directory, and that directory
        # cannot be reached in production: Pebble serves its own self-signed test
        # certificate, and trusting it anywhere else would be the bug.
        verify_ssl = self.directory is not AcmeDirectory.PEBBLE
        self._net = client.ClientNetwork(
            key=self._key,
            alg=ACCOUNT_KEY_ALGORITHM,
            verify_ssl=verify_ssl,
            user_agent=USER_AGENT,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        directory_resource = client.ClientV2.get_directory(self.directory.url(), self._net)
        self._client = client.ClientV2(directory_resource, self._net)
        if self._account_url:
            # Present the stored account URL as the JWS ``kid``. The CA answers for
            # that account only if this key really is its key, so a corrupted or
            # repointed URL fails at the first signed request instead of signing as
            # somebody else.
            self._net.account = messages.RegistrationResource(
                body=messages.Registration.from_json({}), uri=self._account_url
            )

    async def close(self) -> None:
        """Drop the account key and the transport. Nothing here outlives an attempt."""
        self._account_key_pem = ""
        self._key = None
        self._client = None
        self._orderr = None
        self._challenges.clear()
        self._authz.clear()
        net, self._net = self._net, None
        if net is not None:
            net.session.close()

    def _require_client(self) -> tuple[client.ClientV2, jose.JWKEC]:
        if self._client is None or self._key is None:
            raise AcmeConfigError(
                "the ACME session is not connected", code="ACME_SESSION_NOT_CONNECTED"
            )
        return self._client, self._key

    # --- operations --------------------------------------------------------

    async def register_account(self, *, contact_email: str | None = None) -> str:
        """Register the account, or adopt the CA's answer that it already exists."""
        return await asyncio.to_thread(self._register_account, contact_email)

    def _register_account(self, contact_email: str | None) -> str:
        acme_client, _ = self._require_client()
        registration = messages.NewRegistration.from_data(
            email=contact_email or None, terms_of_service_agreed=True
        )

        def _call() -> str:
            try:
                regr = acme_client.new_account(registration)
            except acme_errors.ConflictError as conflict:
                # The key already has an account: the CA refuses to create it twice and
                # names the existing one. Adopting that URL is what makes concurrent
                # first-time registration converge on one authoritative account.
                location = str(conflict.location or "").strip()
                if not location or location == "UNKNOWN-LOCATION":
                    raise AcmeProtocolError(
                        "the certificate authority reported an existing account without naming it",
                        code="ACME_ACCOUNT_LOCATION_MISSING",
                    ) from None
                return location
            uri = str(regr.uri or "").strip()
            if not uri:
                raise AcmeProtocolError(
                    "the certificate authority registered the account without returning its URL",
                    code="ACME_ACCOUNT_LOCATION_MISSING",
                )
            return uri

        return _execute(_call)

    async def create_order(self, *, csr_pem: bytes, identifiers: tuple[str, ...]) -> AcmeOrder:
        return await asyncio.to_thread(self._create_order, csr_pem, identifiers)

    def _create_order(self, csr_pem: bytes, identifiers: tuple[str, ...]) -> AcmeOrder:
        acme_client, key = self._require_client()
        requested = {name.lower().rstrip(".") for name in identifiers}

        def _call() -> AcmeOrder:
            orderr = acme_client.new_order(csr_pem)
            self._orderr = orderr
            granted = {
                str(identifier.value).lower().rstrip(".")
                for identifier in (orderr.body.identifiers or ())
            }
            # The CA derives the order's identifiers from the CSR it was handed. If that
            # set is not exactly what the operator asked for, our CSR asked the wrong
            # question — and ordering on would store material for names nobody
            # requested.
            if granted != requested:
                raise AcmeProtocolError(
                    "the certificate authority's order covers a different identifier set "
                    "than the request",
                    code="ACME_ORDER_IDENTIFIERS_MISMATCH",
                    detail=f"requested {len(requested)}, offered {len(granted)}",
                )
            return self._collected(orderr, key, identifiers=tuple(sorted(granted)))

        return _execute(_call)

    async def resume_order(self, *, order_url: str) -> AcmeOrder:
        return await asyncio.to_thread(self._resume_order, order_url)

    def _resume_order(self, order_url: str) -> AcmeOrder:
        """Re-open an order this process did not create, by its URL.

        Needed by the manual DNS-01 path for a structural reason: an attempt's key
        pair lives only in the attempt that generated it, so the attempt that placed
        a manual order cannot be the one that finalizes it — an operator publishes
        the TXT record minutes or hours later. The order is one *pure data* fact
        inside that attempt (URL, authorizations, challenges), which is exactly what
        this method re-reads from the CA.

        RFC 8555 has no "return this order" endpoint beyond a POST-as-GET of its
        URL, so this uses the client's own primitives (``_post_as_get`` and
        ``_authzr_from_response``), the same two ``new_order`` uses internally. They
        are private API: pinning that is the honest cost of resuming at all, and it
        is tested against a real CA in the Pebble suite rather than only against a
        fake.

        An **invalid** or **deactivated** order is not resumed. Answering for a
        challenge the CA has already judged would report a success that never
        happened, so it is refused here and the flow places a new order instead.
        """
        acme_client, key = self._require_client()
        url = str(order_url or "").strip()
        if not url:
            raise AcmeProtocolError(
                "there is no recorded order URL to resume", code="ACME_ORDER_URL_MISSING"
            )

        def _call() -> AcmeOrder:
            response = acme_client._post_as_get(url)
            body = messages.Order.from_json(response.json())
            status = _status_text(body.status)
            if status in {messages.STATUS_INVALID, messages.STATUS_DEACTIVATED}:
                raise AcmeProtocolError(
                    "the recorded order is no longer usable at the certificate authority",
                    code="ACME_ORDER_UNUSABLE",
                    detail=f"order status {status}",
                )
            authorizations = []
            for authorization_url in body.authorizations or ():
                authorizations.append(
                    acme_client._authzr_from_response(
                        acme_client._post_as_get(authorization_url), uri=authorization_url
                    )
                )
            orderr = messages.OrderResource(
                body=body, uri=url, authorizations=authorizations, csr_pem=b""
            )
            self._orderr = orderr
            return self._collected(
                orderr,
                key,
                identifiers=tuple(
                    sorted(str(identifier.value) for identifier in body.identifiers or ())
                ),
            )

        return _execute(_call)

    def _collected(
        self, orderr: messages.OrderResource, key: jose.JWKEC, *, identifiers: tuple[str, ...]
    ) -> AcmeOrder:
        """Read one order's dns-01 challenges into the seam's own shape.

        Shared by ``create_order`` and ``resume_order`` so a resumed order yields
        exactly the same challenge fields a fresh one did: the token and the TXT
        value the operator was handed have to be *the same values* on the resume
        path, and two parsers would be two chances to disagree.
        """
        collected: list[AcmeChallenge] = []
        for authzr in orderr.authorizations:
            body = authzr.body
            identifier = str(body.identifier.value)
            self._authz[authzr.uri] = authzr
            for challb in body.challenges or ():
                if challb.typ != challenges.DNS01.typ:
                    continue
                if not isinstance(challb.chall, challenges.DNS01):
                    raise AcmeProtocolError(
                        "the certificate authority returned a dns-01 challenge of an "
                        "unexpected shape",
                        code="ACME_CHALLENGE_UNSUPPORTED",
                    )
                self._challenges[challb.uri] = challb
                collected.append(
                    AcmeChallenge(
                        identifier=identifier,
                        wildcard=bool(body.wildcard),
                        authorization_url=authzr.uri,
                        challenge_url=challb.uri,
                        token=str(challb.token),
                        record_name=challb.chall.validation_domain_name(identifier),
                        record_value=str(challb.chall.validation(key)),
                        key_authorization=challb.chall.key_authorization(key),
                        status=_status_text(challb.status),
                    )
                )
        if not collected:
            raise AcmeProtocolError(
                "the certificate authority returned no dns-01 challenge for this order",
                code="ACME_NO_DNS01_CHALLENGE",
            )
        return AcmeOrder(
            order_url=_order_url(orderr),
            status=_status_text(orderr.body.status),
            challenges=tuple(collected),
            expires_at=orderr.body.expires,
            identifiers=identifiers,
        )

    async def accept_challenge(self, *, challenge_url: str) -> None:
        await asyncio.to_thread(self._accept_challenge, challenge_url)

    def _accept_challenge(self, challenge_url: str) -> None:
        acme_client, key = self._require_client()
        challb = self._challenges.get(challenge_url)
        if challb is None:
            raise AcmeProtocolError(
                "this attempt has no challenge with that URL; refusing to answer a "
                "challenge it did not create",
                code="ACME_UNKNOWN_CHALLENGE",
            )
        challenge = challb.chall
        if not isinstance(challenge, challenges.DNS01):
            raise AcmeProtocolError(
                "this attempt's challenge is not a dns-01 challenge",
                code="ACME_CHALLENGE_UNSUPPORTED",
            )

        def _call() -> None:
            acme_client.answer_challenge(challb, challenge.response(key))

        _execute(_call)

    async def poll_authorization(
        self, *, authorization_url: str, timeout_seconds: float
    ) -> AuthorizationState:
        return await asyncio.to_thread(self._poll_authorization, authorization_url, timeout_seconds)

    def _poll_authorization(
        self, authorization_url: str, timeout_seconds: float
    ) -> AuthorizationState:
        """Poll until the authorization leaves ``pending``, or the deadline passes.

        The loop is ours because the library's ``poll()`` is a single round trip: that
        is what makes ``Retry-After`` honor-able *and* the wait boundable at the same
        time. The CA's delay is used as it asked; the deadline caps it; and reaching
        the deadline is a named timeout, not an unbounded wait.
        """
        acme_client, _ = self._require_client()
        authzr = self._authz.get(authorization_url)
        if authzr is None:
            raise AcmeProtocolError(
                "this attempt has no authorization with that URL",
                code="ACME_UNKNOWN_AUTHORIZATION",
            )
        deadline = _utcnow() + timedelta(seconds=max(timeout_seconds, 1.0))

        def _call() -> AuthorizationState:
            current = authzr
            while True:
                current, response = acme_client.poll(current)
                self._authz[authorization_url] = current
                status = _status_text(current.body.status)
                if status != messages.STATUS_PENDING:
                    error_code, error_detail = _first_error(current)
                    return AuthorizationState(
                        status=status, error_code=error_code, error_detail=error_detail
                    )
                remaining = (deadline - _utcnow()).total_seconds()
                if remaining <= 0:
                    raise AcmeTimeout(
                        "the certificate authority was still validating this challenge "
                        "when the attempt's deadline passed",
                        code="ACME_VALIDATION_TIMEOUT",
                    )
                requested = acme_client.retry_after(response, int(DEFAULT_POLL_SECONDS))
                delay = (requested - _utcnow()).total_seconds()
                time.sleep(min(max(delay, 1.0), MAX_POLL_SLEEP_SECONDS, remaining))

        return _execute(_call)

    async def finalize_order(self, *, csr_pem: bytes, timeout_seconds: float) -> IssuedChain:
        return await asyncio.to_thread(self._finalize_order, csr_pem, timeout_seconds)

    def _finalize_order(self, csr_pem: bytes, timeout_seconds: float) -> IssuedChain:
        acme_client, _ = self._require_client()
        orderr = self._orderr
        if orderr is None:
            raise AcmeProtocolError(
                "there is no order to finalize in this attempt", code="ACME_NO_ORDER"
            )
        # The deadline handed to the library is **naive local time**, because that is
        # the contract ``acme`` implements: ``poll_finalization`` compares it against
        # ``datetime.datetime.now()``. An aware datetime here raises ``TypeError``
        # inside the library before the CA is ever asked, which made finalization
        # impossible against every real CA while the fake sessions hid it. Found by
        # the Pebble integration test (``test_certificate_pebble``); the contract
        # lives in :func:`_finalize_deadline` so a unit test can pin it.
        deadline = _finalize_deadline(timeout_seconds)
        # The CSR belongs to *this* attempt, not to the order's earlier life. A resumed
        # manual order is finalized with the key generated after validation, while the
        # resource re-read from the CA carries no CSR at all — handing the library the
        # resource as-is makes it parse an empty CSR and fail before the CA is asked.
        # Found by the manual DNS-01 Pebble test, which is the only path that resumes.
        orderr = orderr.update(csr_pem=csr_pem)
        self._orderr = orderr

        def _call() -> IssuedChain:
            finalized = acme_client.finalize_order(orderr, deadline)
            chain = finalized.fullchain_pem or ""
            if not chain.strip():
                raise AcmeProtocolError(
                    "the certificate authority finalized the order without a certificate",
                    code="ACME_EMPTY_CHAIN",
                )
            return IssuedChain(fullchain_pem=chain, order_url=_order_url(orderr))

        return _execute(_call)


def _first_error(authzr: messages.AuthorizationResource) -> tuple[str, str]:
    """The first challenge error on an authorization, as (code, sanitized detail)."""
    for challb in authzr.body.challenges or ():
        error = challb.error
        if error is None:
            continue
        raw_code = error.code or str(error.typ).rsplit(":", maxsplit=1)[-1]
        return raw_code or "", sanitize_detail(str(error.detail or ""))
    return "", ""


def _order_url(orderr: messages.OrderResource) -> str:
    """The order's URL. Every later step needs it, so a missing one is an error."""
    uri = str(orderr.uri or "").strip()
    if not uri:
        raise AcmeProtocolError(
            "the certificate authority did not return an order URL",
            code="ACME_ORDER_URL_MISSING",
        )
    return uri


class LibraryAcmeProvider:
    """The ``acme``-package implementation of :class:`~app.services.acme.AcmeProvider`."""

    def __init__(self, directory: AcmeDirectory) -> None:
        self.directory = directory

    @asynccontextmanager
    async def open_session(
        self, *, account_key_pem: str, account_url: str | None
    ) -> AsyncIterator[AcmeSession]:
        """One attempt's session, connected off the event loop.

        The ``finally`` closes the session even when the flow forgets to: the account
        key's lifetime is the attempt's, and relying on every caller to end it would
        make that a convention instead of a property.
        """
        session = _LibrarySession(
            self.directory, account_key_pem=account_key_pem, account_url=account_url
        )
        try:
            async with session:
                yield session
        finally:
            await session.close()


__all__ = [
    "ACCOUNT_KEY_ALGORITHM",
    "DEFAULT_POLL_SECONDS",
    "HTTP_TIMEOUT_SECONDS",
    "MAX_POLL_SLEEP_SECONDS",
    "USER_AGENT",
    "LibraryAcmeProvider",
]
