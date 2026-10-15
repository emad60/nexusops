"""Phase 5.2.1.2 migration (`a7b8c9d0e1f2`): the envelope leaves ``organizations``.

The audit finding this revision answers (F1) was not "the column is in the wrong
place" but "the column is behind no tenant net": ``organizations`` is RLS-exempt
because it *is* the tenant, so every read path that could reach an organization row
could read another tenant's wrapped DEK and PostgreSQL would not have refused.
The claims below are the ones that make the move real rather than cosmetic:

* **The envelope is a tenant table now.** ``organization_dek_envelopes`` carries
  ``org_id``, both row-level-security policies (tenant and system), the explicit
  application-role grant, and a unique constraint that makes "one authoritative
  envelope per organization" a database guarantee instead of a convention.
* **Populated envelopes are moved, never discarded.** An envelope written under
  5.2.1 is present, byte-identical, in the new table after the upgrade — the
  migration raises rather than dropping the source columns if the copy does not
  account for every one of them. (Verified by seeding a real envelope at the 5.2.1
  revision and reading it back at ``head``.)
* **The downgrade restores instead of destroying.** It recreates the columns, copies
  every envelope back, verifies the copy, and only then drops the table — and when
  the copy *cannot* be verified it stops with the key material still in place.
* **The generation invariant is enforced by the database** (audit finding F3),
  including the bound ``dek_generation >= 0`` that 5.2.1's design documented but did
  not create.

Every statement is parameterized, and each test builds its own scratch database, so
nothing here depends on the order the suite runs in.
"""

from __future__ import annotations

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

pytestmark = pytest.mark.integration

#: The Phase 5.2.1 revision: the schema whose envelope columns this one relocates.
PHASE521_REVISION = "f5a6b7c8d9e0"
#: This revision.
PHASE5212_REVISION = "a7b8c9d0e1f2"

TABLE = "organization_dek_envelopes"

ORG = "77777777-7777-7777-7777-777777777777"
OTHER_ORG = "88888888-8888-8888-8888-888888888888"

#: A syntactically valid envelope, and deliberately not a usable key: the ciphertext
#: is the base64 of a fixed disclaimer string, so even an instance misconfigured to
#: read it could not unwrap anything. It exists to exercise the schema and the
#: data-move assertions, which are about bytes being carried, not about cryptography.
SAMPLE_ENVELOPE = "v1:test:deterministic-test-key:1:bm90LWEtcmVhbC1rZXk="
SECOND_ENVELOPE = "v1:test:deterministic-test-key:2:YW5vdGhlci1ub3QtYS1rZXk="

#: ``id`` is generated here rather than by the database: the primary key carries a
#: Python-side default (``uuid_pk()``), so a raw insert has to supply one — which is
#: exactly what the application's own claim path does.
INSERT_ENVELOPE = (
    "INSERT INTO organization_dek_envelopes "
    "(id, org_id, dek_ciphertext, dek_generation, created_at, updated_at) "
    "VALUES (gen_random_uuid(), %s, %s, %s, now(), now())"
)


def _seed_phase51(database: str) -> None:
    """Two organizations in the schema Phase 5.2.1 is applied on top of."""
    _exec(
        database,
        [
            (
                "INSERT INTO organizations (id, name, slug, description, status, is_provisional) "
                "VALUES (%s, 'Acme', 'acme', 'tenant one', 'ACTIVE', false), "
                "(%s, 'Globex', 'globex', '', 'SUSPENDED', false)",
                (ORG, OTHER_ORG),
            )
        ],
    )


def _seed_envelope_on_organizations(database: str, org: str = ORG) -> None:
    """A populated 5.2.1 envelope: the state the move must not lose."""
    _exec(
        database,
        [
            (
                "UPDATE organizations SET dek_ciphertext = %s, dek_generation = 1 WHERE id = %s",
                (SAMPLE_ENVELOPE, org),
            )
        ],
    )


def _columns(database: str, table: str) -> dict[str, tuple[str, str]]:
    """``column -> (data_type, is_nullable)`` for *table*."""
    rows = _rows(
        database,
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s",
        (table,),
    )
    return {str(name): (str(dtype), str(nullable)) for name, dtype, nullable in rows}


