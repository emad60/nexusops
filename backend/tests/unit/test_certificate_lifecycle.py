"""The pre-issuance lifecycle is a contract, and Phase 5.1's bound is its shape.

Three things are asserted here rather than trusted:

1. **The transition table is closed and acyclic-forward.** Every pre-issuance
   state has exactly the moves the design gives it, ``FAILED`` is the only state
   that can go backwards (into a retry), and nothing else can skip a step.
2. **An issued generation is unrepresentable.** ``ISSUED`` is not an enum member,
   not a legal target, and not an input any function here accepts — so no code
   path in this phase can report a certificate as issued or delivered.
3. **The derivation and the schema agree.** The certificate status is derived
   from the generation, the partial unique index that allows one in-flight
   generation is built from the same state tuple, and the read models expose only
   approved metadata fields.

The last one is why this module also reads the ORM metadata: the state machine,
the index predicate and the CHECK constraint are three expressions of one
vocabulary, and a change to any of them alone is the bug this file exists to
catch.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.core.permissions import ALL_CODENAMES, PERMISSIONS, ROLE_MATRIX, WILDCARD
from app.models.certificate import CertificateGeneration, one_live_generation_predicate
from app.models.enums import CertificateGenerationState as State
from app.models.enums import CertificateStatus
from app.schemas.certificate import (
    CertificateCreate,
    CertificateGenerationOut,
    CertificateOut,
)
from app.services import certificate_lifecycle as lifecycle

REPO_DIR = Path(__file__).resolve().parents[3]

#: Every field the generation read model is allowed to expose.
GENERATION_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "certificate_id",
    "generation",
    "state",
    "attempt_count",
    "next_attempt_at",
    "last_error",
    "retryable",
    "terminal",
    "status_detail",
}

#: Every field the certificate read model is allowed to expose.
CERTIFICATE_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "domain_id",
    "domain_name",
    "domain_status",
    "primary_cn",
    "sans",
    "status",
    "challenge_type",
    "key_algorithm",
    "auto_renew",
    "expires_at",
    "last_error",
    "current_generation_id",
    "latest_generation",
    "issued",
    "status_detail",
}

#: Substrings that must never name a field on a response model. A key, a wrapped
#: key, a chain, a DEK generation or an ordering cursor is not metadata.
FORBIDDEN_FIELD_FRAGMENTS = (
    "cipher",
    "private",
    "material",
    "deke",
    "secret",
    "order_state",
    "pem",
    "chain",
    "token",
)


# --- 1. the transition table ---------------------------------------------------


def test_every_state_has_a_transition_row() -> None:
    assert set(lifecycle.TRANSITIONS) == set(State)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (State.PENDING, State.ORDERING),
        (State.PENDING, State.FAILED),
        (State.ORDERING, State.CHALLENGE_PUBLISHED),
        (State.ORDERING, State.FAILED),
        (State.CHALLENGE_PUBLISHED, State.VALIDATING),
        (State.CHALLENGE_PUBLISHED, State.FAILED),
        (State.VALIDATING, State.FAILED),
        (State.FAILED, State.ORDERING),
    ],
)
def test_the_legal_moves_are_the_designs(current: State, target: State) -> None:
    assert lifecycle.can_transition(current, target) is True
    assert lifecycle.require_transition(current, target) is target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        # Backwards, except the one sanctioned retry.
        (State.ORDERING, State.PENDING),
        (State.CHALLENGE_PUBLISHED, State.ORDERING),
        (State.VALIDATING, State.CHALLENGE_PUBLISHED),
        # Skipping the challenge that was never published.
        (State.PENDING, State.CHALLENGE_PUBLISHED),
        (State.PENDING, State.VALIDATING),
        (State.ORDERING, State.VALIDATING),
        # A state cannot move to itself.
        (State.PENDING, State.PENDING),
        (State.FAILED, State.FAILED),
    ],
)
def test_every_other_move_is_refused(current: State, target: State) -> None:
    assert lifecycle.can_transition(current, target) is False
    with pytest.raises(lifecycle.InvalidTransition) as exc:
        lifecycle.require_transition(current, target)
    assert exc.value.current == current
    assert exc.value.target == target


def test_unknown_values_are_not_states() -> None:
    assert lifecycle.coerce_state("ISSUED") is None
    assert lifecycle.coerce_state("") is None
    assert lifecycle.coerce_state(None) is None
    assert lifecycle.can_transition("PENDING", "ISSUED") is False
    assert lifecycle.can_transition("nonsense", "ORDERING") is False


# --- 2. an issued generation does not exist in this phase ----------------------


def test_issued_is_not_a_generation_state() -> None:
    values = {str(member) for member in State}
    assert "ISSUED" not in values
    # ... and the material-bearing vocabulary in its entirety is absent, not just
    # the one state: none of these may be written or transitioned into yet.
    for absent in (
        "ISSUED",
        "SUPERSEDED",
        "SUSPENDED",
        "EXPIRED",
        "REVOCATION_PENDING",
        "REVOKED",
        "REVOCATION_FAILED",
        "REVOKED_LOCAL_ONLY",
    ):
        assert absent not in values
        assert lifecycle.coerce_state(absent) is None
        assert lifecycle.can_transition(State.VALIDATING, absent) is False
        with pytest.raises(lifecycle.InvalidTransition):
            lifecycle.require_transition(State.VALIDATING, absent)


def test_handing_a_material_state_to_the_lifecycle_is_refused_loudly() -> None:
    """A newer row read by this phase's code fails rather than being mislabelled."""
    with pytest.raises(lifecycle.UnrepresentableState):
        lifecycle.assert_pre_issuance("ISSUED")
    with pytest.raises(lifecycle.UnrepresentableState):
        lifecycle.assert_pre_issuance(None)
    with pytest.raises(lifecycle.UnrepresentableState):
        lifecycle.certificate_status_for("SUPERSEDED")


