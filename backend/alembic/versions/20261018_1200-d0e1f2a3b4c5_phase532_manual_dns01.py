"""Phase 5.3.2 — manual DNS-01: ``certificates.dns_mode`` and ``AWAITING_MANUAL``.

Two changes, and they are one change: a workflow in which the *customer* publishes
the challenge record cannot be represented by a column alone, because the attempt
that placed the order has to stop somewhere between "order placed" and "challenge
answered" and report that it is waiting for a human. Adding the state without the
mode would give the flow a place to wait that no certificate could legitimately
reach; adding the mode without the state would leave the manual order to be
re-ordered on every dispatch.

* ``certificates.dns_mode`` — ``automated`` (the platform publishes through the
  certificate's DNS credential) or ``manual`` (the customer publishes it). Explicit
  rather than inferred from a missing credential: "no credential attached" is also
  the state of a request whose credential was never chosen, and guessing ``manual``
  from that would move a certificate into a workflow nobody selected.
  ``ck_certificates_manual_mode_has_no_provider`` keeps the two halves coherent — a
  manual certificate never names an automated publisher.
* ``AWAITING_MANUAL`` — a **live pre-issuance** state, which is why three existing
  constraints are widened rather than left alone:
  - ``uq_cert_generations_one_live`` (partial unique index) — an awaiting generation
    is an in-flight generation; two of them for one certificate would be two open
    orders and two sets of instructions.
  - ``ck_certificate_generations_material_guard`` — an awaiting generation has no
    material, so it has to be in the guard's no-material branch.
  - ``ck_certificate_generations_state_valid`` — the vocabulary itself.

``ck_certificate_generations_directory_required`` needs no change: an awaiting
generation always has ``directory_url`` (it is written when the order is placed, in
the same transaction), so the wider predicate would accept exactly the same rows.

The downgrade refuses while any certificate is manual or any generation is awaiting
a manual confirmation. Dropping the column would silently convert those requests to
automated ones whose publisher was never chosen, and narrowing the state CHECK would
fail on the rows themselves — a stopped migration with the data intact is the honest
outcome, the same rule the 5.2.2 and 5.3 downgrades apply.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Created: 2026-10-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: str | None = "c9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: ``CertificateDnsMode``'s members (a CHECK cannot call Python; drift-tested
#: against the enum by ``test_migration_drift.py``).
DNS_MODES = ("automated", "manual")

#: Every generation state, literally: the enum's members in declaration order.
GENERATION_STATES = (
    "PENDING",
    "ORDERING",
    "AWAITING_MANUAL",
    "CHALLENGE_PUBLISHED",
    "VALIDATING",
    "FAILED",
    "ISSUED",
    "SUPERSEDED",
    "SUSPENDED",
    "EXPIRED",
    "REVOCATION_PENDING",
    "REVOKED",
    "REVOCATION_FAILED",
    "REVOKED_LOCAL_ONLY",
)

#: The live set — the partial index's predicate. ``AWAITING_MANUAL`` is included:
#: the generation holds an open order and is resumed, not replaced.
LIVE_STATES = ("PENDING", "ORDERING", "AWAITING_MANUAL", "CHALLENGE_PUBLISHED", "VALIDATING")

CK_CERTIFICATES_DNS_MODE = "ck_certificates_dns_mode_valid"
CK_CERTIFICATES_MANUAL_NO_PROVIDER = "ck_certificates_manual_mode_has_no_provider"
CK_GENERATIONS_STATE = "ck_certificate_generations_state_valid"
CK_GENERATIONS_MATERIAL_GUARD = "ck_certificate_generations_material_guard"
INDEX_ONE_LIVE = "uq_cert_generations_one_live"


def _in_list(column: str, values: Sequence[str]) -> str:
    """``column IN ('a', 'b')`` with the literals quoted for a CHECK."""
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def _guard_predicate(no_material_states: Sequence[str]) -> str:
    """The material guard, over the no-material branch for *no_material_states*."""
    return (
        f"{_in_list('state', no_material_states)} OR (key_ciphertext IS NOT NULL "
        "AND chain_ciphertext IS NOT NULL AND deke_id IS NOT NULL "
        "AND issued_at IS NOT NULL AND not_before IS NOT NULL AND not_after IS NOT NULL)"
    )


def _drop_constraint(table: str, name: str) -> None:
    """Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)."""
    op.execute(sa.text(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"'))


def _recreate(state_states: Sequence[str], live_states: Sequence[str]) -> None:
    """Replace the state CHECK, the guard and the one-live index in one transaction.

    Doing all three together is the point: between dropping the old state CHECK and
    creating the guard, a generation could name a state with no rule — so the order
    is drop state check, create state check, drop guard, create guard, and the index
    last. All of it is one migration transaction, so no committed schema is ever
    missing one of them.
    """
    _drop_constraint("certificate_generations", CK_GENERATIONS_STATE)
    op.create_check_constraint(
        op.f(CK_GENERATIONS_STATE), "certificate_generations", _in_list("state", state_states)
    )
    _drop_constraint("certificate_generations", CK_GENERATIONS_MATERIAL_GUARD)
    op.create_check_constraint(
        op.f(CK_GENERATIONS_MATERIAL_GUARD),
        "certificate_generations",
        _guard_predicate((*live_states, "FAILED")),
    )
    op.drop_index(INDEX_ONE_LIVE, table_name="certificate_generations")
    op.create_index(
        INDEX_ONE_LIVE,
        "certificate_generations",
        ["certificate_id"],
        unique=True,
        postgresql_where=sa.text(_in_list("state", live_states)),
    )


def _assert_no_manual_work() -> None:
    """Refuse a downgrade that would reinterpret or strand a manual certificate."""
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                manual integer;
                awaiting integer;
            BEGIN
                SELECT count(*) INTO manual FROM certificates WHERE dns_mode = 'manual';
                SELECT count(*) INTO awaiting
                  FROM certificate_generations
                 WHERE state = 'AWAITING_MANUAL';
                IF manual > 0 OR awaiting > 0 THEN
                    RAISE EXCEPTION
                        'refusing to downgrade past 5.3.2: % certificate(s) use manual DNS-01 '
                        'and % generation(s) are awaiting an operator-published challenge. '
                        'Dropping the mode would relabel them as automated requests whose '
                        'publisher was never chosen. Finish or remove them first.',
                        manual, awaiting;
                END IF;
            END $$;
            """
        )
    )


def upgrade() -> None:
    op.add_column(
        "certificates",
        sa.Column("dns_mode", sa.String(length=16), nullable=False, server_default="automated"),
    )
    op.create_check_constraint(
        op.f(CK_CERTIFICATES_DNS_MODE), "certificates", _in_list("dns_mode", DNS_MODES)
    )
    op.create_check_constraint(
        op.f(CK_CERTIFICATES_MANUAL_NO_PROVIDER),
        "certificates",
        "dns_mode <> 'manual' OR dns_provider_id IS NULL",
    )
    _recreate(GENERATION_STATES, LIVE_STATES)


def downgrade() -> None:
    """Remove the manual workflow — refusing while anything still uses it."""
    _assert_no_manual_work()
    previous_states = tuple(state for state in GENERATION_STATES if state != "AWAITING_MANUAL")
    previous_live = tuple(state for state in LIVE_STATES if state != "AWAITING_MANUAL")
    _recreate(previous_states, previous_live)
    _drop_constraint("certificates", CK_CERTIFICATES_MANUAL_NO_PROVIDER)
    _drop_constraint("certificates", CK_CERTIFICATES_DNS_MODE)
    op.drop_column("certificates", "dns_mode")