def _tables(database: str) -> set[str]:
    return {
        str(row[0])
        for row in _rows(database, "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    }


def _stored_envelopes(database: str) -> list[tuple[str, str, int]]:
    """``(org_id, ciphertext, generation)`` for every populated envelope, ordered."""
    return [
        (str(row[0]), str(row[1]), int(row[2]))
        for row in _rows(
            database,
            # The table name is a module constant, spelled out rather than
            # interpolated so the statement is a literal (ruff S608) and reads as
            # the query it is.
            "SELECT org_id, dek_ciphertext, dek_generation FROM organization_dek_envelopes "
            "WHERE dek_ciphertext IS NOT NULL ORDER BY org_id",
        )
    ]


# --- the move -----------------------------------------------------------------


def test_upgrade_moves_a_populated_envelope_to_its_own_tenant_table(
    scratch_database: str,
) -> None:
    _run_migration(scratch_database, PHASE521_REVISION)
    _seed_phase51(scratch_database)
    _seed_envelope_on_organizations(scratch_database)
    assert TABLE not in _tables(scratch_database)

    _run_migration(scratch_database, "head")

    # The envelope columns are gone from the RLS-exempt table, and only from it:
    # the rest of the organization row is untouched.
    columns = _columns(scratch_database, "organizations")
    assert "dek_ciphertext" not in columns
    assert "dek_generation" not in columns
    assert _rows(
        scratch_database, "SELECT name, slug, status FROM organizations ORDER BY name"
    ) == [("Acme", "acme", "ACTIVE"), ("Globex", "globex", "SUSPENDED")]

    # The value itself moved: same ciphertext, same generation, still exactly one
    # envelope for the organization that had one.
    assert _stored_envelopes(scratch_database) == [(ORG, SAMPLE_ENVELOPE, 1)]
    assert _rows(scratch_database, "SELECT count(*) FROM organization_dek_envelopes") == [(1,)]


def test_organizations_that_had_no_envelope_get_no_row(scratch_database: str) -> None:
    """The move creates rows only where there was key material.

    A row with a NULL ciphertext and generation 0 would be a *state* the old schema
    carried (the column existed on every organization) but not an envelope. Creating
    one per tenant would be inventing key-management records during a schema move.
    """
    _run_migration(scratch_database, PHASE521_REVISION)
    _seed_phase51(scratch_database)
    _seed_envelope_on_organizations(scratch_database, ORG)

    _run_migration(scratch_database, "head")

    assert [row[0] for row in _stored_envelopes(scratch_database)] == [ORG]
    assert _rows(
        scratch_database,
        "SELECT count(*) FROM organization_dek_envelopes WHERE org_id = %s",
        (OTHER_ORG,),
    ) == [(0,)]
    # ``dek_generation`` is NOT NULL with default 0, so a row *can* express "no DEK
    # yet" — the point is that this migration does not manufacture such rows.
    assert _columns(scratch_database, TABLE)["dek_generation"] == ("integer", "NO")


# --- the shape the new table has ----------------------------------------------


def test_the_envelope_table_is_unique_per_organization(scratch_database: str) -> None:
    """Two envelopes for one tenant are refused by the database, not by a service."""
    _run_migration(scratch_database, "head")
    _seed_phase51(scratch_database)
    _exec(scratch_database, [(INSERT_ENVELOPE, (ORG, SAMPLE_ENVELOPE, 1))])

    with pytest.raises(psycopg.errors.UniqueViolation):
        _exec(scratch_database, [(INSERT_ENVELOPE, (ORG, SECOND_ENVELOPE, 1))])

    # A second organization is not affected by the constraint.
    _exec(scratch_database, [(INSERT_ENVELOPE, (OTHER_ORG, SECOND_ENVELOPE, 1))])
    assert _rows(scratch_database, "SELECT count(*) FROM organization_dek_envelopes") == [(2,)]


def test_the_generation_bound_and_the_pair_invariant_are_database_guarantees(
    scratch_database: str,
) -> None:
    """F3: a negative generation, and either half of an inconsistent pair, fail.

    The bound is the part 5.2.1 documented but did not create. The pair invariant is
    the one it did create, restated here because it now constrains a different table
    — and because "the check moved with the column" is exactly the kind of thing a
    migration can quietly get wrong.
    """
    _run_migration(scratch_database, "head")
    _seed_phase51(scratch_database)

    # A negative generation is not a state the model can produce.
    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(scratch_database, [(INSERT_ENVELOPE, (ORG, SAMPLE_ENVELOPE, -1))])
    # A ciphertext behind generation 0: an orphan, indistinguishable from "no DEK".
    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(scratch_database, [(INSERT_ENVELOPE, (ORG, SAMPLE_ENVELOPE, 0))])
    # A generation promising material that is not there.
    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(scratch_database, [(INSERT_ENVELOPE, (ORG, None, 1))])

    # Both valid states are accepted: the documented initial state, and a real one.
    _exec(
        scratch_database,
        [
            (INSERT_ENVELOPE, (ORG, None, 0)),
            (INSERT_ENVELOPE, (OTHER_ORG, SAMPLE_ENVELOPE, 1)),
        ],
    )
    assert [
        (str(row[0]), row[1], int(row[2]))
        for row in _rows(
            scratch_database,
            "SELECT org_id, dek_ciphertext, dek_generation FROM organization_dek_envelopes "
            "ORDER BY org_id",
        )
    ] == [(ORG, None, 0), (OTHER_ORG, SAMPLE_ENVELOPE, 1)]


def test_the_envelope_table_is_a_tenant_table_and_the_app_role_can_use_it(
    scratch_database: str,
) -> None:
    """RLS plus the grant: the policies are only load-bearing for a non-owner role.

    The tenancy migration's blanket ``GRANT ... ON ALL TABLES`` ran long before this
    table existed, so the explicit grant here is what stops the runtime role from
    having no access at all — and the role must not be the owner and must not bypass
    RLS, or the two policies would be inert.
    """
    from tests.conftest import TEST_APP_ROLE

    _run_migration(scratch_database, "head")

    relrowsecurity, policies = _rows(
        scratch_database,
        "SELECT c.relrowsecurity, "
        "       (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid) "
        "FROM pg_class c WHERE c.relname = %s",
        (TABLE,),
    )[0]
    assert relrowsecurity is True
    assert policies == 2, "one tenant policy and one system policy, as everywhere else"

    names = {
        str(row[0])
        for row in _rows(
            scratch_database,
            "SELECT polname FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid "
            "WHERE c.relname = %s ORDER BY polname",
            (TABLE,),
        )
    }
    assert names == {f"{TABLE}_system", f"{TABLE}_tenant"}

    # The tenant policy constrains reads *and* writes with the tenant column; the
    # system policy keys on the sentinel GUC instead, exactly as on every other
    # tenant table, so only one of the two mentions ``org_id``.
    both_directions = _rows(
        scratch_database,
        "SELECT count(*) FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid "
        "WHERE c.relname = %s "
        "  AND pg_get_expr(p.polqual, p.polrelid) LIKE '%%org_id%%' "
        "  AND pg_get_expr(p.polwithcheck, p.polrelid) LIKE '%%org_id%%'",
        (TABLE,),
    )
    assert both_directions == [(1,)]

    # The application role has the four DML verbs, is not the owner, and is not
    # exempt from the policies.
    granted = {
        str(row[0])
        for row in _rows(
            scratch_database,
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE table_schema = 'public' AND table_name = %s AND grantee = %s",
            (TABLE, TEST_APP_ROLE),
        )
    }
    assert granted == {"SELECT", "INSERT", "UPDATE", "DELETE"}, granted
    owner_is_app, bypasses_rls = _rows(
        scratch_database,
        "SELECT c.relowner = (SELECT oid FROM pg_roles WHERE rolname = %s), "
        "       (SELECT rolbypassrls FROM pg_roles WHERE rolname = %s) "
        "FROM pg_class c WHERE c.relname = %s",
        (TEST_APP_ROLE, TEST_APP_ROLE, TABLE),
    )[0]
    assert owner_is_app is False, "the RLS-enforced role must not own the table"
    assert bypasses_rls is False


def test_the_constraint_names_match_the_models(scratch_database: str) -> None:
    """The migration's rendered names must be the ones the model metadata declares.

    A doubled convention prefix (``ck_organization_dek_envelopes_ck_...``) is the
    failure this catches: the constraints would still *work*, and only the drift
    check would notice, which is too late to be useful.
    """
    from app.models.tenancy import OrganizationDekEnvelope

    _run_migration(scratch_database, "head")
    actual = {
        str(row[0])
        for row in _rows(
            scratch_database,
            "SELECT conname FROM pg_constraint WHERE conrelid = "
            "(SELECT oid FROM pg_class WHERE relname = %s)",
            (TABLE,),
        )
    }
    expected = {
        str(constraint.name) for constraint in OrganizationDekEnvelope.__table__.constraints
    }
    assert expected <= actual, f"missing from the migration: {sorted(expected - actual)}"
    assert not [name for name in actual if name.count("dek_pair_valid") > 1]
    assert not [name for name in actual if name.count("dek_generation_non_negative") > 1]


# --- downgrade: restore, or stop with the data still in place ------------------


def test_downgrade_restores_the_envelope_and_the_reupgrade_moves_it_back(
    scratch_database: str,
) -> None:
    """The reversal is a data move in the other direction, and it is reversible.

    5.2.1's own downgrade refused to run while any envelope existed, because the
    columns were the only home the data had. Now there is somewhere for it to go, so
    the refusal is not needed — but restoring without dropping is.
    """
    _run_migration(scratch_database, PHASE521_REVISION)
    _seed_phase51(scratch_database)
    _seed_envelope_on_organizations(scratch_database)
    _run_migration(scratch_database, "head")
    assert _stored_envelopes(scratch_database) == [(ORG, SAMPLE_ENVELOPE, 1)]

    _run_downgrade(scratch_database, PHASE521_REVISION)

    assert TABLE not in _tables(scratch_database)
    assert _rows(
        scratch_database,
        "SELECT dek_ciphertext, dek_generation FROM organizations WHERE id = %s",
        (ORG,),
    ) == [(SAMPLE_ENVELOPE, 1)]
    assert _rows(
        scratch_database,
        "SELECT dek_ciphertext, dek_generation FROM organizations WHERE id = %s",
        (OTHER_ORG,),
    ) == [(None, 0)]

    # Forward again: same envelope, same generation, nothing invented.
    _run_migration(scratch_database, "head")
    assert _stored_envelopes(scratch_database) == [(ORG, SAMPLE_ENVELOPE, 1)]
    assert _rows(scratch_database, "SELECT count(*) FROM organization_dek_envelopes") == [(1,)]


def test_downgrade_refuses_to_drop_the_table_when_the_copy_cannot_be_verified(
    scratch_database: str,
) -> None:
    """The guard is the anti-data-loss property, so it is proved, not assumed.

    The only way to make the restore under-account for what is stored is two
    populated rows for one organization, which the unique constraint forbids — so
    the test removes the constraint first. That is an anomaly no supported code path
    can produce, which is exactly why it is worth forcing: the failure mode being
    guarded against is a downgrade that drops the only copy of a wrapped DEK, and
    "it cannot happen through the API" is not the same as "it stops the migration".
    """
    _run_migration(scratch_database, "head")
    _seed_phase51(scratch_database)
    _exec(
        scratch_database,
        [
            (INSERT_ENVELOPE, (ORG, SAMPLE_ENVELOPE, 1)),
            # Forced anomaly: the unique constraint is what normally makes this
            # impossible, so it is dropped for the duration of this test.
            (f"ALTER TABLE {TABLE} DROP CONSTRAINT uq_organization_dek_envelopes_org_id", ()),
            (INSERT_ENVELOPE, (ORG, SECOND_ENVELOPE, 1)),
        ],
    )

    with pytest.raises((InternalError, ProgrammingError, RuntimeError)) as raised:
        _run_downgrade(scratch_database, PHASE521_REVISION)
    assert "refusing to drop organization_dek_envelopes" in str(raised.value)

    # Nothing was destroyed: the table is still there with both envelopes, and the
    # migration can be retried once the anomaly is resolved.
    assert TABLE in _tables(scratch_database)
    assert _stored_envelopes(scratch_database) == [
        (ORG, SAMPLE_ENVELOPE, 1),
        (ORG, SECOND_ENVELOPE, 1),
    ]


# --- the chain -----------------------------------------------------------------


def test_the_revision_sits_directly_after_phase_521() -> None:
    """One linear head, with this revision immediately after the 5.2.1 one.

    This revision is no longer the tip — Phase 5.2.2 (``b8c9d0e1f2a3``) extends
    the chain — so the claim is about the *chain*: this revision's own
    down-revision is unchanged, and the single head still passes through it. A
    second head, a re-parented revision or a branch would all fail here.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple alembic heads: {heads}"
    assert script.get_revision(PHASE5212_REVISION).down_revision == PHASE521_REVISION

    # Walked from the head downwards: this revision must still be on the way in,
    # and still immediately after 5.2.1.
    chain = [revision.revision for revision in script.walk_revisions(head=heads[0], base="base")]
    assert PHASE5212_REVISION in chain, "5.2.1.2 is not an ancestor of the head"
    assert chain.index(PHASE521_REVISION) == chain.index(PHASE5212_REVISION) + 1
