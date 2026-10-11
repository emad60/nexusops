"""The pre-issuance certificate lifecycle — pure decisions, no I/O, no side effects.

Phase 5.1 ships the *metadata* half of the certificate subsystem: an identity
row, its generations, and the state machine that says which transitions are
legal. Nothing here issues anything. The module is deliberately free of database
access, HTTP and Celery so the rules can be tested exhaustively and reused by the
issuance worker (5.3) unchanged — "decide" and "do" are separate steps, and the
only thing a caller learns here is whether a move is legal.

The vocabulary itself is bounded by
:class:`~app.models.enums.CertificateGenerationState`, which in this phase holds
only the states a generation can occupy **before any material exists**:

    PENDING → ORDERING → CHALLENGE_PUBLISHED → VALIDATING → (FAILED)
    FAILED  → ORDERING                                   (retry, bounded)

The design's post-issuance states (``ISSUED``, ``SUPERSEDED``, ``EXPIRED``,
``SUSPENDED``, the revocation axis) arrive in Phase 5.2 together with the key
envelope they describe. Until then they are **unrepresentable**: not enum
members, not accepted by the database CHECK, and refused by
:func:`assert_pre_issuance` if a caller — say an older worker reading a newer row
— ever hands one in. That is the difference between "we do not issue yet" and "an
issued row could be written anyway".
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.enums import CertificateGenerationState, CertificateStatus

#: Where every new generation starts: created, ordered by nobody yet.
INITIAL_STATE = CertificateGenerationState.PENDING

#: Attempts allowed per generation before it is terminal. Matches the design's
#: budget (§5.5); the delay below is the same exponential backoff.
MAX_ISSUE_ATTEMPTS = 5

#: First retry delay, doubled per attempt: 5, 10, 20, 40, 80 minutes.
_BASE_DELAY_SECONDS = 300
_MAX_DELAY_SECONDS = 24 * 60 * 60

#: The legal moves of the pre-issuance machine. ``FAILED`` may be retried, and
#: everything else moves forward exactly one step, so an attempt cannot skip the
#: challenge it never published.
TRANSITIONS: dict[CertificateGenerationState, frozenset[CertificateGenerationState]] = {
    CertificateGenerationState.PENDING: frozenset(
        {CertificateGenerationState.ORDERING, CertificateGenerationState.FAILED}
    ),
    CertificateGenerationState.ORDERING: frozenset(
        {CertificateGenerationState.CHALLENGE_PUBLISHED, CertificateGenerationState.FAILED}
    ),
    CertificateGenerationState.CHALLENGE_PUBLISHED: frozenset(
        {CertificateGenerationState.VALIDATING, CertificateGenerationState.FAILED}
    ),
    CertificateGenerationState.VALIDATING: frozenset({CertificateGenerationState.FAILED}),
    CertificateGenerationState.FAILED: frozenset({CertificateGenerationState.ORDERING}),
}


class InvalidTransition(ValueError):
    """Two pre-issuance states with no legal move between them."""

    def __init__(self, current: object, target: object) -> None:
        super().__init__(f"a certificate generation cannot move from {current!r} to {target!r}")
        self.current = current
        self.target = target


class UnrepresentableState(ValueError):
    """A generation state this phase's schema cannot express.

    Raised for the post-issuance vocabulary (``ISSUED`` and friends), which
    Phase 5.2 introduces with the key material it implies. A caller seeing this
    is not looking at a bug in the state machine: it is looking at a value that
    no Phase 5.1 row can hold.
    """

    def __init__(self, value: object) -> None:
        super().__init__(
            f"{value!r} is not a pre-issuance certificate generation state: material-bearing "
            "states (ISSUED, SUPERSEDED, EXPIRED, SUSPENDED, the revocation states) are "
            "introduced by Phase 5.2"
        )
        self.value = value


def _utcnow() -> datetime:
    return datetime.now(UTC)


def coerce_state(value: object) -> CertificateGenerationState | None:
    """The enum member for *value*, or ``None`` when it names no state at all."""
    if isinstance(value, CertificateGenerationState):
        return value
    if isinstance(value, str):
        try:
            return CertificateGenerationState(value)
        except ValueError:
            return None
    return None


def assert_pre_issuance(value: object) -> CertificateGenerationState:
    """Return *value* as a pre-issuance state, or refuse it loudly.

    This is the guard the whole slice rests on: ``ISSUED`` is not merely unused
    here, it is not a value this schema can hold, so anything that claims to be
    one is a contradiction rather than a state to handle.
    """
    state = coerce_state(value)
    if state is None:
        raise UnrepresentableState(value)
    return state


def can_transition(current: object, target: object) -> bool:
    """Whether *current* may move to *target* under the pre-issuance machine."""
    from_state = coerce_state(current)
    to_state = coerce_state(target)
    if from_state is None or to_state is None:
        return False
    return to_state in TRANSITIONS.get(from_state, frozenset())


def require_transition(current: object, target: object) -> CertificateGenerationState:
    """The target state, or :class:`InvalidTransition` when the move is illegal."""
    resolved = coerce_state(target)
    if resolved is None or not can_transition(current, resolved):
        raise InvalidTransition(current, target)
    return resolved


def retry_budget_exhausted(attempt_count: int) -> bool:
    """Whether a generation has spent every attempt it was allowed."""
    return attempt_count >= MAX_ISSUE_ATTEMPTS


def is_retryable(state: object, attempt_count: int) -> bool:
    """Whether a failed generation may be moved back to ``ORDERING``.

    A failure is retryable only while the attempt budget lasts; once it is spent
    the generation is terminal and a fresh generation is the only way forward.
    """
    return coerce_state(state) is CertificateGenerationState.FAILED and not retry_budget_exhausted(
        attempt_count
    )


def is_terminal(state: object, attempt_count: int) -> bool:
    """Whether this generation will never move again."""
    return coerce_state(state) is CertificateGenerationState.FAILED and retry_budget_exhausted(
        attempt_count
    )


def attempt_delay_seconds(attempt_count: int) -> int:
    """Exponential backoff after *attempt_count* spent attempts, capped at 24h."""
    exponent = max(1, attempt_count) - 1
    return min(_BASE_DELAY_SECONDS * (2**exponent), _MAX_DELAY_SECONDS)


def next_attempt_at(attempt_count: int, *, now: datetime | None = None) -> datetime:
    """When the next attempt on a generation becomes due."""
    return (now or _utcnow()) + timedelta(seconds=attempt_delay_seconds(attempt_count))


#: The certificate statuses a pre-issuance generation may be reported as. Every
#: other member of :class:`CertificateStatus` describes material.
_PRE_ISSUANCE_STATUS: dict[CertificateGenerationState, CertificateStatus] = {
    CertificateGenerationState.PENDING: CertificateStatus.PENDING,
    CertificateGenerationState.ORDERING: CertificateStatus.PENDING,
    CertificateGenerationState.CHALLENGE_PUBLISHED: CertificateStatus.PENDING,
    CertificateGenerationState.VALIDATING: CertificateStatus.PENDING,
    CertificateGenerationState.FAILED: CertificateStatus.FAILED,
}


def certificate_status_for(state: object) -> CertificateStatus:
    """The certificate-level status implied by a generation's state.

    Derived, never stored by the caller: the row's own ``status`` column is a
    denormalized view of exactly this function, so a certificate cannot claim to
    be issued while its generation is still being ordered. ``ISSUED`` is
    unreachable by construction in Phase 5.1 — there is no input that maps to it.
    """
    return _PRE_ISSUANCE_STATUS[assert_pre_issuance(state)]


def status_detail_for(state: object, attempt_count: int = 0) -> str:
    """A short, sanitized sentence for ``status``. Never key material.

    The wording is load-bearing: a request that has not been issued must never
    read as if it had been, so every pre-issuance line says so explicitly.
    """
    resolved = assert_pre_issuance(state)
    if resolved is CertificateGenerationState.PENDING:
        return "Requested — no certificate has been issued yet"
    if resolved is CertificateGenerationState.ORDERING:
        return "An order is being placed with the certificate authority — nothing is issued yet"
    if resolved is CertificateGenerationState.CHALLENGE_PUBLISHED:
        return "Ownership challenge published — nothing is issued yet"
    if resolved is CertificateGenerationState.VALIDATING:
        return "Waiting for the certificate authority to validate the challenge — nothing is issued yet"
    if is_terminal(resolved, attempt_count):
        return (
            f"Issuance failed and the attempt budget ({MAX_ISSUE_ATTEMPTS}) is spent — no "
            "certificate has been issued"
        )
    if is_retryable(resolved, attempt_count):
        return (
            f"Issuance attempt {attempt_count} of {MAX_ISSUE_ATTEMPTS} failed — nothing is "
            "issued; another attempt is scheduled"
        )
    return "Issuance failed — no certificate has been issued yet"
