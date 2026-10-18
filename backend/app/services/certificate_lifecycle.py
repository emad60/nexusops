"""The certificate lifecycle — pure decisions, no I/O, no side effects.

The whole state machine lives here as data, so the rules can be tested
exhaustively and reused unchanged by the issuance worker (5.3): "decide" and "do"
are separate steps, and the only thing a caller learns here is whether a move is
legal.

Phase 5.1 held the pre-issuance half only, and the vocabulary itself was
truncated so that a material-bearing row was *unrepresentable*. Phase 5.2.2
widens it to the full machine, in the same slice that adds the material columns
and the organization DEK envelope those states require, plus the **material guard
CHECK** that makes the widening safe: a generation in any post-issuance state must
carry ``key_ciphertext``, ``chain_ciphertext``, ``deke_id``, ``issued_at``,
``not_before`` and ``not_after``. So the property 5.1 bought — "there is no window
in which an issued generation lacks its key material" — is preserved, now by a
constraint instead of by the absence of the column.

The machine (phase5-design.md §2.2):

    PENDING → ORDERING → CHALLENGE_PUBLISHED → VALIDATING → ISSUED
    ORDERING → AWAITING_MANUAL → CHALLENGE_PUBLISHED        (manual DNS-01)
    AWAITING_MANUAL → ORDERING                              (re-order, e.g. expired)
    AWAITING_MANUAL → FAILED
    FAILED → AWAITING_MANUAL                                (retry: order still open)
    ISSUED  → SUPERSEDED | SUSPENDED | EXPIRED | REVOCATION_PENDING
    SUPERSEDED → SUSPENDED | REVOCATION_PENDING
    SUSPENDED  → REVOCATION_PENDING
    EXPIRED    → REVOCATION_PENDING
    REVOCATION_PENDING → REVOKED | REVOCATION_FAILED
    REVOCATION_FAILED  → REVOCATION_PENDING | REVOKED_LOCAL_ONLY
    FAILED → ORDERING                                    (retry, bounded)
    REVOKED, REVOKED_LOCAL_ONLY                          (terminal)

Two deliberate additions to the design's diagram, both recorded in the
:data:`TRANSITIONS` table rather than left implicit: a ``SUPERSEDED`` or
``EXPIRED`` generation may still be revoked (§9.5's manual revoke must not be
blocked by the fact that a newer generation replaced this one, or by its
``notAfter`` having passed), and ``REVOCATION_FAILED`` can end at
``REVOKED_LOCAL_ONLY`` when the CA never answered and the material was removed
anyway — the design's own distinction between "the CA refused" and "the CA never
answered".

Two axes stay separate, on purpose (§2.2): ``state`` says whether the material is
usable, ``revocation_state`` records the CA conversation. Nothing here ever makes
"stop serving this material" wait for the CA.
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

#: The legal moves of the whole machine. ``FAILED`` may be retried while its
#: budget lasts, and every forward step is explicit, so an attempt cannot skip the
#: challenge it never published and a superseded generation cannot silently become
#: current again.
TRANSITIONS: dict[CertificateGenerationState, frozenset[CertificateGenerationState]] = {
    CertificateGenerationState.PENDING: frozenset(
        {CertificateGenerationState.ORDERING, CertificateGenerationState.FAILED}
    ),
    CertificateGenerationState.ORDERING: frozenset(
        {
            CertificateGenerationState.CHALLENGE_PUBLISHED,
            # The manual DNS-01 branch: the order is placed and the attempt stops
            # deliberately, because publishing the record is the customer's act.
            CertificateGenerationState.AWAITING_MANUAL,
            CertificateGenerationState.FAILED,
        }
    ),
    # A manual generation waits for an operator without holding a worker. Both ways
    # out are legal and mean different things: an authoritative observation that
    # passed moves it forward, and a fresh order (the previous one expired, or the
    # document was unreadable) goes back through ``ORDERING``. ``FAILED`` is for a
    # failure the platform recorded while resuming — never for "the operator has not
    # confirmed yet", which is the state itself.
    CertificateGenerationState.AWAITING_MANUAL: frozenset(
        {
            CertificateGenerationState.ORDERING,
            CertificateGenerationState.CHALLENGE_PUBLISHED,
            CertificateGenerationState.FAILED,
        }
    ),
    CertificateGenerationState.CHALLENGE_PUBLISHED: frozenset(
        {CertificateGenerationState.VALIDATING, CertificateGenerationState.FAILED}
    ),
    CertificateGenerationState.VALIDATING: frozenset(
        {CertificateGenerationState.ISSUED, CertificateGenerationState.FAILED}
    ),
    CertificateGenerationState.FAILED: frozenset(
        {
            CertificateGenerationState.ORDERING,
            # A retry of a manual generation whose order is still open does not
            # re-order: it observes the record the operator already published and,
            # when that observation has not happened yet, goes back to waiting
            # rather than handing out a second set of instructions.
            CertificateGenerationState.AWAITING_MANUAL,
        }
    ),
    CertificateGenerationState.ISSUED: frozenset(
        {
            CertificateGenerationState.SUPERSEDED,
            CertificateGenerationState.SUSPENDED,
            CertificateGenerationState.EXPIRED,
            CertificateGenerationState.REVOCATION_PENDING,
        }
    ),
    CertificateGenerationState.SUPERSEDED: frozenset(
        {
            CertificateGenerationState.SUSPENDED,
            # Deliberate addition: a manual revoke (§9.5) must not be refused
            # because a newer generation has already replaced this one.
            CertificateGenerationState.REVOCATION_PENDING,
        }
    ),
    CertificateGenerationState.SUSPENDED: frozenset(
        {CertificateGenerationState.REVOCATION_PENDING}
    ),
    CertificateGenerationState.EXPIRED: frozenset(
        # Deliberate addition: ``notAfter`` passing does not make a key
        # unrevokable — an expired certificate is still worth revoking.
        {CertificateGenerationState.REVOCATION_PENDING}
    ),
    CertificateGenerationState.REVOCATION_PENDING: frozenset(
        {CertificateGenerationState.REVOKED, CertificateGenerationState.REVOCATION_FAILED}
    ),
    CertificateGenerationState.REVOCATION_FAILED: frozenset(
        {
            CertificateGenerationState.REVOCATION_PENDING,
            CertificateGenerationState.REVOKED_LOCAL_ONLY,
        }
    ),
    CertificateGenerationState.REVOKED: frozenset(),
    CertificateGenerationState.REVOKED_LOCAL_ONLY: frozenset(),
}


class InvalidTransition(ValueError):
    """Two states with no legal move between them."""

    def __init__(self, current: object, target: object) -> None:
        super().__init__(f"a certificate generation cannot move from {current!r} to {target!r}")
        self.current = current
        self.target = target


class UnrepresentableState(ValueError):
    """A state the caller's context cannot accept.

    Two callers narrow differently and both refusals are loud:

    * the **pre-issuance path** (creating a generation) refuses a material-bearing
      state, because a fresh generation cannot already have material — the message
      says which kind of value was handed in;
    * anything handed a value that names **no** state at all refuses it as
      unknown, rather than guessing a default.
    """

    def __init__(
        self, value: object, *, expectation: str = "a certificate generation state"
    ) -> None:
        super().__init__(f"{value!r} is not {expectation}")
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


def assert_state(value: object) -> CertificateGenerationState:
    """Return *value* as a state, or refuse a value that names none."""
    state = coerce_state(value)
    if state is None:
        raise UnrepresentableState(value)
    return state


def assert_pre_issuance(value: object) -> CertificateGenerationState:
    """Return *value* as a pre-issuance state, or refuse it loudly.

    The narrowing the *creation* path uses: a generation that has just been
    requested has no material and cannot claim a state that requires some. This is
    a check on the caller's intent, not on the schema any more — Phase 5.2.2's
    material guard CHECK is what makes a material-less ``ISSUED`` row impossible.
    """
    state = assert_state(value)
    if material_required(state):
        raise UnrepresentableState(
            value,
            expectation=(
                "a pre-issuance certificate generation state: a fresh generation cannot "
                "already carry key material, and every material-bearing state requires it"
            ),
        )
    return state


def assert_material_bearing(value: object) -> CertificateGenerationState:
    """Return *value* as a state that **must** carry material, or refuse it.

    The mirror of :func:`assert_pre_issuance`, for the issuance path: a caller
    about to write a chain and a key must be in a state the guard CHECK expects
    material for, otherwise the write would be rejected by the database and the
    bug would surface as an IntegrityError rather than as this.
    """
    state = assert_state(value)
    if not material_required(state):
        raise UnrepresentableState(
            value,
            expectation=(
                "a material-bearing certificate generation state: a generation still being "
                "ordered has nothing to store yet"
            ),
        )
    return state


def material_required(state: object) -> bool:
    """Whether a generation in *state* must carry its material and ``deke_id``.

    Derived from the enum, so this predicate, the model's guard CHECK and the
    migration's constraint cannot drift: they all read
    :meth:`CertificateGenerationState.material_bearing`.
    """
    return assert_state(state) in CertificateGenerationState.material_bearing()


def can_transition(current: object, target: object) -> bool:
    """Whether *current* may move to *target*."""
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
    """Whether this generation will never move again.

    ``REVOKED`` and ``REVOKED_LOCAL_ONLY`` have no outgoing edge; ``FAILED`` is
    terminal once its budget is spent. Everything else can still move — an expired
    or superseded generation is still revocable, and a suspension is still a step
    on the way to revocation.
    """
    resolved = coerce_state(state)
    if resolved is CertificateGenerationState.FAILED:
        return retry_budget_exhausted(attempt_count)
    return resolved in {
        CertificateGenerationState.REVOKED,
        CertificateGenerationState.REVOKED_LOCAL_ONLY,
    }


def attempt_delay_seconds(attempt_count: int) -> int:
    """Exponential backoff after *attempt_count* spent attempts, capped at 24h."""
    exponent = max(1, attempt_count) - 1
    return min(_BASE_DELAY_SECONDS * (2**exponent), _MAX_DELAY_SECONDS)


def next_attempt_at(attempt_count: int, *, now: datetime | None = None) -> datetime:
    """When the next attempt on a generation becomes due."""
    return (now or _utcnow()) + timedelta(seconds=attempt_delay_seconds(attempt_count))


#: The certificate-level status a generation implies. Derived, never stored by the
#: caller: the certificate row's own ``status`` column is a denormalized view of
#: exactly this mapping, so a certificate cannot claim to be issued while its
#: generation is still being ordered.
#:
#: Two deliberate collapses, both because the certificate status vocabulary is
#: smaller than the generation one: ``SUPERSEDED`` reports as ``ISSUED`` (the
#: material exists and may still be serving until it is removed) and
#: ``REVOCATION_FAILED`` reports as ``REVOCATION_PENDING`` (the CA conversation is
#: unfinished, which is what that status says; "failed" is a retry detail shown on
#: the generation, not a certificate-level fact).
_STATUS_FOR: dict[CertificateGenerationState, CertificateStatus] = {
    CertificateGenerationState.PENDING: CertificateStatus.PENDING,
    CertificateGenerationState.ORDERING: CertificateStatus.PENDING,
    CertificateGenerationState.AWAITING_MANUAL: CertificateStatus.PENDING,
    CertificateGenerationState.CHALLENGE_PUBLISHED: CertificateStatus.PENDING,
    CertificateGenerationState.VALIDATING: CertificateStatus.PENDING,
    CertificateGenerationState.FAILED: CertificateStatus.FAILED,
    CertificateGenerationState.ISSUED: CertificateStatus.ISSUED,
    CertificateGenerationState.SUPERSEDED: CertificateStatus.ISSUED,
    CertificateGenerationState.SUSPENDED: CertificateStatus.SUSPENDED,
    CertificateGenerationState.EXPIRED: CertificateStatus.EXPIRED,
    CertificateGenerationState.REVOCATION_PENDING: CertificateStatus.REVOCATION_PENDING,
    CertificateGenerationState.REVOCATION_FAILED: CertificateStatus.REVOCATION_PENDING,
    CertificateGenerationState.REVOKED: CertificateStatus.REVOKED,
    CertificateGenerationState.REVOKED_LOCAL_ONLY: CertificateStatus.REVOKED_LOCAL_ONLY,
}


def certificate_status_for(state: object) -> CertificateStatus:
    """The certificate-level status implied by a generation's state."""
    return _STATUS_FOR[assert_state(state)]


