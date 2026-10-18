"""Unit tests for the DNS propagation wait.

Publishing a record is not the same fact as the authoritative servers answering with
it, so this module's contract is narrow and easy to get subtly wrong: a positive
observation must be enough, a negative one must never be final before the deadline,
and a name with no delegation must fail immediately rather than burn the wait.
"""

from __future__ import annotations

import pytest
from app.services import dns_propagation as propagation
from app.services.dns_verifier import (
    STATUS_NO_TXT,
    STATUS_NXDOMAIN,
    STATUS_OK,
    STATUS_SERVFAIL,
    STATUS_TIMEOUT,
    ServerAnswer,
    TxtObservation,
)

EXPECTATION = propagation.TxtExpectation(name="_acme-challenge.example.com", values=("value-a",))


def _ok(*values: str, nameservers: tuple[str, ...] = ("ns1.example.net",)) -> TxtObservation:
    return TxtObservation(STATUS_OK, values=tuple(values), nameservers=nameservers)


def _servers(
    *answers: tuple[str, str, tuple[str, ...]],
) -> TxtObservation:
    """A per-server observation, exactly what ``observe_txt_record`` returns."""
    entries = tuple(
        ServerAnswer(server=server, status=status, values=values)
        for server, status, values in answers
    )
    return TxtObservation(
        STATUS_OK,
        values=tuple(dict.fromkeys(value for _s, _st, values in answers for value in values)),
        nameservers=("ns1.example.net", "ns2.example.net"),
        server_answers=entries,
    )


class _Clock:
    """A monotonic clock that only moves when something sleeps."""

    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


# --- expectations --------------------------------------------------------------


def test_expectation_requires_a_name_and_a_value() -> None:
    with pytest.raises(ValueError):
        propagation.TxtExpectation(name="", values=("v",))
    with pytest.raises(ValueError):
        propagation.TxtExpectation(name="n", values=())


def test_missing_from_strips_observed_values_and_keeps_expectation_order() -> None:
    expectation = propagation.TxtExpectation(name="n", values=("a", "b", "c"))
    assert expectation.missing_from((" a ", "b")) == ("c",)
    assert expectation.missing_from(("a", "b", "c", "extra")) == ()


# --- evaluate ------------------------------------------------------------------


def test_evaluate_requires_an_expectation() -> None:
    assert propagation.evaluate((), {}) == (
        False,
        propagation.STATUS_MISSING,
        "no challenge record was expected",
    )


def test_evaluate_needs_an_observation_for_every_name() -> None:
    ok, status, detail = propagation.evaluate((EXPECTATION,), {})
    assert (ok, status) == (False, propagation.STATUS_ERROR)
    assert "no observation" in detail


def test_evaluate_accepts_complete_authoritative_answers() -> None:
    ok, status, detail = propagation.evaluate((EXPECTATION,), {EXPECTATION.name: _ok("value-a")})
    assert (ok, status, detail) == (True, propagation.STATUS_PROPAGATED, "")


def test_evaluate_reports_a_subset_as_missing_not_pending() -> None:
    # An authoritative "OK" that lacks the value is a verdict, not a delay.
    ok, status, detail = propagation.evaluate((EXPECTATION,), {EXPECTATION.name: _ok("other")})
    assert (ok, status) == (False, propagation.STATUS_MISSING)
    assert "1 of 1" in detail


@pytest.mark.parametrize("observed_status", [STATUS_NXDOMAIN, STATUS_SERVFAIL, "NO_TXT", "TIMEOUT"])
def test_evaluate_calls_inconclusive_answers_pending(observed_status: str) -> None:
    ok, status, _ = propagation.evaluate(
        (EXPECTATION,), {EXPECTATION.name: TxtObservation(observed_status)}
    )
    assert (ok, status) == (False, propagation.STATUS_PENDING)


def test_evaluate_refuses_a_name_without_authoritative_delegation() -> None:
    ok, status, detail = propagation.evaluate(
        (EXPECTATION,), {EXPECTATION.name: TxtObservation("NO_NAMESERVERS")}
    )
    assert (ok, status) == (False, propagation.STATUS_NO_AUTHORITATIVE_NS)
    assert EXPECTATION.name in detail


def test_evaluate_reports_the_unsatisfied_count_across_names() -> None:
    second = propagation.TxtExpectation(name="_acme-challenge.other.test", values=("value-b",))
    ok, status, detail = propagation.evaluate(
        (EXPECTATION, second),
        {EXPECTATION.name: _ok("value-a"), second.name: _ok("something-else")},
    )
    assert (ok, status) == (False, propagation.STATUS_MISSING)
    assert "1 of 2 records still missing" in detail


