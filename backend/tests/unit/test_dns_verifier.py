"""The verification decision: every outcome, without a network.

``decide`` is where anti-takeover lives, so each rule gets a case here — a token
match with a changed delegation, a sweep that must invalidate versus a user
re-verification that must accept, and the four ways DNS can simply not answer.
"""

from __future__ import annotations

import pytest
from app.services.dns_verifier import (
    REASON_DNS_UNAVAILABLE,
    REASON_NO_NAMESERVERS,
    REASON_NS_CHANGED,
    REASON_TXT_MISMATCH,
    REASON_TXT_MISSING,
    REASON_VERIFIED,
    STATUS_ERROR,
    STATUS_MALFORMED,
    STATUS_NO_NAMESERVERS,
    STATUS_NO_TXT,
    STATUS_NXDOMAIN,
    STATUS_OK,
    STATUS_SERVFAIL,
    STATUS_TIMEOUT,
    TxtObservation,
    decide,
    matches_token,
)

TOKEN = "nxs-verify-abc123"
NS = ("ns1.example.net", "ns2.example.net")


def observation(**kwargs) -> TxtObservation:
    values = kwargs.pop("values", (TOKEN,))
    return TxtObservation(
        status=kwargs.pop("status", STATUS_OK),
        values=values,
        nameservers=kwargs.pop("nameservers", NS),
        detail=kwargs.pop("detail", ""),
    )


def test_token_match_verifies_and_stores_the_nameserver_snapshot() -> None:
    decision = decide(
        observation(), expected_token=TOKEN, ns_snapshot=(), require_snapshot_match=False
    )
    assert decision.ok
    assert decision.reason == REASON_VERIFIED
    assert decision.ns_snapshot == NS
    assert not decision.ns_changed


def test_token_mismatch_does_not_verify() -> None:
    decision = decide(
        observation(values=("nxs-verify-wrong",)),
        expected_token=TOKEN,
        ns_snapshot=(),
        require_snapshot_match=False,
    )
    assert not decision.ok
    assert decision.reason == REASON_TXT_MISMATCH
    # The expected token never appears in the explanation.
    assert TOKEN not in decision.detail


def test_missing_txt_record_is_reported_separately_from_a_wrong_value() -> None:
    for status in (STATUS_NO_TXT, STATUS_NXDOMAIN):
        decision = decide(
            observation(status=status, values=()),
            expected_token=TOKEN,
            ns_snapshot=(),
            require_snapshot_match=False,
        )
        assert not decision.ok
        assert decision.reason == REASON_TXT_MISSING


@pytest.mark.parametrize("status", [STATUS_TIMEOUT, STATUS_SERVFAIL, STATUS_ERROR])
def test_unavailable_authoritative_dns_is_a_distinct_reason(status: str) -> None:
    decision = decide(
        observation(status=status, values=()),
        expected_token=TOKEN,
        ns_snapshot=(),
        require_snapshot_match=False,
    )
    assert not decision.ok
    assert decision.reason == REASON_DNS_UNAVAILABLE


def test_missing_nameservers_never_verifies() -> None:
    decision = decide(
        observation(status=STATUS_NO_NAMESERVERS, values=(), nameservers=()),
        expected_token=TOKEN,
        ns_snapshot=(),
        require_snapshot_match=False,
    )
    assert not decision.ok
    assert decision.reason == REASON_NO_NAMESERVERS


def test_malformed_response_is_not_treated_as_a_match() -> None:
    decision = decide(
        observation(status=STATUS_MALFORMED, values=()),
        expected_token=TOKEN,
        ns_snapshot=(),
        require_snapshot_match=False,
    )
    assert not decision.ok
    assert decision.reason == REASON_TXT_MISSING


def test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() -> None:
    decision = decide(
        observation(nameservers=("ns3.attacker.test",)),
        expected_token=TOKEN,
        ns_snapshot=NS,
        require_snapshot_match=True,
    )
    assert not decision.ok
    assert decision.reason == REASON_NS_CHANGED
    assert decision.ns_changed


def test_a_user_reverification_accepts_a_new_delegation() -> None:
    # A legitimate re-delegation must be re-provable; the sweep's stricter rule
    # exists to catch a name that changed hands *without* the owner asking.
    decision = decide(
        observation(nameservers=("ns9.newhost.test",)),
        expected_token=TOKEN,
        ns_snapshot=NS,
        require_snapshot_match=False,
    )
    assert decision.ok
    assert decision.ns_snapshot == ("ns9.newhost.test",)
    assert decision.ns_changed


def test_nameserver_comparison_is_order_and_case_insensitive() -> None:
    decision = decide(
        observation(nameservers=("NS2.Example.NET", "ns1.example.net.")),
        expected_token=TOKEN,
        ns_snapshot=NS,
        require_snapshot_match=True,
    )
    assert decision.ok
    assert not decision.ns_changed


def test_multiple_txt_values_are_all_considered() -> None:
    decision = decide(
        observation(values=("unrelated=1", TOKEN)),
        expected_token=TOKEN,
        ns_snapshot=(),
        require_snapshot_match=False,
    )
    assert decision.ok


def test_token_comparison_requires_an_exact_match() -> None:
    assert matches_token((TOKEN,), TOKEN)
    assert matches_token((f" {TOKEN} ",), TOKEN)  # values are stripped
    assert not matches_token((TOKEN + "x",), TOKEN)
    assert not matches_token((TOKEN[:-1],), TOKEN)
    assert not matches_token((), TOKEN)
    assert not matches_token(("",), "")  # an empty expected token never matches
    assert not matches_token(("some-other",), TOKEN)
