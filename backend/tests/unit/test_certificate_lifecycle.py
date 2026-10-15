"""The generation lifecycle is a contract, and its material gating is its shape.

Four things are asserted here rather than trusted:

1. **The transition table is closed and acyclic-forward.** Every state in the
   (now complete) vocabulary has exactly the moves the design gives it,
   ``FAILED`` is the only state that can go backwards (into a retry), only
   ``VALIDATING`` may enter ``ISSUED``, and the revocation states are terminal.
2. **A material-bearing state cannot be reached or written without material.**
   Phase 5.1 bought that property by truncating the vocabulary — ``ISSUED`` was
   not an enum member at all. Phase 5.2.2 widens the vocabulary to the full
   machine, so the property is now carried by the **material guard**: the enum's
   ``material_bearing()`` decides which states must carry ``key_ciphertext``,
   ``chain_ciphertext``, ``deke_id``, ``issued_at``, ``not_before`` and
   ``not_after``, and the model's CHECK is derived from that same tuple. This
   file asserts the two halves cannot disagree, which is what keeps the widening
   from reopening the window 5.1 closed.
3. **The derivation and the schema agree.** The certificate status is derived
   from the generation, the partial unique index that allows one in-flight
   generation is built from the same state tuple, and the read models expose only
   approved metadata fields — the material columns exist now, and none of them may
   appear in a response model.

The last one is why this module also reads the ORM metadata: the state machine,
the index predicate and the CHECK constraints are expressions of one vocabulary,
and a change to any of them alone is the bug this file exists to catch.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.core.permissions import ALL_CODENAMES, PERMISSIONS, ROLE_MATRIX, WILDCARD
from app.models.certificate import (
    Certificate,
    CertificateGeneration,
    material_guard_predicate,
    one_live_generation_predicate,
)
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
    # Phase 5.2.2 metadata *about* the material, never the material itself.
    "not_before",
    "not_after",
    "issued_at",
    "fingerprint",
    "revocation_state",
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
    "dns_provider_id",
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
        # Post-issuance (5.2.2): the material is stored, and these are the only
        # ways a material-bearing generation moves.
        (State.VALIDATING, State.ISSUED),
        (State.ISSUED, State.SUPERSEDED),
        (State.ISSUED, State.SUSPENDED),
        (State.ISSUED, State.EXPIRED),
        (State.ISSUED, State.REVOCATION_PENDING),
        (State.SUPERSEDED, State.SUSPENDED),
        # A manual revoke is not blocked by a newer generation (§9.5).
        (State.SUPERSEDED, State.REVOCATION_PENDING),
        (State.SUSPENDED, State.REVOCATION_PENDING),
        # ``notAfter`` passing does not make a key unrevokable.
        (State.EXPIRED, State.REVOCATION_PENDING),
        (State.REVOCATION_PENDING, State.REVOKED),
        (State.REVOCATION_PENDING, State.REVOCATION_FAILED),
        (State.REVOCATION_FAILED, State.REVOCATION_PENDING),
        (State.REVOCATION_FAILED, State.REVOKED_LOCAL_ONLY),
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
        # Material cannot be minted by skipping the challenge.
        (State.PENDING, State.ISSUED),
        (State.ORDERING, State.ISSUED),
        (State.CHALLENGE_PUBLISHED, State.ISSUED),
        # A material-bearing generation cannot walk backwards into ordering.
        (State.ISSUED, State.VALIDATING),
        (State.SUPERSEDED, State.ISSUED),
        (State.EXPIRED, State.ISSUED),
        # A revocation is not "issued" again, and only the CA conversation can
        # end a pending revocation.
        (State.ISSUED, State.REVOKED),
        (State.REVOCATION_PENDING, State.ISSUED),
        # Terminal means terminal.
        (State.REVOKED, State.REVOCATION_PENDING),
        (State.REVOKED_LOCAL_ONLY, State.REVOCATION_PENDING),
    ],
)
def test_every_other_move_is_refused(current: State, target: State) -> None:
    assert lifecycle.can_transition(current, target) is False
    with pytest.raises(lifecycle.InvalidTransition) as exc:
        lifecycle.require_transition(current, target)
    assert exc.value.current == current
    assert exc.value.target == target


def test_unknown_values_are_not_states() -> None:
    assert lifecycle.coerce_state("ISSUED_ELSEWHERE") is None
    assert lifecycle.coerce_state("") is None
    assert lifecycle.coerce_state(None) is None
    assert lifecycle.coerce_state(State.PENDING) is State.PENDING
    # A state that exists is not automatically a legal target.
    assert lifecycle.can_transition("PENDING", "ISSUED") is False
    assert lifecycle.can_transition("nonsense", "ORDERING") is False


def test_handing_an_unknown_value_to_the_lifecycle_is_refused_loudly() -> None:
    """A value that names no state fails rather than being mislabelled."""
    with pytest.raises(lifecycle.UnrepresentableState):
        lifecycle.assert_state(None)
    with pytest.raises(lifecycle.UnrepresentableState):
        lifecycle.certificate_status_for("SUPERSEDED_ELSEWHERE")
    with pytest.raises(lifecycle.UnrepresentableState):
        lifecycle.material_required("nonsense")


# --- 2. a material-bearing state cannot exist without material -----------------


def test_every_state_is_exactly_one_of_pre_issuance_or_material_bearing() -> None:
    """The two predicates partition the vocabulary — the guard's whole premise."""
    pre_issuance = set(State.live_pre_issuance()) | {State.FAILED}
    material_bearing = set(State.material_bearing())
    assert pre_issuance & material_bearing == set()
    assert pre_issuance | material_bearing == set(State)
    # ``FAILED`` is material-less by construction but is *not* live: a retry needs
    # a row of its own, so ``live_pre_issuance`` must not have grown to include it.
    assert State.FAILED not in State.live_pre_issuance()