# --- wait loop -----------------------------------------------------------------


def test_wait_returns_a_missing_result_without_an_expectation() -> None:
    result = propagation.wait_for_txt_records((), timeout_seconds=1)
    assert result.ok is False
    assert result.status == propagation.STATUS_MISSING
    assert result.attempts == 0


def test_wait_accepts_an_immediately_visible_record(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)

    result = propagation.wait_for_txt_records(
        (EXPECTATION,), timeout_seconds=120, observer=lambda name: _ok("value-a")
    )
    assert result.ok is True
    assert result.status == propagation.STATUS_PROPAGATED
    assert result.attempts == 1
    assert clock.slept == []
    assert result.nameservers == ("ns1.example.net",)
    assert result.observed == {EXPECTATION.name: ("value-a",)}


def test_wait_retries_until_the_value_appears(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)
    answers = iter([TxtObservation(STATUS_NXDOMAIN), _ok("value-a")])

    result = propagation.wait_for_txt_records(
        (EXPECTATION,),
        timeout_seconds=120,
        interval_seconds=10,
        observer=lambda name: next(answers),
    )
    assert result.ok is True
    assert result.attempts == 2
    assert clock.slept == [10]


def test_wait_stops_at_the_deadline_and_reports_a_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)

    result = propagation.wait_for_txt_records(
        (EXPECTATION,),
        timeout_seconds=20,
        interval_seconds=10,
        observer=lambda name: TxtObservation(STATUS_NXDOMAIN),
    )
    assert result.ok is False
    assert result.status == propagation.STATUS_TIMEOUT
    # Two full intervals plus the final look that observes the deadline passed.
    assert result.attempts == 3
    # The last sleep is bounded by the remaining budget, never the full interval.
    assert sum(clock.slept) <= 20


def test_wait_does_not_hold_a_worker_for_a_name_with_no_delegation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)

    result = propagation.wait_for_txt_records(
        (EXPECTATION,),
        timeout_seconds=300,
        observer=lambda name: TxtObservation("NO_NAMESERVERS"),
    )
    assert result.ok is False
    assert result.status == propagation.STATUS_NO_AUTHORITATIVE_NS
    assert result.attempts == 1
    assert clock.slept == []


def test_wait_keeps_the_last_observation_for_the_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)

    result = propagation.wait_for_txt_records(
        (EXPECTATION,),
        timeout_seconds=10,
        interval_seconds=10,
        observer=lambda name: _ok("wrong-value", nameservers=("ns9.example.net",)),
    )
    assert result.ok is False
    assert result.status == propagation.STATUS_MISSING
    assert result.observed[EXPECTATION.name] == ("wrong-value",)
    assert result.nameservers == ("ns9.example.net",)
    assert result.pending_names == (EXPECTATION.name,)


def test_observer_failure_becomes_a_dns_status_not_a_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)

    def broken(name: str) -> TxtObservation:
        raise RuntimeError("resolver exploded")

    result = propagation.wait_for_txt_records(
        (EXPECTATION,),
        timeout_seconds=10,
        interval_seconds=10,
        observer=broken,
    )
    assert result.status == propagation.STATUS_TIMEOUT
    assert result.attempts == 2


def test_observer_window_converts_an_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(name: str) -> TxtObservation:
        raise ValueError("no")

    observation = propagation.observer_window(broken, EXPECTATION.name, budget=1.0)
    assert observation.status == "ERROR"
    assert observation.values == ()


# --- authoritative agreement (the mixed-answer case) -----------------------------


def test_one_positive_answer_does_not_override_a_stale_authoritative_server() -> None:
    """The defect this policy closes: one server's positive answer is not a verdict.

    Two nameservers, one serving the freshly published value and one still serving
    the previous value. Telling the CA "ready" here would start validation against
    a zone that has not converged, so the round must stay pending.
    """
    observation = _servers(
        ("192.0.2.1", STATUS_OK, ("value-a",)),
        ("192.0.2.2", STATUS_OK, ("value-old",)),
    )
    ok, status, detail = propagation.evaluate((EXPECTATION,), {EXPECTATION.name: observation})
    assert ok is False
    assert status == propagation.STATUS_PENDING, "a disagreement is a delay, not a verdict"
    assert "1 of 2 authoritative nameservers" in detail


