"""Has the challenge record actually reached the authoritative nameservers?

Publishing a TXT record through a provider's API returns as soon as the *provider*
accepted it. That is not the same fact as "the name's authoritative servers
answer with it", and the difference is the whole reason this module exists:

* a CA resolves the challenge name through its own recursive resolvers, so a
  record that only exists in the provider's API — or in one zone's cache — fails
  validation and burns an attempt, an order and a CA-side failure count;
* an operator *saying* they published a record is a claim, not an observation
  (phase5-design.md §5.3). The manual path therefore runs the same check the
  automated path runs, and only a positive observation lets the flow tell the CA
  a challenge is ready.

So the policy is: ask the authoritative servers, repeatedly, until the expected
value is visible or a **hard deadline** passes. Both halves matter — a single
negative check would fail a zone that is merely a few seconds behind, and an
unbounded wait would hold a worker open for a record the customer never published.

Two properties this module keeps deliberately:

* the deadline is the only thing that ends the loop, and it is checked before every
  sleep, so an attempt cannot overrun by one poll interval plus a DNS budget;
* **every authoritative server that answered must serve every expected value**
  before the record counts as propagated. A negative answer from one server is
  never final while there is time left, and — the mirror of that rule — a
  *positive* answer from one server is not enough while another server that
  answered still lacks the value. A zone whose servers disagree is mid-
  propagation, and telling a CA "ready" then is what makes a validation fail for
  a reason the platform could already see.

A server that **did not answer** (timeout, SERVFAIL, transport error) is a
separate fact from one that answered without the value: it is recorded per server
and reported, and it does not by itself block readiness, because the platform
cannot observe a value a server refuses to serve — a CA may well not reach that
server either. The distinction is preserved rather than collapsed into "all" or
"any", and it is visible in :attr:`PropagationResult.nameserver_answers`.

Nothing here writes anything or answers an ACME server: it observes, and returns
an observation with a truthful status for the caller to act on.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.services.dns_verifier import (
    DNS_TOTAL_BUDGET,
    STATUS_ERROR,
    STATUS_NO_TXT,
    STATUS_NXDOMAIN,
    STATUS_OK,
    STATUS_SERVFAIL,
    STATUS_TIMEOUT,
    ServerAnswer,
    TxtObservation,
    observe_txt_record,
)

log = get_logger("nexusops.dns_propagation")

#: How long to wait before looking again. Short relative to the deadline (120s by
#: default) so a record that is already live is accepted almost immediately, and
#: long enough that a slow zone is not hammered.
PROPAGATION_POLL_SECONDS = 10.0

#: Result statuses. ``PROPAGATED`` is the only one a caller may act on.
STATUS_PROPAGATED = "PROPAGATED"
STATUS_MISSING = "MISSING"
STATUS_PENDING = "PENDING"
STATUS_NO_AUTHORITATIVE_NS = "NO_AUTHORITATIVE_NS"
STATUS_DNS_UNAVAILABLE = "DNS_UNAVAILABLE"

#: Statuses that mean "keep waiting if there is time left": the observation itself
#: is inconclusive rather than a verdict about the record.
_RETRYABLE_STATUSES = frozenset(
    {
        STATUS_NXDOMAIN,
        STATUS_TIMEOUT,
        STATUS_SERVFAIL,
        STATUS_ERROR,
        STATUS_NO_TXT,
        "MALFORMED",
    }
)

#: Statuses in which a server gave an **authoritative answer about the name**.
#: Every one of them is evidence: it means the server holds the zone, so its
#: silence about a value is a fact about the zone rather than about the network.
_ANSWERED_STATUSES = frozenset({STATUS_OK, STATUS_NO_TXT, STATUS_NXDOMAIN})


def _observer_name(observation: TxtObservation) -> str:
    return observation.status


@dataclass(frozen=True, slots=True)
class TxtExpectation:
    """One TXT record name and **every** value that must be present there.

    A set rather than a single value because one name legitimately carries several
    challenge values: ``example.com`` and ``*.example.com`` are two authorizations
    for the same identifier, so both DNS-01 values are published at
    ``_acme-challenge.example.com`` at the same time. Requiring all of them before
    saying "ready" is also what makes cleanup target the record this platform
    created instead of "the" TXT record at that name (§5.3).
    """

    name: str
    values: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a TXT expectation needs a record name")
        if not self.values:
            raise ValueError(f"no expected TXT value was given for {self.name!r}")

    def missing_from(self, observed: Sequence[str]) -> tuple[str, ...]:
        """The expected values absent from *observed*, in expectation order."""
        others = [str(value).strip() for value in observed]
        return tuple(value for value in self.values if value not in others)


@dataclass(frozen=True, slots=True)
class PropagationResult:
    """What the authoritative servers said about a set of expectations.

    ``observed`` is the last thing each name's authoritative servers returned, kept
    so a failure can report the *actual* state — the difference between "nothing is
    published" and "something else is published there" is the first thing an
    operator needs, and neither is a secret (both are public DNS data).
    """

    ok: bool
    status: str
    attempts: int
    elapsed_seconds: float
    expectations: tuple[TxtExpectation, ...]
    observed: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    nameservers: tuple[str, ...] = ()
    detail: str = ""
    #: What each authoritative address said, per record name. Empty when the
    #: observer returned only an aggregate answer (a seam, not the wire).
    nameserver_answers: Mapping[str, tuple[ServerAnswer, ...]] = field(default_factory=dict)

    @property
    def pending_names(self) -> tuple[str, ...]:
        """The record names whose expectation is not satisfied yet.

        Judged exactly the way :func:`evaluate` judged the round — per server when
        the round kept per-server answers. A report built from the union would
        claim a name is done because one server served it, which is the same
        mistake this module now refuses to make when deciding.
        """
        pending: list[str] = []
        for expectation in self.expectations:
            answers = self.nameserver_answers.get(expectation.name, ())
            if answers:
                answered = [answer for answer in answers if answer.status in _ANSWERED_STATUSES]
                if answered and all(
                    answer.status == STATUS_OK and not expectation.missing_from(answer.values)
                    for answer in answered
                ):
                    continue
                pending.append(expectation.name)
                continue
            if expectation.missing_from(self.observed.get(expectation.name, ())):
                pending.append(expectation.name)
        return tuple(pending)


#: The seam a test replaces: takes a record name, returns what authoritative DNS
#: says about it. Defaults to the real observation, and is a parameter everywhere
#: rather than a module global so no test can leave a process-wide stub behind.
Observer = Callable[[str], TxtObservation]


def evaluate(
    expectations: Sequence[TxtExpectation], observations: Mapping[str, TxtObservation]
) -> tuple[bool, str, str]:
    """Fold one round of observations into ``(ok, status, detail)``. **Pure.**

    ``ok`` is true only when every expectation is satisfied by an authoritative
    answer **from every server that answered**. The status distinguishes the two
    ways that can fail, because they call for different things:
    ``NO_AUTHORITATIVE_NS`` is a configuration problem (the name has no delegation
    this platform can see — a typo'd zone, a domain not using the provider's
    nameservers), while anything else means the record is not being served *yet*
    and is worth waiting for.
    """
    if not expectations:
        return False, STATUS_MISSING, "no challenge record was expected"

    unsatisfied: list[str] = []
    pending = False
    reasons: list[str] = []
    for expectation in expectations:
        observation = observations.get(expectation.name)
        if observation is None:
            return False, STATUS_ERROR, "no observation was made for one of the challenge records"
        if observation.status == "NO_NAMESERVERS" and not observation.nameservers:
            return (
                False,
                STATUS_NO_AUTHORITATIVE_NS,
                f"no authoritative nameserver was found for {expectation.name}, so the "
                "challenge record cannot be observed by a certificate authority",
            )
        satisfied, inconclusive, detail = _verdict(expectation, observation)
        if satisfied:
            continue
        unsatisfied.append(expectation.name)
        pending = pending or inconclusive
        if detail and detail not in reasons and len(reasons) < 3:
            reasons.append(detail)

    if not unsatisfied:
        return True, STATUS_PROPAGATED, ""
    message = (
        "the challenge record is not visible at the authoritative nameservers yet "
        f"({len(unsatisfied)} of {len(expectations)} record"
        f"{'' if len(expectations) == 1 else 's'} still missing)"
    )
    if reasons:
        message = f"{message}: {'; '.join(reasons)}"
    return False, STATUS_PENDING if pending else STATUS_MISSING, message


def _verdict(expectation: TxtExpectation, observation: TxtObservation) -> tuple[bool, bool, str]:
    """``(satisfied, inconclusive, detail)`` for one name across every server seen.

    Two rules, and the second is the one this module exists to get right:

    * a server that answered authoritatively without every expected value **vetoes**
      readiness even when another server serves them all — that is a disagreement,
      and waiting is how it resolves;
    * a server that did not answer is recorded, not treated as agreement. It cannot
      supply evidence either way, and blocking forever on a server the platform
      cannot reach would make an unreachable secondary a permanent outage.
    """
    answers = observation.server_answers
    if not answers:
        # An aggregate-only observation: there is exactly one answer to judge, and
        # a status that may simply mean "not there yet".
        if observation.status == STATUS_OK:
            if not expectation.missing_from(observation.values):
                return True, False, ""
            return (
                False,
                False,
                "the authoritative answer does not carry the expected value",
            )
        return False, observation.status in _RETRYABLE_STATUSES, observation.detail

    answered = [answer for answer in answers if answer.status in _ANSWERED_STATUSES]
    agreeing = [
        answer
        for answer in answered
        if answer.status == STATUS_OK and not expectation.missing_from(answer.values)
    ]
    if answered and len(agreeing) == len(answered):
        return True, False, ""
    if agreeing:
        return (
            False,
            True,
            f"the value is served by {len(agreeing)} of {len(answered)} authoritative "
            "nameservers that answered; the others do not serve it yet",
        )
    if not answered:
        return False, True, observation.detail or "no authoritative nameserver answered"
    if all(answer.status == STATUS_OK for answer in answered):
        # Every server that answered holds TXT records and none is this value: an
        # authoritative verdict, not a delay — unless a server was unreachable, in
        # which case this round is still inconclusive.
        return (
            False,
            len(answered) < len(answers),
            "the authoritative answer does not carry the expected value",
        )
    return False, True, observation.detail or "no authoritative nameserver serves the value yet"


def observe(
    expectations: Sequence[TxtExpectation], *, observer: Observer, budget: float
) -> tuple[dict[str, TxtObservation], float]:
    """One round: observe every expected name. Returns the round and its elapsed time."""
    started = time.monotonic()
    observations: dict[str, TxtObservation] = {}
    for expectation in expectations:
        observations[expectation.name] = observer_window(observer, expectation.name, budget)
    return observations, time.monotonic() - started


def observer_window(observer: Observer, name: str, budget: float) -> TxtObservation:
    """Call *observer* for *name*, converting an unexpected exception into an

    observation. A resolver that raises (misconfiguration, a library bug) must not
    take down a worker whose only crime was asking about a name, and the failure has
    to be visible as a DNS status rather than as a task crash.
    """
    try:
        return observer(name)
    except Exception as exc:  # pragma: no cover - only a broken resolver reaches this
        log.warning("dns_observation_failed", name=name, error=exc.__class__.__name__)
        return TxtObservation(STATUS_ERROR, detail="the DNS observation failed")


def wait_for_txt_records(
    expectations: Sequence[TxtExpectation],
    *,
    timeout_seconds: float,
    interval_seconds: float = PROPAGATION_POLL_SECONDS,
    observer: Observer | None = None,
    budget: float = DNS_TOTAL_BUDGET,
) -> PropagationResult:
    """Poll the authoritative servers until every value is visible, or the deadline.

    The deadline is checked *before* each sleep and each round, and every round is
    bounded by its own DNS budget, so the total wait stays inside
    ``timeout_seconds`` plus at most one observation budget. A timeout is a normal
    result — the record may still be propagating — so it is returned, not raised.
    """
    observer = observer or observe_txt_record
    deadline = time.monotonic() + max(timeout_seconds, 1.0)
    expected = tuple(expectations)
    if not expected:
        return PropagationResult(
            ok=False,
            status=STATUS_MISSING,
            attempts=0,
            elapsed_seconds=0.0,
            expectations=(),
            detail="no challenge record was expected",
        )

    started = time.monotonic()
    attempts = 0
    last_observations: dict[str, TxtObservation] = {}
    last_status = STATUS_PENDING
    last_detail = ""

    while True:
        attempts += 1
        last_observations, _elapsed = observe(expected, observer=observer, budget=budget)
        ok, last_status, last_detail = evaluate(expected, last_observations)
        if ok:
            break
        if last_status == STATUS_NO_AUTHORITATIVE_NS:
            # Waiting cannot fix a name with no authoritative delegation.
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            last_status = STATUS_TIMEOUT if last_status == STATUS_PENDING else last_status
            last_detail = last_detail or "the challenge record did not appear in time"
            break
        time.sleep(min(interval_seconds, remaining))

    nameservers: tuple[str, ...] = ()
    observed: dict[str, tuple[str, ...]] = {}
    per_server: dict[str, tuple[ServerAnswer, ...]] = {}
    for name, observation in last_observations.items():
        observed[name] = observation.values
        if observation.server_answers:
            per_server[name] = observation.server_answers
        if observation.nameservers:
            nameservers = observation.nameservers
    result = PropagationResult(
        ok=last_status == STATUS_PROPAGATED,
        status=last_status,
        attempts=attempts,
        elapsed_seconds=round(time.monotonic() - started, 3),
        expectations=expected,
        observed=observed,
        nameservers=nameservers,
        detail=last_detail,
        nameserver_answers=per_server,
    )
    log.info(
        "dns_propagation_checked",
        status=result.status,
        records=len(expected),
        attempts=attempts,
        elapsed_seconds=result.elapsed_seconds,
    )
    return result


__all__ = [
    "PROPAGATION_POLL_SECONDS",
    "STATUS_DNS_UNAVAILABLE",
    "STATUS_MISSING",
    "STATUS_NO_AUTHORITATIVE_NS",
    "STATUS_PENDING",
    "STATUS_PROPAGATED",
    "Observer",
    "PropagationResult",
    "TxtExpectation",
    "evaluate",
    "observe",
    "wait_for_txt_records",
]
