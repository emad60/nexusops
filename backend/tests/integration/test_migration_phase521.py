"""Phase 5.2.1 migration (`f5a6b7c8d9e0`): two columns, one invariant, one refusal.

The schema change is small, so the interesting claims are about *what it does not
do* and *what it will not undo*:

* **Additive, and only the approved columns.** A populated Phase 5.1 instance is
  migrated forward and every pre-existing row is checked: nothing is rewritten,
  and no column of a later slice (certificate material, providers, ACME accounts)
  appears — there is nowhere for a half-built 5.2.2 to hide.
* **The pair invariant is a database guarantee.** ``(dek_ciphertext IS NULL) =
  (dek_generation = 0)`` is asserted in both directions by trying to violate it,
  because a convention that only the application honours is not what makes
  "generation 0" trustworthy.
* **The downgrade refuses to destroy key material.** With a wrapped DEK present it
  raises and the data survives; with no wrapped DEK it removes the columns and a
  second upgrade restores them. Both paths are real Alembic runs, and the refusal
  is checked for the thing that actually matters: that the ciphertext is still
  there afterwards.

Every statement is parameterized, and each test builds its own scratch database,
so nothing here depends on the order the suite runs in.
"""

from __future__ import annotations

import psycopg
import pytest
from sqlalchemy.exc import InternalError, ProgrammingError

from .test_migration_phase2 import (
    Statement,
    _alembic_config,
    _exec,
    _rows,
    _run_downgrade,
    _run_migration,
)

pytestmark = pytest.mark.integration

#: The Phase 5.1 head — the schema this revision is written on top of.
PRE_PHASE521_REVISION = "c8d9e0f1a2b3"
#: The Phase 5.2.1 revision this module pins.
PHASE521_REVISION = "f5a6b7c8d9e0"

ORG = "77777777-7777-7777-7777-777777777777"
OTHER_ORG = "88888888-8888-8888-8888-888888888888"

#: A syntactically valid envelope. It is *not* a usable key: the ciphertext is the
#: base64 of a short fixed string, so even a misconfigured instance that somehow
#: read this row could not unwrap anything with it. It exists to exercise the
#: schema and the downgrade refusal.
SAMPLE_ENVELOPE = "v1:test:deterministic-test-key:1:bm90LWEtcmVhbC1rZXk="

#: Columns and tables the *later* slices own. None may exist yet: a placeholder
#: column is exactly the forward reference the approved slices forbid.
LATER_SLICE_COLUMNS = ("deke_id", "key_ciphertext", "chain_ciphertext", "dns_provider_id")
LATER_SLICE_TABLES = ("dns_providers", "acme_accounts", "certificate_deliveries")


def _seed_phase51(database: str) -> None:
    """A populated instance in the schema Phase 5.2.1 is written on top of."""
    statements: list[Statement] = [
        (
            "INSERT INTO organizations (id, name, slug, description, status, is_provisional) "
            "VALUES (%s, 'Acme', 'acme', 'tenant one', 'ACTIVE', false), "
            "(%s, 'Globex', 'globex', '', 'SUSPENDED', false)",
            (ORG, OTHER_ORG),
        ),
    ]
    _exec(database, statements)


def _columns(database: str) -> dict[str, tuple[str, str]]:
    """``column -> (data_type, is_nullable)`` for ``organizations``."""
    rows = _rows(
        database,
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'organizations'",
    )
    return {str(name): (str(dtype), str(nullable)) for name, dtype, nullable in rows}


def test_upgrade_adds_only_the_approved_columns(scratch_database: str) -> None:
    _run_migration(scratch_database, PRE_PHASE521_REVISION)
    _seed_phase51(scratch_database)
    assert "dek_ciphertext" not in _columns(scratch_database)

    _run_migration(scratch_database, "head")
    columns = _columns(scratch_database)

    assert columns["dek_ciphertext"] == ("text", "YES"), "the envelope column is nullable text"
    assert columns["dek_generation"] == ("integer", "NO")

    # Every pre-existing organization keeps the schema's own "no DEK yet" state:
    # nothing is backfilled into a generation the platform cannot unwrap.
    assert _rows(
        scratch_database,
        "SELECT dek_ciphertext, dek_generation FROM organizations ORDER BY name",
    ) == [(None, 0), (None, 0)]

    # The rest of each row is untouched.
    assert _rows(
        scratch_database,
        "SELECT name, slug, description, status FROM organizations ORDER BY name",
    ) == [("Acme", "acme", "tenant one", "ACTIVE"), ("Globex", "globex", "", "SUSPENDED")]


def test_upgrade_adds_no_later_slice_artifacts(scratch_database: str) -> None:
    _run_migration(scratch_database, "head")
    present = set(_columns(scratch_database))
    assert not present & set(LATER_SLICE_COLUMNS), (
        f"Phase 5.2.1 must not create later-slice columns: {present & set(LATER_SLICE_COLUMNS)}"
    )
    tables = {
        str(row[0])
        for row in _rows(
            scratch_database,
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'",
        )
    }
    assert not tables & set(LATER_SLICE_TABLES), (
        f"Phase 5.2.1 must not create later-slice tables: {tables & set(LATER_SLICE_TABLES)}"
    )


