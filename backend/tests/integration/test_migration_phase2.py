"""Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data.

The promotion of `deployment_environments` from application scope to project
scope is a **data** migration, so a passing `upgrade head` proves nothing on its
own. This module builds its own scratch databases, inserts the pre-Phase-2
shapes that a real instance would have, runs the migration, and checks three
things the plan promised:

1. **Deterministic duplicate handling.** Two applications of one project may
   each have defined ``production``. They must merge into ONE project
   environment, chosen deterministically, with no scalar field and no config key
   lost.
2. **Nothing is orphaned.** Every deployment that existed before still points at
   a live environment and its own application after the migration — the
   duplicate rows are deleted only *after* their deployments are re-pointed, so
   the FK's ``ON DELETE CASCADE`` never fires.
3. **History starts complete.** Every pre-existing secret gets a version row for
   its current value, and the new scope/unique constraints behave.

It also checks the two ends of the range: a database migrated from zero and a
database migrated from real legacy data. Alembic's own ``upgrade`` is used, so
the test exercises the same code path a deployment does.

Every statement is parameterized — the fixtures are constant, but test SQL that
interpolates is a habit worth never forming.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Sequence

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from tests.conftest import (
    _PG_PASSWORD,
    _PG_PORT,
    _PG_USER,
    BACKEND_DIR,
    TEST_PG_HOST,
)

pytestmark = pytest.mark.integration

PHASE2_REVISION = "b2c3d4e5f6a7"
PRE_PHASE2_REVISION = "f1a2b3c4d5e6"

ACME = "11111111-1111-1111-1111-111111111111"
GLOBEX = "22222222-2222-2222-2222-222222222222"
YMART = "aaaa1111-0000-0000-0000-000000000001"
OTHER_PROJECT = "bbbb2222-0000-0000-0000-000000000001"

API_APP = "aaaa1111-0000-0000-0000-0000000000a1"
WORKER_APP = "aaaa1111-0000-0000-0000-0000000000a2"
ADMIN_APP = "aaaa1111-0000-0000-0000-0000000000a3"
OTHER_APP = "bbbb2222-0000-0000-0000-0000000000a1"

#: Environment ids whose ``created_at`` ordering decides the merge survivor:
#: the API rows are the oldest, so they win a slug clash.
API_PROD = "aaaa1111-0000-0000-0000-0000000000e1"
API_STAGING = "aaaa1111-0000-0000-0000-0000000000e2"
WORKER_PROD = "aaaa1111-0000-0000-0000-0000000000e3"
ADMIN_STAGING = "aaaa1111-0000-0000-0000-0000000000e4"
OTHER_PROD = "bbbb2222-0000-0000-0000-0000000000e1"

D_API_PROD = "aaaa1111-0000-0000-0000-0000000000d1"
D_WORKER_PROD = "aaaa1111-0000-0000-0000-0000000000d2"
D_API_STAGING = "aaaa1111-0000-0000-0000-0000000000d3"
D_ADMIN_STAGING = "aaaa1111-0000-0000-0000-0000000000d4"

ORG_SECRET = "aaaa1111-0000-0000-0000-000000000051"
PROJECT_SECRET = "aaaa1111-0000-0000-0000-000000000062"

Statement = tuple[str, Sequence[object]]


#: The ``scratch_database`` fixture is defined in this package's conftest.py so
#: the Phase 2 and Phase 2.1 migration modules share one implementation.


def _owner_dsn(database: str) -> str:
    return f"postgresql://{_PG_USER}:{_PG_PASSWORD}@{TEST_PG_HOST}:{_PG_PORT}/{database}"


def _migration_dsn(database: str) -> str:
    return _owner_dsn(database).replace("postgresql://", "postgresql+psycopg://")


def _alembic_config(database: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", _migration_dsn(database))
    return cfg


def _run_migration(database: str, revision: str) -> None:
    """Upgrade ``database`` to ``revision`` through the app's own settings path.

    ``alembic/env.py`` resolves the URL from the cached settings singleton, so
    the DSN is exported and the cache cleared for the duration of the call —
    then restored, because every other test must keep talking to the test DB.
    """
    from app.core.config import get_settings

    previous = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["MIGRATION_DATABASE_URL"] = _migration_dsn(database)
    get_settings.cache_clear()
    try:
        command.upgrade(_alembic_config(database), revision)
    finally:
        if previous is None:
            os.environ.pop("MIGRATION_DATABASE_URL", None)
        else:
            os.environ["MIGRATION_DATABASE_URL"] = previous
        get_settings.cache_clear()


def _exec(database: str, statements: Sequence[Statement]) -> None:
    """Run statements in one transaction as the owner (committed on success)."""
    with psycopg.connect(_owner_dsn(database)) as conn:
        for sql, params in statements:
            conn.execute(sql, params)


def _rows(database: str, sql: str, params: Sequence[object] = ()) -> list[tuple[object, ...]]:
    with psycopg.connect(_owner_dsn(database)) as conn:
        return list(conn.execute(sql, params).fetchall())


def _seed_legacy_data(database: str) -> None:
    """The pre-Phase-2 shapes: application-scoped environments, per-app dupes."""
    _exec(
        database,
        [
            (
                "INSERT INTO organizations "
                "(id, name, slug, description, status, is_provisional) VALUES "
                "(%s, 'Acme', 'acme', '', 'ACTIVE', false), "
                "(%s, 'Globex', 'globex', '', 'ACTIVE', false)",
                (ACME, GLOBEX),
            ),
            (
                "INSERT INTO projects "
                "(id, org_id, name, description, repository_url, default_branch) VALUES "
                "(%s, %s, 'Ymart', 'retail', 'https://git.example/ymart.git', 'main'), "
                "(%s, %s, 'Warehouse', 'other tenant', 'https://git.example/wh.git', 'main')",
                (YMART, ACME, OTHER_PROJECT, GLOBEX),
            ),
            (
                "INSERT INTO applications "
                "(id, org_id, project_id, name, slug, description, repository_url, build_config) "
                "VALUES (%s, %s, %s, 'API', 'api', '', '', '{}'), "
                "(%s, %s, %s, 'Worker', 'worker', '', '', '{}'), "
                "(%s, %s, %s, 'Admin', 'admin', '', '', '{}'), "
                "(%s, %s, %s, 'Ingest', 'ingest', '', '', '{}')",
                (
                    API_APP,
                    ACME,
                    YMART,
                    WORKER_APP,
                    ACME,
                    YMART,
                    ADMIN_APP,
                    ACME,
                    YMART,
                    OTHER_APP,
                    GLOBEX,
                    OTHER_PROJECT,
                ),
            ),
            (
                # API: production (oldest, so it wins the merge) + staging whose
                # healthcheck is empty and must be filled from the duplicate.
                "INSERT INTO deployment_environments "
                "(id, org_id, application_id, name, slug, healthcheck_path, auto_deploy, config, "
                " created_at, updated_at) VALUES "
                "(%s, %s, %s, 'production', 'production', '/healthz', false, "
                ' \'{"LOG_LEVEL": "info", "REGION": "eu"}\', '
                " '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'), "
                "(%s, %s, %s, 'staging', 'staging', '', false, '{\"LOG_LEVEL\": \"debug\"}', "
                " '2026-01-02T00:00:00Z', '2026-01-02T00:00:00Z')",
                (
                    API_PROD,
                    ACME,
                    API_APP,
                    API_STAGING,
                    ACME,
                    API_APP,
                ),
            ),
            (
                # Worker: its own production — same slug, different application.
                "INSERT INTO deployment_environments "
                "(id, org_id, application_id, name, slug, healthcheck_path, auto_deploy, config, "
                " created_at, updated_at) VALUES "
                "(%s, %s, %s, 'production', 'production', '', true, "
                ' \'{"LOG_LEVEL": "warn", "WORKER_ONLY": "1"}\', '
                " '2026-01-03T00:00:00Z', '2026-01-03T00:00:00Z')",
                (WORKER_PROD, ACME, WORKER_APP),
            ),
            (
                # Admin: its own staging — collides, and carries the healthcheck
                # the survivor lacks.
                "INSERT INTO deployment_environments "
                "(id, org_id, application_id, name, slug, healthcheck_path, auto_deploy, config, "
                " created_at, updated_at) VALUES "
                "(%s, %s, %s, 'staging', 'staging', '/admin-healthz', false, "
                ' \'{"LOG_LEVEL": "trace"}\', '
                " '2026-01-04T00:00:00Z', '2026-01-04T00:00:00Z')",
                (ADMIN_STAGING, ACME, ADMIN_APP),
            ),
            (
                # A same-slug environment in the OTHER organization must not be
                # merged with Acme's: grouping is per organization.
                "INSERT INTO deployment_environments "
                "(id, org_id, application_id, name, slug, healthcheck_path, auto_deploy, config, "
                " created_at, updated_at) VALUES "
                "(%s, %s, %s, 'production', 'production', '/healthz', false, "
                ' \'{"LOG_LEVEL": "info"}\', '
                " '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')",
                (OTHER_PROD, GLOBEX, OTHER_APP),
            ),
            (
                # One deployment per environment; all four must survive.
                "INSERT INTO deployments "
                "(id, org_id, number, application_id, environment_id, version, git_commit, notes, "
                " status, trigger, is_rollback, failure_reason, cancel_requested) VALUES "
                "(%s, %s, 1, %s, %s, '1.0.0', 'abc', '', 'SUCCESS', 'MANUAL', false, '', false), "
                "(%s, %s, 1, %s, %s, '2.0.0', 'def', '', 'SUCCESS', 'API', false, '', false), "
                "(%s, %s, 2, %s, %s, '1.1.0', 'ghi', '', 'FAILED', 'MANUAL', false, 'boom', false), "
                "(%s, %s, 1, %s, %s, '3.0.0', 'jkl', '', 'SUCCESS', 'MANUAL', false, '', false)",
                (
                    D_API_PROD,
                    ACME,
                    API_APP,
                    API_PROD,
                    D_WORKER_PROD,
                    ACME,
                    WORKER_APP,
                    WORKER_PROD,
                    D_API_STAGING,
                    ACME,
                    API_APP,
                    API_STAGING,
                    D_ADMIN_STAGING,
                    ACME,
                    ADMIN_APP,
                    ADMIN_STAGING,
                ),
            ),
            (
                # Secrets: one organization-wide, one project-scoped, version 3.
                "INSERT INTO secrets "
                "(id, org_id, project_id, key, ciphertext, version, digest, description) VALUES "
                "(%s, %s, NULL, 'STRIPE_KEY', 'gAAAAA-cipher-1', 3, 'digest000111', 'org'), "
                "(%s, %s, %s, 'DATABASE_URL', 'gAAAAA-cipher-2', 3, 'digest000222', 'project')",
                (ORG_SECRET, ACME, PROJECT_SECRET, ACME, YMART),
            ),
        ],
    )


def test_promotes_environments_and_keeps_every_deployment_resolvable(
    scratch_database: str,
) -> None:
    _run_migration(scratch_database, PRE_PHASE2_REVISION)
    _seed_legacy_data(scratch_database)
    _run_migration(scratch_database, "head")

    # --- environments are project-scoped and merged -------------------------
    envs = _rows(
        scratch_database,
        "SELECT slug, project_id, environment_type, config, healthcheck_path, auto_deploy "
        "FROM deployment_environments WHERE org_id = %s ORDER BY slug",
        (ACME,),
    )
    assert [row[0] for row in envs] == ["production", "staging"], envs
    assert {str(row[1]) for row in envs} == {YMART}
    # Phase 2 defaulted every legacy row to DEV; the Phase 2.1 corrective
    # migration reclassifies the unambiguous slugs (production/staging).
    assert {row[2] for row in envs} == {"PROD", "STAGING"}, envs

    production = next(row for row in envs if row[0] == "production")
    staging = next(row for row in envs if row[0] == "staging")
    assert production[2] == "PROD"
    assert staging[2] == "STAGING"

    # Survivor = earliest created_at (API's row); fields fill from duplicates.
    assert production[5] is True, "auto_deploy must be the OR of the merged group"
    assert production[3]["REGION"] == "eu", "the survivor's own keys survive"
    assert production[3]["WORKER_ONLY"] == "1", "duplicate-only keys are unioned in"
    assert production[3]["LOG_LEVEL"] == "info", "the survivor wins a key clash"
    assert staging[4] == "/admin-healthz", "empty fields are filled from a duplicate"
    assert staging[3]["LOG_LEVEL"] == "debug", "the survivor wins a clash on staging too"

    # The other organization keeps its own environment — grouping is per org.
    other = _rows(
        scratch_database,
        "SELECT slug, project_id FROM deployment_environments WHERE org_id = %s",
        (GLOBEX,),
    )
    assert [tuple(map(str, row)) for row in other] == [("production", OTHER_PROJECT)]

    # --- every deployment still resolves to a live environment --------------
    deployments = _rows(
        scratch_database,
        "SELECT d.number, a.name, e.slug, e.project_id FROM deployments d "
        "JOIN applications a ON a.id = d.application_id "
        "JOIN deployment_environments e ON e.id = d.environment_id "
        "WHERE d.org_id = %s ORDER BY a.name, d.number",
        (ACME,),
    )
    assert [(row[0], row[1], row[2]) for row in deployments] == [
        (1, "API", "production"),
        (2, "API", "staging"),
        (1, "Admin", "staging"),
        (1, "Worker", "production"),
    ]
    assert {str(row[3]) for row in deployments} == {YMART}
    # No deployment was lost to the merge (the CASCADE would have taken them).
    assert len(deployments) == 4


def test_legacy_secrets_gain_scope_and_complete_history(scratch_database: str) -> None:
    _run_migration(scratch_database, PRE_PHASE2_REVISION)
    _seed_legacy_data(scratch_database)
    _run_migration(scratch_database, "head")

    # Scope: the environment level exists and is unused for legacy rows; the
    # project scope survives the promotion.
    scopes = _rows(
        scratch_database,
        "SELECT key, project_id, environment_id FROM secrets WHERE org_id = %s ORDER BY key",
        (ACME,),
    )
    assert [(row[0], str(row[1]) if row[1] else None, row[2]) for row in scopes] == [
        ("DATABASE_URL", YMART, None),
        ("STRIPE_KEY", None, None),
    ], scopes

    # History is backfilled from the current value, at the current version.
    versions = _rows(
        scratch_database,
        "SELECT s.key, v.version, v.ciphertext = s.ciphertext AS same_value "
        "FROM secrets s JOIN secret_versions v ON v.secret_id = s.id "
        "WHERE s.org_id = %s ORDER BY s.key",
        (ACME,),
    )
    assert [(row[0], row[1], row[2]) for row in versions] == [
        ("DATABASE_URL", 3, True),
        ("STRIPE_KEY", 3, True),
    ]

    # One partial unique index per scope level, plus the project-slug uniqueness.
    indexes = {row[0] for row in _rows(scratch_database, "SELECT indexname FROM pg_indexes")}
    assert {
        "ux_secrets_org_scope_key",
        "ux_secrets_project_scope_key",
        "ux_secrets_environment_scope_key",
        "uq_envs_project_slug",
    } <= indexes

    # A duplicate (project, slug) is rejected by the database, not just in code.
    with pytest.raises(psycopg.errors.UniqueViolation):
        _exec(
            scratch_database,
            [
                (
                    "INSERT INTO deployment_environments "
                    "(id, org_id, project_id, name, slug, healthcheck_path, auto_deploy, config, "
                    " environment_type) VALUES (%s, %s, %s, 'Production', 'production', '', false, "
                    " '{}', 'PROD')",
                    (uuid.uuid4(), ACME, YMART),
                )
            ],
        )


def test_environment_type_check_rejects_unknown_kinds(scratch_database: str) -> None:
    _run_migration(scratch_database, "head")
    with pytest.raises(psycopg.errors.CheckViolation):
        _exec(
            scratch_database,
            [
                (
                    "INSERT INTO organizations "
                    "(id, name, slug, description, status, is_provisional) "
                    "VALUES (%s, 'Acme', 'acme', '', 'ACTIVE', false)",
                    (ACME,),
                ),
                (
                    "INSERT INTO projects "
                    "(id, org_id, name, description, repository_url, default_branch) "
                    "VALUES (%s, %s, 'Ymart', '', '', 'main')",
                    (YMART, ACME),
                ),
                (
                    "INSERT INTO deployment_environments "
                    "(id, org_id, project_id, name, slug, healthcheck_path, auto_deploy, config, "
                    " environment_type) VALUES (%s, %s, %s, 'qa', 'qa', '', false, '{}', 'QA')",
                    (uuid.uuid4(), ACME, YMART),
                ),
            ],
        )


def test_migration_from_zero_matches_the_models(scratch_database: str) -> None:
    """A fresh database reaches the same shape the models describe."""
    _run_migration(scratch_database, "head")

    columns = {
        (row[0], row[1])
        for row in _rows(
            scratch_database,
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'public'",
        )
    }
    assert ("projects", "config") in columns
    assert ("deployment_environments", "project_id") in columns
    assert ("deployment_environments", "environment_type") in columns
    assert ("deployment_environments", "application_id") not in columns
    assert ("secrets", "environment_id") in columns
    assert ("secret_versions", "ciphertext") in columns

    # The new tenant-owned table is RLS-covered like every other one.
    policies = {
        row[0]
        for row in _rows(
            scratch_database,
            "SELECT polname FROM pg_policy WHERE polrelid = 'secret_versions'::regclass",
        )
    }
    assert {"secret_versions_tenant", "secret_versions_system"} <= policies
    assert _rows(
        scratch_database,
        "SELECT relrowsecurity FROM pg_class WHERE relname = 'secret_versions'",
    ) == [(True,)]


def test_exactly_one_alembic_head() -> None:
    """Phase 2 adds one migration; heads must not fork."""
    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple alembic heads: {heads}"
    # And the Phase 2 revision is reachable, i.e. actually applied by `head`.
    assert any(rev.revision == PHASE2_REVISION for rev in script.walk_revisions("base", "heads"))