def test_an_absent_answer_from_another_server_also_vetoes_readiness() -> None:
    observation = _servers(
        ("192.0.2.1", STATUS_OK, ("value-a",)),
        ("192.0.2.2", STATUS_NO_TXT, ()),
    )
    ok, status, detail = propagation.evaluate((EXPECTATION,), {EXPECTATION.name: observation})
    assert (ok, status) == (False, propagation.STATUS_PENDING)
    assert "1 of 2" in detail


def test_every_answering_server_must_serve_every_expected_value() -> None:
    # Apex + wildcard share one record name and publish two values. A server that
    # serves only one of them is a server the CA may ask and get half an answer.
    expectation = propagation.TxtExpectation(
        name="_acme-challenge.example.com", values=("value-a", "value-b")
    )
    observation = _servers(
        ("192.0.2.1", STATUS_OK, ("value-a", "value-b")),
        ("192.0.2.2", STATUS_OK, ("value-a",)),
    )
    ok, status, _ = propagation.evaluate((expectation,), {expectation.name: observation})
    assert (ok, status) == (False, propagation.STATUS_PENDING)

    converged = _servers(
        ("192.0.2.1", STATUS_OK, ("value-a", "value-b")),
        ("192.0.2.2", STATUS_OK, ("value-a", "value-b")),
    )
    ok, status, detail = propagation.evaluate((expectation,), {expectation.name: converged})
    assert (ok, status, detail) == (True, propagation.STATUS_PROPAGATED, "")


def test_unreachable_server_is_recorded_but_does_not_block_agreement() -> None:
    # The platform cannot observe a value a server refuses to serve, and a CA may
    # not reach it either: the servers that *did* answer all agree.
    observation = _servers(
        ("192.0.2.1", STATUS_OK, ("value-a",)),
        ("192.0.2.2", STATUS_TIMEOUT, ()),
    )
    ok, status, _ = propagation.evaluate((EXPECTATION,), {EXPECTATION.name: observation})
    assert (ok, status) == (True, propagation.STATUS_PROPAGATED)

    result = propagation.wait_for_txt_records(
        (EXPECTATION,), timeout_seconds=5, observer=lambda name: observation
    )
    assert result.ok is True
    assert result.nameserver_answers[EXPECTATION.name][1].status == STATUS_TIMEOUT


def test_no_answering_server_is_pending_not_propagated() -> None:
    observation = _servers(
        ("192.0.2.1", STATUS_TIMEOUT, ()),
        ("192.0.2.2", STATUS_SERVFAIL, ()),
    )
    ok, status, _ = propagation.evaluate((EXPECTATION,), {EXPECTATION.name: observation})
    assert (ok, status) == (False, propagation.STATUS_PENDING)


def test_every_answering_server_holding_other_values_is_an_authoritative_verdict() -> None:
    observation = _servers(
        ("192.0.2.1", STATUS_OK, ("value-old",)),
        ("192.0.2.2", STATUS_OK, ("value-old",)),
    )
    ok, status, _ = propagation.evaluate((EXPECTATION,), {EXPECTATION.name: observation})
    assert (ok, status) == (False, propagation.STATUS_MISSING)


def test_wait_converges_only_after_the_stale_server_catches_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)
    rounds = iter(
        [
            _servers(
                ("192.0.2.1", STATUS_OK, ("value-a",)),
                ("192.0.2.2", STATUS_OK, ("value-old",)),
            ),
            _servers(
                ("192.0.2.1", STATUS_OK, ("value-a",)),
                ("192.0.2.2", STATUS_OK, ("value-a",)),
            ),
        ]
    )

    result = propagation.wait_for_txt_records(
        (EXPECTATION,), timeout_seconds=120, interval_seconds=10, observer=lambda name: next(rounds)
    )
    assert result.ok is True
    assert result.attempts == 2
    assert clock.slept == [10]


def test_wait_reports_the_disagreement_when_the_deadline_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock()
    monkeypatch.setattr(propagation, "time", clock)
    stale = _servers(
        ("192.0.2.1", STATUS_OK, ("value-a",)),
        ("192.0.2.2", STATUS_OK, ("value-old",)),
    )

    result = propagation.wait_for_txt_records(
        (EXPECTATION,), timeout_seconds=20, interval_seconds=10, observer=lambda name: stale
    )
    assert result.ok is False
    assert result.status == propagation.STATUS_TIMEOUT
    assert "1 of 2 authoritative nameservers" in result.detail
    assert result.pending_names == (EXPECTATION.name,)