def test_the_constraint_is_named_exactly_once(scratch_database: str) -> None:
    """The naming convention must not be applied twice.

    A fresh database is the only place this can be checked honestly: passing the
    already-prefixed name to ``op.create_check_constraint`` yields
    ``ck_organizations_ck_organizations_dek_pair_valid`` on a fresh run, which
    ``compare_metadata`` cannot match against the model — silent drift that only
    shows up in the migration-drift test.
    """
    _run_migration(scratch_database, "head")
    names = {
        str(row[0])
        for row in _rows(
            scratch_database,
            "SELECT conname FROM pg_constraint "
            "WHERE conrelid = 'organizations'::regclass AND contype = 'c'",
        )
    }
    assert "ck_organizations_dek_pair_valid" in names
    assert not [name for name in names if name.count("ck_organizations") > 1]


def test_the_pair_invariant_is_enforced_in_both_directions(scratch_database: str) -> None:
    """A ciphertext behind generation 0, and a generation with no material, both fail."""
    _run_migration(scratch_database, "head")
    _seed_phase51(scratch_database)

    # A wrapped DEK with generation 0: an orphan, indistinguishable from "no DEK".
    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(
            scratch_database,
            [
                (
                    "UPDATE organizations SET dek_ciphertext = %s WHERE id = %s",
                    (SAMPLE_ENVELOPE, ORG),
                )
            ],
        )
    # A generation promising material that is not there.
    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(
            scratch_database,
            [("UPDATE organizations SET dek_generation = 1 WHERE id = %s", (ORG,))],
        )
    # The valid pair is accepted, in both write orders.
    _exec(
        scratch_database,
        [
            (
                "UPDATE organizations SET dek_ciphertext = %s, dek_generation = 1 WHERE id = %s",
                (SAMPLE_ENVELOPE, ORG),
            ),
            (
                "UPDATE organizations SET dek_generation = 0, dek_ciphertext = NULL WHERE id = %s",
                (ORG,),
            ),
        ],
    )
    assert _rows(
        scratch_database,
        "SELECT dek_ciphertext, dek_generation FROM organizations WHERE id = %s",
        (ORG,),
    ) == [(None, 0)]


def test_downgrade_removes_the_columns_when_no_dek_is_stored(scratch_database: str) -> None:
    _run_migration(scratch_database, "head")
    _seed_phase51(scratch_database)

    _run_downgrade(scratch_database, PRE_PHASE521_REVISION)
    columns = _columns(scratch_database)
    assert "dek_ciphertext" not in columns
    assert "dek_generation" not in columns
    assert _rows(scratch_database, "SELECT name, status FROM organizations ORDER BY name") == [
        ("Acme", "ACTIVE"),
        ("Globex", "SUSPENDED"),
    ]

    # And it is forward-appliable again: a downgrade is a reversal, not a dead end.
    _run_migration(scratch_database, "head")
    columns = _columns(scratch_database)
    assert columns["dek_ciphertext"] == ("text", "YES")
    assert columns["dek_generation"] == ("integer", "NO")


def test_downgrade_refuses_to_discard_a_wrapped_dek(scratch_database: str) -> None:
    """The refusal is the point: a rollback must not delete key material."""
    _run_migration(scratch_database, "head")
    _seed_phase51(scratch_database)
    _exec(
        scratch_database,
        [
            (
                "UPDATE organizations SET dek_ciphertext = %s, dek_generation = 1 WHERE id = %s",
                (SAMPLE_ENVELOPE, ORG),
            )
        ],
    )

    with pytest.raises((InternalError, ProgrammingError, RuntimeError)) as raised:
        _run_downgrade(scratch_database, PRE_PHASE521_REVISION)
    assert "refusing to drop the organization DEK envelope" in str(raised.value)

    # The material is still there, and the schema still has a place for it.
    columns = _columns(scratch_database)
    assert columns["dek_ciphertext"] == ("text", "YES")
    assert _rows(
        scratch_database,
        "SELECT dek_ciphertext, dek_generation FROM organizations WHERE id = %s",
        (ORG,),
    ) == [(SAMPLE_ENVELOPE, 1)]
    # The other organization was never populated, so it was never the reason.
    assert _rows(
        scratch_database,
        "SELECT dek_ciphertext, dek_generation FROM organizations WHERE id = %s",
        (OTHER_ORG,),
    ) == [(None, 0)]


def test_the_revision_is_reachable_from_head() -> None:
    """One linear head, with this revision directly after the Phase 5.1 one."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple alembic heads: {heads}"
    revision = script.get_revision(PHASE521_REVISION)
    assert revision.down_revision == PRE_PHASE521_REVISION
    assert script.get_revision(PRE_PHASE521_REVISION).down_revision == "b7c8d9e0f1a2"