def test_the_material_predicate_follows_the_enum() -> None:
    for state in State:
        assert lifecycle.material_required(state) is (state in State.material_bearing())


def test_the_two_narrowings_refuse_each_others_vocabulary() -> None:
    """A fresh generation cannot already carry material, and material cannot be
    written into a state the guard CHECK does not require it for."""
    for state in State.material_bearing():
        assert lifecycle.assert_material_bearing(state) is state
        with pytest.raises(lifecycle.UnrepresentableState):
            lifecycle.assert_pre_issuance(state)
    for state in (*State.live_pre_issuance(), State.FAILED):
        assert lifecycle.assert_pre_issuance(state) is state
        with pytest.raises(lifecycle.UnrepresentableState):
            lifecycle.assert_material_bearing(state)


def test_every_material_bearing_state_has_a_way_in_and_only_validating_issues() -> None:
    """No material-bearing state is unreachable, and none is entered by skipping
    the challenge except through ``VALIDATING``."""
    for target in State.material_bearing():
        sources = {state for state in State if lifecycle.can_transition(state, target)}
        assert sources, f"{target} is unreachable"
        if target is State.ISSUED:
            assert sources == {State.VALIDATING}
        else:
            assert State.VALIDATING not in sources, target


def test_the_initial_state_is_the_one_a_request_starts_in() -> None:
    assert lifecycle.INITIAL_STATE is State.PENDING
    assert lifecycle.assert_pre_issuance(lifecycle.INITIAL_STATE) is State.PENDING


# --- 3. derived status and retry policy ---------------------------------------


def test_the_status_derivation_is_the_documented_one() -> None:
    """Every generation state maps to exactly one certificate status.

    Two collapses are deliberate and asserted here, because a silent third one
    would be the bug this test exists to catch: ``SUPERSEDED`` reads as
    ``ISSUED`` (the material exists and may still be serving) and
    ``REVOCATION_FAILED`` reads as ``REVOCATION_PENDING`` (the CA conversation is
    unfinished, which is what that status says).
    """
    derived = {lifecycle.certificate_status_for(state) for state in State}
    assert derived == set(CertificateStatus)
    # Nothing has been issued while the order is still in flight — and a request
    # that has not produced material must never read as if it had.
    for in_flight in State.live_pre_issuance():
        assert lifecycle.certificate_status_for(in_flight) is CertificateStatus.PENDING
    assert lifecycle.certificate_status_for(State.FAILED) is CertificateStatus.FAILED
    assert lifecycle.certificate_status_for(State.ISSUED) is CertificateStatus.ISSUED
    assert lifecycle.certificate_status_for(State.SUPERSEDED) is CertificateStatus.ISSUED
    assert lifecycle.certificate_status_for(State.SUSPENDED) is CertificateStatus.SUSPENDED
    assert lifecycle.certificate_status_for(State.EXPIRED) is CertificateStatus.EXPIRED
    assert (
        lifecycle.certificate_status_for(State.REVOCATION_FAILED)
        is CertificateStatus.REVOCATION_PENDING
    )
    assert lifecycle.certificate_status_for(State.REVOKED) is CertificateStatus.REVOKED
    assert (
        lifecycle.certificate_status_for(State.REVOKED_LOCAL_ONLY)
        is CertificateStatus.REVOKED_LOCAL_ONLY
    )


