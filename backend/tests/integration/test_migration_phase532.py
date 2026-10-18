"""Phase 5.3.2 migration (`d0e1f2a3b4c5`): one column, one state, one refusal.

The revision is small and the interesting claims are about the *guarantees* it
turns from conventions into schema:

* **Existing certificates keep working.** A populated Phase 5.3 instance migrates
  forward, and every row that never chose a publisher is ``automated`` — the
  default is a backfill of the only workflow that existed, not a guess.
* **The manual pair is coherent in the database.** ``AWAITING_MANUAL`` is a live
  pre-issuance state, so it must satisfy the material guard (no material), the
  one-live index (a second open order is refused) and the state vocabulary. The
  manual/provider contradiction is refused by a CHECK, not by the service alone.
* **The downgrade refuses to reinterpret a request.** With a manual certificate
  or an awaiting generation the downgrade raises and leaves the data and the
  column intact; with neither it removes the column and a second upgrade restores
  it.

As in the other phase tests, everything runs through real Alembic runs against a
scratch database, so nothing depends on suite order.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest
from sqlalchemy.exc import InternalError, ProgrammingError

from .test_migration_phase2 import (
    _alembic_config,
    _exec,
    _rows,
    _run_downgrade,
    _run_migration,
)
from .test_migration_phase5 import DOMAIN, ORG, PRE_PHASE5_REVISION, _seed_phase4

pytestmark = pytest.mark.integration

#: The Phase 5.3 head — the schema this revision is written on top of.
PRE_PHASE532_REVISION = "c9d0e1f2a3b4"
#: The Phase 5.3.2 revision this module pins.
PHASE532_REVISION = "d0e1f2a3b4c5"

CERTIFICATE = "cccc5320-0000-0000-0000-000000000001"
OTHER_CERTIFICATE = "cccc5320-0000-0000-0000-000000000002"
GENERATION = "cccc5320-0000-0000-0000-000000000003"
SECOND_GENERATION = "cccc5320-0000-0000-0000-000000000004"
PROVIDER = "cccc5320-0000-0000-0000-000000000005"

FINGERPRINT = "a" * 64

#: Let's Encrypt staging — a member of the closed directory vocabulary. An
#: ``AWAITING_MANUAL`` row has placed an order, so the directory is required: the
#: resume has to know which CA is waiting.
DIRECTORY_URL = "https://acme-staging-v02.api.letsencrypt.org/directory"


def _insert_certificate(
    database: str,
    *,
    certificate_id: str = CERTIFICATE,
    primary_cn: str = "manual.example.com",
    dns_mode: str | None = None,
) -> None:
    """One certificate row; ``dns_mode`` is only written when the column exists."""
    if dns_mode is None:
        _exec(
            database,
            [
                (
                    "INSERT INTO certificates "
                    "(id, org_id, domain_id, primary_cn, sans, status, challenge_type, "
                    " auto_renew, key_algorithm, last_error) "
                    "VALUES (%s, %s, %s, %s, '[]'::jsonb, 'PENDING', 'dns-01', true, "
                    " 'ecdsa-p256', '')",
                    (certificate_id, ORG, DOMAIN, primary_cn),
                )
            ],
        )
        return
    _exec(
        database,
        [
            (
                "INSERT INTO certificates "
                "(id, org_id, domain_id, primary_cn, sans, status, challenge_type, "
                " auto_renew, key_algorithm, last_error, dns_mode) "
                "VALUES (%s, %s, %s, %s, '[]'::jsonb, 'PENDING', 'dns-01', true, "
                " 'ecdsa-p256', '', %s)",
                (certificate_id, ORG, DOMAIN, primary_cn, dns_mode),
            )
        ],
    )


def _insert_provider(database: str) -> None:
    _exec(
        database,
        [
            (
                "INSERT INTO dns_providers "
                "(id, org_id, name, kind, credentials_ciphertext, credential_fingerprint, "
                " deke_id, verify_error) "
                "VALUES (%s, %s, 'cloudflare-main', 'cloudflare', 'v1:test:not-a-real-key', "
                " %s, 1, '')",
                (PROVIDER, ORG, FINGERPRINT),
            )
        ],
    )


def _insert_generation(
    database: str,
    *,
    generation_id: str = GENERATION,
    certificate_id: str = CERTIFICATE,
    generation: int = 1,
    state: str = "AWAITING_MANUAL",
    directory_url: str | None = DIRECTORY_URL,
) -> None:
    _exec(
        database,
        [
            (
                "INSERT INTO certificate_generations "
                "(id, org_id, certificate_id, generation, state, order_state, last_error, "
                " attempt_count, directory_url) "
                "VALUES (%s, %s, %s, %s, %s, '{}', '', 0, %s)",
                (generation_id, ORG, certificate_id, generation, state, directory_url),
            )
        ],
    )


def _columns(database: str, table: str) -> set[str]:
    return {
        str(row[0])
        for row in _rows(
            database,
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s",
            (table,),
        )
    }


def _migrate_to_phase532(database: str) -> None:
    _run_migration(database, PRE_PHASE5_REVISION)
    _seed_phase4(database)
    _run_migration(database, PHASE532_REVISION)


def _migrate_to_phase53(database: str) -> None:
    _run_migration(database, PRE_PHASE5_REVISION)
    _seed_phase4(database)
    _run_migration(database, PRE_PHASE532_REVISION)


# --- 1. existing rows -------------------------------------------------------------


def test_existing_certificates_become_automated(scratch_database: str) -> None:
    """The only workflow that existed is the only value the backfill can mean."""
    _migrate_to_phase53(scratch_database)
    _insert_certificate(scratch_database)
    assert "dns_mode" not in _columns(scratch_database, "certificates")

    _run_migration(scratch_database, PHASE532_REVISION)

    assert _rows(
        scratch_database,
        "SELECT primary_cn, dns_mode, status FROM certificates",
    ) == [("manual.example.com", "automated", "PENDING")]
    # And the column has a server default, so a writer that does not mention it
    # (an older worker mid-rollout) cannot insert a row with no publisher.
    _insert_certificate(
        scratch_database, certificate_id=OTHER_CERTIFICATE, primary_cn="legacy.example.com"
    )
    assert _rows(
        scratch_database,
        "SELECT dns_mode FROM certificates WHERE id = %s",
        (OTHER_CERTIFICATE,),
    ) == [("automated",)]


def test_the_mode_vocabulary_is_closed(scratch_database: str) -> None:
    _migrate_to_phase532(scratch_database)
    _insert_certificate(scratch_database, dns_mode="manual")

    with pytest.raises(psycopg.errors.CheckViolation):
        _insert_certificate(
            scratch_database,
            certificate_id=OTHER_CERTIFICATE,
            primary_cn="typo.example.com",
            dns_mode="automatic",
        )


def test_a_manual_certificate_cannot_name_an_automated_publisher(
    scratch_database: str,
) -> None:
    """The contradiction is unrepresentable, not merely impolite.

    A row with both would describe two operators for one challenge, and the
    issuance path would have to choose which one to believe at challenge time.
    """
    _migrate_to_phase532(scratch_database)
    _insert_provider(scratch_database)
    _insert_certificate(scratch_database, dns_mode="manual")

    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(
            scratch_database,
            [
                (
                    "UPDATE certificates SET dns_provider_id = %s WHERE id = %s",
                    (PROVIDER, CERTIFICATE),
                )
            ],
        )

    # The automated half of the pair is still allowed: attaching a credential to
    # an automated certificate is the normal path.
    _insert_certificate(
        scratch_database,
        certificate_id=OTHER_CERTIFICATE,
        primary_cn="auto.example.com",
    )
    _exec(
        scratch_database,
        [
            (
                "UPDATE certificates SET dns_provider_id = %s WHERE id = %s",
                (PROVIDER, OTHER_CERTIFICATE),
            )
        ],
    )
    assert _rows(
        scratch_database,
        "SELECT dns_mode, dns_provider_id FROM certificates WHERE id = %s",
        (OTHER_CERTIFICATE,),
    ) == [("automated", uuid.UUID(PROVIDER))]


# --- 2. the new state -------------------------------------------------------------


def test_awaiting_manual_is_a_live_state_with_no_material(scratch_database: str) -> None:
    """Both halves of the definition, asserted by trying the forbidden row.

    ``AWAITING_MANUAL`` is in the guard's no-material branch (so the insert
    succeeds without a key) and in the one-live index (so a second open
    generation for the same certificate is refused). A state that satisfied only
    one ofthem would either fail on the first manual order or allow two.
    """
    _migrate_to_phase532(scratch_database)
    _insert_certificate(scratch_database, dns_mode="manual")

    _insert_generation(scratch_database)
    assert _rows(
        scratch_database,
        "SELECT state, key_ciphertext, deke_id FROM certificate_generations",
    ) == [("AWAITING_MANUAL", None, None)]

    # The index that carries the uniqueness has to name the state too, or two
    # manual orders could wait for two different sets of instructions at once.
    definitions = {
        str(row[0]): str(row[1])
        for row in _rows(
            scratch_database,
            "SELECT indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = 'public' AND tablename = 'certificate_generations'",
        )
    }
    assert "'AWAITING_MANUAL'" in definitions["uq_cert_generations_one_live"]

    with pytest.raises(psycopg.errors.UniqueViolation):
        _insert_generation(
            scratch_database,
            generation_id=SECOND_GENERATION,
            generation=2,
            state="ORDERING",
        )


def test_an_awaiting_generation_must_name_the_directory_it_ordered_at(
    scratch_database: str,
) -> None:
    """The order exists, so the CA that holds it is known and is required.

    Allowing NULL here would let a stopped attempt exist with no way to resume it
    (there is no directory to answer at) and no way to recognize which CA's order
    is open.
    """
    _migrate_to_phase532(scratch_database)
    _insert_certificate(scratch_database, dns_mode="manual")

    with pytest.raises(psycopg.errors.CheckViolation):
        _insert_generation(scratch_database, directory_url=None)


def test_a_generation_that_outlives_the_order_needs_its_material(
    scratch_database: str,
) -> None:
    """Widening the guard must not have widened it past the material states."""
    _migrate_to_phase532(scratch_database)
    _insert_certificate(scratch_database, dns_mode="manual")

    with pytest.raises(psycopg.errors.CheckViolation):
        _insert_generation(scratch_database, state="ISSUED")


# --- 3. the downgrade ---------------------------------------------------------------


def test_downgrade_removes_the_mode_when_nothing_uses_it(scratch_database: str) -> None:
    _migrate_to_phase53(scratch_database)
    _insert_certificate(scratch_database)
    _run_migration(scratch_database, PHASE532_REVISION)

    _run_downgrade(scratch_database, PRE_PHASE532_REVISION)
    assert "dns_mode" not in _columns(scratch_database, "certificates")
    assert _rows(
        scratch_database,
        "SELECT primary_cn, status FROM certificates",
    ) == [("manual.example.com", "PENDING")]

    # A downgrade is a reversal, not a dead end: the revision is forward-appliable
    # again and the backfilled default is the same fact.
    _run_migration(scratch_database, PHASE532_REVISION)
    assert _rows(scratch_database, "SELECT dns_mode FROM certificates") == [("automated",)]


def test_downgrade_refuses_to_relabel_a_manual_certificate(scratch_database: str) -> None:
    """The refusal is the point: dropping the column is not a data migration.

    Every manual certificate would silently become an automated request whose
    publisher was never chosen — a workflow nobody selected, waiting for a
    credential that does not exist.
    """
    _migrate_to_phase532(scratch_database)
    _insert_certificate(scratch_database, dns_mode="manual")

    with pytest.raises((InternalError, ProgrammingError, RuntimeError)) as raised:
        _run_downgrade(scratch_database, PRE_PHASE532_REVISION)
    assert "refusing to downgrade past 5.3.2" in str(raised.value)

    # The column and the fact it records are both still there.
    assert "dns_mode" in _columns(scratch_database, "certificates")
    assert _rows(scratch_database, "SELECT dns_mode FROM certificates") == [("manual",)]

    # And it is the *manual* row that stopped it: removing it lets the same
    # downgrade through.
    _exec(
        scratch_database,
        [("DELETE FROM certificates WHERE id = %s", (CERTIFICATE,))],
    )
    _run_downgrade(scratch_database, PRE_PHASE532_REVISION)
    assert "dns_mode" not in _columns(scratch_database, "certificates")


def test_downgrade_refuses_to_strand_an_awaiting_generation(scratch_database: str) -> None:
    """Narrowing the state CHECK would fail on the row; the guard says why first."""
    _migrate_to_phase532(scratch_database)
    _insert_certificate(scratch_database)
    _insert_generation(scratch_database)

    with pytest.raises((InternalError, ProgrammingError, RuntimeError)) as raised:
        _run_downgrade(scratch_database, PRE_PHASE532_REVISION)
    assert "refusing to downgrade past 5.3.2" in str(raised.value)

    assert _rows(
        scratch_database,
        "SELECT state FROM certificate_generations WHERE id = %s",
        (GENERATION,),
    ) == [("AWAITING_MANUAL",)]
    assert "dns_mode" in _columns(scratch_database, "certificates")


# --- 4. the chain -------------------------------------------------------------------


def test_the_revision_is_reachable_from_head() -> None:
    """One linear head, directly after the Phase 5.3 revision."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple alembic heads: {heads}"
    revision = script.get_revision(PHASE532_REVISION)
    assert revision.down_revision == PRE_PHASE532_REVISION
