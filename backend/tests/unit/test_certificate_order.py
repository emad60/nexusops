"""Unit tests for the ACME order document — the crash-recovery contract.

The document is the only thing that survives between worker invocations, so the
properties pinned here are the ones a resume depends on: reads never raise, writes
are bounded and idempotent, cleanup bookkeeping is never lost, and the operator view
is an allowlist rather than a filtered copy.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from app.services import certificate_order as order
from app.services.acme import AcmeChallenge

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def _challenge(
    name: str = "example.com",
    *,
    wildcard: bool = False,
    url: str | None = None,
    value: str = "txt-value",
) -> AcmeChallenge:
    challenge_url = url or f"https://ca.test/chall/{name}/{value}"
    return AcmeChallenge(
        identifier=name,
        wildcard=wildcard,
        authorization_url=f"https://ca.test/authz/{name}",
        challenge_url=challenge_url,
        token="token",
        record_name=f"_acme-challenge.{name}",
        record_value=value,
        key_authorization=f"token.thumbprint.{value}",
        status="pending",
    )


def _generation(**state: Any) -> SimpleNamespace:
    return SimpleNamespace(order_state=state or None)


# --- reading -------------------------------------------------------------------


def test_load_treats_missing_and_malformed_state_as_not_ordered() -> None:
    assert order.load(_generation()) == {"version": order.DOCUMENT_VERSION}
    assert order.load(SimpleNamespace(order_state=["not", "a", "dict"])) == {
        "version": order.DOCUMENT_VERSION
    }
    assert order.entries(order.load(SimpleNamespace(order_state=None))) == []


def test_load_copies_and_drops_unshaped_entries() -> None:
    state = {"challenges": [{"challenge_url": "u"}, "junk", 3]}
    generation = SimpleNamespace(order_state=state)
    loaded = order.load(generation)
    assert len(loaded["challenges"]) == 1
    # A copy: the caller mutating its view must not write the ORM attribute.
    loaded["challenges"].append({"challenge_url": "other"})
    assert len(generation.order_state["challenges"]) == 3


def test_version_falls_back_when_unreadable() -> None:
    assert order.version({"version": 99}) == 99
    assert order.version({"version": "1"}) == order.DOCUMENT_VERSION
    assert order.version({}) == order.DOCUMENT_VERSION


# --- writing -------------------------------------------------------------------


def test_set_order_stamps_the_new_order() -> None:
    document = order.set_order(
        order.load(_generation()),
        directory_url="https://ca.test/dir",
        order_url="https://ca.test/order/1",
        mode="manual",
        expires_at=NOW,
        txt_ttl=60,
    )
    assert document["version"] == order.DOCUMENT_VERSION
    assert document["mode"] == order.MODE_MANUAL
    assert document["txt_ttl"] == 60
    assert document["order_expires_at"] == NOW.isoformat()
    assert document["started_at"]


def test_set_order_normalizes_an_unknown_mode_to_automated() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="something-else")
    assert document["mode"] == order.MODE_AUTOMATED


def test_store_copies_and_bounds_the_recorded_challenges() -> None:
    generation = _generation()
    challenges = tuple(
        _challenge(url=f"https://ca.test/chall/{index}")
        for index in range(order.MAX_RECORDED_CHALLENGES + 5)
    )
    document = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    order.record_challenges(document, challenges, mode="automated", order_url="o")

    stored = order.store(generation, document)
    assert stored["version"] == order.DOCUMENT_VERSION
    assert len(stored["challenges"]) == order.MAX_RECORDED_CHALLENGES
    assert generation.order_state is stored
    # What landed in the column is exactly what entries() reads back.
    assert len(order.entries(stored)) == order.MAX_RECORDED_CHALLENGES


def test_record_challenges_is_idempotent_per_challenge_url() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    challenge = _challenge()
    order.record_challenges(document, (challenge,), mode="automated", order_url="o")
    entry = order.entries(document)[0]
    order.update_challenge(
        document,
        entry["ref"],
        record_id="record-1",
        zone_id="zone-1",
        provider_id="provider-1",
        cleanup=order.CLEANUP_PENDING,
        published_at=NOW.isoformat(),
    )

    # Re-reading the same order after a crash: the reference and cleanup state
    # of an already-published challenge must survive.
    order.record_challenges(document, (challenge,), mode="automated", order_url="o")
    assert len(order.entries(document)) == 1
    entry = order.entries(document)[0]
    assert entry["record_id"] == "record-1"
    assert entry["published_at"] == NOW.isoformat()


def test_record_challenges_marks_manual_challenges_as_owing_no_cleanup() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="manual")
    order.record_challenges(document, (_challenge(),), mode="manual", order_url="o")
    entry = order.entries(document)[0]
    assert entry["mode"] == order.MODE_MANUAL
    assert entry["cleanup"] == order.CLEANUP_NOT_REQUIRED
    assert order.pending_cleanup(document) == []


def test_reset_challenges_keeps_only_unconfirmed_records() -> None:
    document = order.set_order({}, directory_url="d", order_url="old", mode="automated")
    order.record_challenges(
        document,
        (_challenge(url="https://ca.test/chall/a"), _challenge(url="https://ca.test/chall/b")),
        mode="automated",
        order_url="old",
    )
    first, second = order.entries(document)

    order.update_challenge(document, first["ref"], record_id="record-a")
    order.update_challenge(document, first["ref"], cleanup=order.CLEANUP_DONE)
    order.update_challenge(document, second["ref"], record_id="record-b")
    order.update_challenge(document, second["ref"], cleanup=order.CLEANUP_UNRESOLVED)

    survivors = order.entries(order.reset_challenges(document))
    assert [entry["ref"] for entry in survivors] == [second["ref"]]


def test_update_challenge_cannot_add_untyped_fields() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    order.record_challenges(document, (_challenge(),), mode="automated", order_url="o")
    ref = order.entries(document)[0]["ref"]

    entry = order.update_challenge(document, ref, private_key="SECRET", record_id="r1")
    assert entry is not None
    assert "private_key" not in entry
    assert entry["record_id"] == "r1"

    assert order.update_challenge(document, "missing-ref", record_id="x") is None


def test_update_challenge_validates_cleanup_and_coerces_counters() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    order.record_challenges(document, (_challenge(),), mode="automated", order_url="o")
    ref = order.entries(document)[0]["ref"]

    entry = order.update_challenge(document, ref, cleanup="finished", cleanup_attempts="3")
    assert entry is not None
    assert entry["cleanup"] == order.CLEANUP_PENDING
    assert entry["cleanup_attempts"] == 3

    entry = order.update_challenge(document, ref, cleanup=order.CLEANUP_DONE)
    assert entry is not None
    assert entry["cleanup"] == order.CLEANUP_DONE


def test_update_challenge_bounds_free_text() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    order.record_challenges(document, (_challenge(),), mode="automated", order_url="o")
    ref = order.entries(document)[0]["ref"]

    entry = order.update_challenge(document, ref, error="e" * (order.MAX_TEXT * 2))
    assert entry is not None
    assert len(entry["error"]) == order.MAX_TEXT


# --- projections ---------------------------------------------------------------


def test_current_entries_excludes_replaced_orders() -> None:
    document = order.set_order({}, directory_url="d", order_url="old", mode="automated")
    order.record_challenges(
        document, (_challenge(url="https://ca.test/chall/old"),), mode="automated", order_url="old"
    )
    order.set_order(document, directory_url="d", order_url="new", mode="automated")
    order.record_challenges(
        document, (_challenge(url="https://ca.test/chall/new"),), mode="automated", order_url="new"
    )

    assert [entry["order_url"] for entry in order.current_entries(document)] == ["new"]

    document.pop("order_url")
    assert order.current_entries(document) == []


def test_pending_publication_ignores_published_and_other_orders() -> None:
    document = order.set_order({}, directory_url="d", order_url="current", mode="automated")
    order.record_challenges(
        document,
        (
            _challenge(url="https://ca.test/chall/one"),
            _challenge(url="https://ca.test/chall/two"),
        ),
        mode="automated",
        order_url="current",
    )
    published, _ = order.entries(document)
    order.update_challenge(document, published["ref"], published_at=NOW.isoformat())

    pending = order.pending_publication(document)
    assert [entry["ref"] for entry in pending] == [order.entries(document)[1]["ref"]]


def test_pending_cleanup_includes_unresolved_but_requires_a_record() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    order.record_challenges(
        document,
        (
            _challenge(url="https://ca.test/chall/one"),
            _challenge(url="https://ca.test/chall/two"),
        ),
        mode="automated",
        order_url="o",
    )
    first, second = order.entries(document)
    # No record was ever created at this provider, so nothing is owed.
    assert order.pending_cleanup(document) == []

    order.update_challenge(document, first["ref"], record_id="r1")
    order.update_challenge(document, first["ref"], cleanup=order.CLEANUP_UNRESOLVED)
    order.update_challenge(document, second["ref"], record_id="r2")
    order.update_challenge(document, second["ref"], cleanup=order.CLEANUP_DONE)

    assert [entry["ref"] for entry in order.pending_cleanup(document)] == [first["ref"]]
    assert [entry["ref"] for entry in order.cleanup_incomplete(document)] == [first["ref"]]


def test_manual_instructions_are_public_only() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="manual")
    order.record_challenges(document, (_challenge(wildcard=True),), mode="manual", order_url="o")

    instructions = order.manual_instructions(document)
    assert len(instructions) == 1
    assert set(instructions[0]) == {
        "ref",
        "identifier",
        "wildcard",
        "record_name",
        "record_value",
        "confirmed",
        "validated",
    }
    assert instructions[0]["wildcard"] is True
    assert instructions[0]["confirmed"] is False


def test_public_view_is_an_allowlist() -> None:
    document = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    order.record_challenges(document, (_challenge(),), mode="automated", order_url="o")
    ref = order.entries(document)[0]["ref"]
    order.update_challenge(
        document, ref, record_id="r1", zone_id="z1", provider_id="p1", cleanup_error="boom"
    )

    view = order.public_view(document)
    assert set(view) == {
        "version",
        "mode",
        "order_url",
        "order_expires_at",
        "started_at",
        "finalized_at",
        "challenges",
    }
    assert set(view["challenges"][0]) == {
        "ref",
        "identifier",
        "wildcard",
        "record_name",
        "record_value",
        "mode",
        "published",
        "confirmed_at",
        "validated_at",
        "cleanup",
        "error",
    }
    serialized = repr(view)
    assert "record_id" not in serialized
    assert "zone_id" not in serialized
    assert "provider_id" not in serialized
    assert "key_authorization" not in serialized


def test_public_view_defaults_unknown_cleanup_to_pending() -> None:
    document = {"challenges": [{"challenge_url": "u", "cleanup": ""}]}
    view = order.public_view(document)
    assert view["challenges"][0]["cleanup"] == order.CLEANUP_PENDING


# --- attempt bookkeeping -------------------------------------------------------


def test_attempt_in_flight_requires_a_start_and_no_finish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The module stamps the real clock, so it is pinned here: comparing a real
    # "now" against the fixed NOW below would make this test pass or fail by the
    # hour it runs at rather than by the predicate it checks.
    monkeypatch.setattr(order, "_utcnow", lambda: NOW)
    document: dict[str, Any] = {}
    assert order.attempt_in_flight(document) is False

    order.begin_attempt(document)
    assert order.attempt_in_flight(document) is True
    assert (
        order.attempt_in_flight(document, now=NOW + timedelta(minutes=5), ttl_seconds=60) is False
    )

    order.finish_attempt(document)
    assert order.attempt_in_flight(document) is False


def test_started_at_falls_back_to_the_row_timestamp() -> None:
    fallback = NOW - timedelta(hours=1)
    assert order.started_at({}, fallback=fallback) == fallback
    assert order.started_at({"started_at": "not-a-time"}, fallback=fallback) == fallback

    stamped = order.set_order({}, directory_url="d", order_url="o", mode="automated")
    parsed = order.started_at(stamped, fallback=fallback)
    assert parsed != fallback
    assert parsed.tzinfo is not None


def test_challenge_ref_is_stable_and_opaque() -> None:
    ref = order.challenge_ref("https://ca.test/chall/1")
    assert ref == order.challenge_ref("https://ca.test/chall/1")
    assert len(ref) == order.REF_LENGTH
    assert "ca.test" not in ref
    assert ref != order.challenge_ref("https://ca.test/chall/2")


@pytest.mark.parametrize("entry", [{"challenge_url": ""}, {"challenge_url": 5}, {}])
def test_entries_skips_entries_without_a_challenge_url(entry: dict[str, Any]) -> None:
    assert order.entries({"challenges": [entry]}) == []