def test_only_the_revocation_states_are_terminal() -> None:
    assert lifecycle.is_terminal(State.REVOKED, 0) is True
    assert lifecycle.is_terminal(State.REVOKED_LOCAL_ONLY, 0) is True
    # A superseded or expired generation is still revocable, and a suspension is
    # a step on the way there — none of them is the end of the machine.
    for state in State.material_bearing():
        if state in {State.REVOKED, State.REVOKED_LOCAL_ONLY}:
            continue
        assert lifecycle.is_terminal(state, 0) is False, state
        assert lifecycle.is_retryable(state, 0) is False, state


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


def test_every_status_detail_is_non_empty_and_says_what_it_should() -> None:
    """A request that has not been issued must not read as if it had, and a
    generation that does hold material must say so rather than staying silent."""
    for state in (*State.live_pre_issuance(), State.FAILED):
        for attempt in (0, 1, lifecycle.MAX_ISSUE_ATTEMPTS):
            detail = lifecycle.status_detail_for(state, attempt)
            assert detail.strip()
            assert "issued" in detail.lower(), detail

    issued = lifecycle.status_detail_for(State.ISSUED).lower()
    assert "issued" in issued
    # The human description and the derived status agree in both directions: a
    # material-bearing state never claims nothing was issued.
    for state in State.material_bearing():
        detail = lifecycle.status_detail_for(state, 0)
        assert detail.strip(), state
        assert "nothing is issued" not in detail.lower(), detail
        assert "no certificate has been issued" not in detail.lower(), detail


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
    """The 5.1 CHECK is widened to the whole machine in the same change as the
    guard — the vocabulary and the constraint that makes it safe move together."""
    state_check = _generation_checks()["ck_certificate_generations_state_valid"]
    for state in State:
        assert f"'{state.value}'" in state_check


def test_the_material_guard_check_is_the_enums_predicate() -> None:
    """The guard is derived, not restated: it is the pre-issuance branch *or* the
    six material fields, and it must equal the function the model builds it from.

    A guard that lost a column or admitted a material-bearing state into its
    first branch would reintroduce exactly the material-less ``ISSUED`` row 5.1
    made unrepresentable.
    """
    guard = _generation_checks()["ck_certificate_generations_material_guard"]
    assert guard == material_guard_predicate()

    pre_issuance = set(State.live_pre_issuance()) | {State.FAILED}
    for state in sorted(pre_issuance, key=str):
        assert f"'{state.value}'" in guard, state
    for state in State.material_bearing():
        assert f"'{state.value}'" not in guard, (
            f"{state.value} is material-bearing and must not appear in the guard's "
            "no-material branch"
        )
    for column in (
        "key_ciphertext",
        "chain_ciphertext",
        "deke_id",
        "issued_at",
        "not_before",
        "not_after",
    ):
        assert column in guard, column


def test_the_certificate_suspension_pair_is_a_constraint() -> None:
    """Suspension is set and cleared as one fact (§9.3), at both levels."""
    for table in (Certificate.__table__, CertificateGeneration.__table__):
        names = {
            str(constraint.name): str(constraint.sqltext)
            for constraint in table.constraints
            if constraint.__class__.__name__ == "CheckConstraint"
        }
        pair = next(text for name, text in names.items() if name.endswith("_suspension_pair_valid"))
        assert "suspended_at IS NULL" in pair
        assert "suspension_reason = ''" in pair


def _generation_checks() -> dict[str, str]:
    return {
        str(constraint.name): str(constraint.sqltext)
        for constraint in CertificateGeneration.__table__.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }


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


def test_the_request_body_accepts_the_credential_override_and_nothing_else() -> None:
    """``dns_provider_id`` arrived with its table in 5.2.2; the body stays closed.

    The override is a reference the service resolves inside the caller's own
    organization, so it belongs on the request. Anything the request does not
    name — including every material column the slice added — is refused rather
    than ignored.
    """
    request = CertificateCreate(
        domain_id="11111111-1111-1111-1111-111111111111",
        identifiers=["example.com"],
        dns_provider_id="22222222-2222-2222-2222-222222222222",
    )
    assert request.dns_provider_id is not None
    # Omitted is a value too: inherit the Domain's credential.
    assert (
        CertificateCreate(
            domain_id="11111111-1111-1111-1111-111111111111",
            identifiers=["example.com"],
        ).dns_provider_id
        is None
    )

    with pytest.raises(ValueError):
        CertificateCreate(
            domain_id="11111111-1111-1111-1111-111111111111",
            identifiers=["example.com"],
            key_ciphertext="not-a-payload-field",
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