def status_detail_for(state: object, attempt_count: int = 0) -> str:
    """A short, sanitized sentence for ``status``. Never key material."""
    resolved = assert_state(state)
    if resolved is CertificateGenerationState.PENDING:
        return "Requested — no certificate has been issued yet"
    if resolved is CertificateGenerationState.ORDERING:
        return "An order is being placed with the certificate authority — nothing is issued yet"
    if resolved is CertificateGenerationState.AWAITING_MANUAL:
        return (
            "Waiting for the challenge record to be published and confirmed — nothing is issued yet"
        )
    if resolved is CertificateGenerationState.CHALLENGE_PUBLISHED:
        return "Ownership challenge published — nothing is issued yet"
    if resolved is CertificateGenerationState.VALIDATING:
        return "Waiting for the certificate authority to validate the challenge — nothing is issued yet"
    if resolved is CertificateGenerationState.FAILED:
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
    if resolved is CertificateGenerationState.ISSUED:
        return "Issued — the chain and key are stored and await delivery"
    if resolved is CertificateGenerationState.SUPERSEDED:
        return (
            "Superseded by a newer generation — its material is kept until every node has "
            "stopped serving it"
        )
    if resolved is CertificateGenerationState.SUSPENDED:
        return "Suspended — its identifiers are not authorized to be served; the material is kept"
    if resolved is CertificateGenerationState.EXPIRED:
        return "Expired — the certificate authority's notAfter has passed"
    if resolved is CertificateGenerationState.REVOCATION_PENDING:
        return "Revocation requested — waiting for the certificate authority"
    if resolved is CertificateGenerationState.REVOCATION_FAILED:
        return (
            "Revocation attempt did not succeed — retried within a bounded budget; serving this "
            "material is already stopped independently of the authority"
        )
    if resolved is CertificateGenerationState.REVOKED:
        return "Revoked — the certificate authority acknowledged it"
    return (
        "Material removed locally but the certificate authority never acknowledged the "
        "revocation — this is not the same as a completed revocation"
    )