def test_the_initial_state_is_the_one_a_request_starts_in() -> None:
    assert lifecycle.INITIAL_STATE is State.PENDING
    assert lifecycle.assert_pre_issuance(lifecycle.INITIAL_STATE) is State.PENDING


# --- 3. derived status and retry policy ---------------------------------------


def test_no_pre_issuance_state_ever_derives_an_issued_status() -> None:
    derived = {lifecycle.certificate_status_for(state) for state in State}
    assert derived == {CertificateStatus.PENDING, CertificateStatus.FAILED}
    assert CertificateStatus.ISSUED not in derived
    # The in-flight states all read as one thing to a client: requested.
    for in_flight in State.live_pre_issuance():
        assert lifecycle.certificate_status_for(in_flight) is CertificateStatus.PENDING
    assert lifecycle.certificate_status_for(State.FAILED) is CertificateStatus.FAILED


def test_a_failure_is_retryable_until_the_budget_is_spent() -> None:
    assert lifecycle.MAX_ISSUE_ATTEMPTS > 1
    for spent in range(lifecycle.MAX_ISSUE_ATTEMPTS):
        assert lifecycle.is_retryable(State.FAILED, spent) is True
        assert lifecycle.is_terminal(State.FAILED, spent) is False
    assert lifecycle.is_retryable(State.FAILED, lifecycle.MAX_ISSUE_ATTEMPTS) is False
    assert lifecycle.is_terminal(State.FAILED, lifecycle.MAX_ISSUE_ATTEMPTS) is True
    # Only FAILED is retryable: a state that is still in flight is not a failure.
    for state in State.live_pre_issuance():
        assert lifecycle.is_retryable(state, 0) is False
        assert lifecycle.is_terminal(state, 0) is False


def test_backoff_grows_and_is_capped() -> None:
    first = lifecycle.attempt_delay_seconds(1)
    values = [lifecycle.attempt_delay_seconds(attempt) for attempt in range(1, 12)]
    assert values[0] == first > 0
    assert values == sorted(values)
    assert values[-1] <= 24 * 60 * 60
    assert lifecycle.attempt_delay_seconds(99) == 24 * 60 * 60

    now = datetime(2026, 10, 12, 12, 0, tzinfo=UTC)
    assert lifecycle.next_attempt_at(1, now=now) == now + timedelta(seconds=first)
    assert lifecycle.next_attempt_at(2, now=now) > lifecycle.next_attempt_at(1, now=now)
    # A generation that has not been attempted yet is still due after one delay,
    # not immediately: the cursor is a backoff, never a busy loop.
    assert lifecycle.next_attempt_at(0, now=now) == now + timedelta(seconds=first)


def test_every_status_detail_says_nothing_has_been_issued() -> None:
    for state in State:
        for attempt in (0, 1, lifecycle.MAX_ISSUE_ATTEMPTS):
            detail = lifecycle.status_detail_for(state, attempt)
            assert detail.strip()
            assert "issued" in detail.lower(), detail


# --- 4. the derivation, the index and the schema agree -------------------------


def test_the_one_live_generation_index_covers_exactly_the_live_states() -> None:
    predicate = one_live_generation_predicate()
    for state in State.live_pre_issuance():
        assert f"'{state.value}'" in predicate
    # FAILED is deliberately outside it: a retry needs a row of its own.
    assert "'FAILED'" not in predicate

    index = next(
        index
        for index in CertificateGeneration.__table__.indexes
        if index.name == "uq_cert_generations_one_live"
    )
    assert index.unique is True
    assert [column.name for column in index.columns] == ["certificate_id"]
    assert str(index.dialect_options["postgresql"]["where"]) == predicate


def test_the_generation_state_check_matches_the_enum() -> None:
    checks = {
        str(constraint.name): str(constraint.sqltext)
        for constraint in CertificateGeneration.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    state_check = next(text for name, text in checks.items() if name.endswith("_state_valid"))
    for state in State:
        assert f"'{state.value}'" in state_check
    assert "'ISSUED'" not in state_check


def test_the_generation_number_and_attempt_columns_are_bounded_by_the_database() -> None:
    checks = " ".join(
        str(constraint.sqltext)
        for constraint in CertificateGeneration.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    )
    assert "generation >= 1" in checks
    assert "attempt_count >= 0" in checks


# --- 5. the read models expose approved metadata only --------------------------


def test_the_response_models_expose_exactly_the_approved_fields() -> None:
    assert set(CertificateOut.model_fields) == CERTIFICATE_FIELDS
    assert set(CertificateGenerationOut.model_fields) == GENERATION_FIELDS


@pytest.mark.parametrize("fragment", FORBIDDEN_FIELD_FRAGMENTS)
def test_no_response_field_can_hold_key_material(fragment: str) -> None:
    fields = set(CertificateOut.model_fields) | set(CertificateGenerationOut.model_fields)
    offending = sorted(name for name in fields if fragment in name)
    assert offending == [], f"read models must not expose {fragment!r}: {offending}"


def test_the_request_body_rejects_fields_this_phase_does_not_have() -> None:
    """No forward reference: ``dns_provider_id`` arrives with its table in 5.2."""
    with pytest.raises(ValueError):
        CertificateCreate(
            domain_id="11111111-1111-1111-1111-111111111111",
            identifiers=["example.com"],
            dns_provider_id="22222222-2222-2222-2222-222222222222",
        )
    with pytest.raises(ValueError):
        CertificateCreate(
            domain_id="11111111-1111-1111-1111-111111111111",
            identifiers=[],
        )


# --- 6. the certificate role matrix is the committed one -----------------------


def _documented_matrix() -> dict[str, tuple[bool, bool]]:
    """The certificate rows of the design's §4.1 role table, from the document.

    The design's table is the committed decision (O3); this parses it so the
    registry and the document cannot drift apart silently.
    """
    design = (REPO_DIR / "docs" / "phase5-design.md").read_text(encoding="utf-8")
    lines = design.splitlines()
    header = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("|")
        and "Stored role" in line
        and "certificate.read" in line
        and "certificate.manage" in line
    )
    documented: dict[str, tuple[bool, bool]] = {}
    for line in lines[header + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            break
        role = cells[0].replace("*", "").split()[0]
        documented[role] = ("✓" in cells[1], "✓" in cells[2])
    return documented


def test_the_registry_and_the_committed_role_matrix_agree() -> None:
    documented = _documented_matrix()
    # Guard the parser itself: a miss must fail loudly rather than pass vacuously.
    assert set(documented) == {"Owner", "Admin", "Operator", "Developer", "Viewer"}

    assert ALL_CODENAMES >= {"certificate.read", "certificate.manage"}
    for role, (reads, manages) in documented.items():
        grants = ROLE_MATRIX[role]
        if WILDCARD in grants:
            assert reads and manages, "the wildcard role holds both by definition"
            continue
        assert ("certificate.read" in grants) is reads, role
        assert ("certificate.manage" in grants) is manages, role

    # The stored role name is `Operator`; the design's table says so explicitly,
    # so no `DevOps` row may appear in the registry before the rename ships.
    assert "DevOps" not in ROLE_MATRIX


def test_certificate_read_does_not_carry_management_authority() -> None:
    """Read-only roles hold the read codename and nothing else certificate-side."""
    for role in ("Developer", "Viewer"):
        grants = set(ROLE_MATRIX[role])
        assert "certificate.read" in grants
        assert "certificate.manage" not in grants
    for role in ("Admin", "Operator"):
        assert {"certificate.read", "certificate.manage"} <= set(ROLE_MATRIX[role])


def test_the_registry_adds_exactly_the_two_certificate_codenames() -> None:
    specs = {spec.codename for spec in PERMISSIONS if spec.codename.startswith("certificate.")}
    assert specs == {"certificate.read", "certificate.manage"}
    # No management-by-execute grant hides behind the new group.
    assert not any(codename.endswith(".execute") for codename in ALL_CODENAMES)
