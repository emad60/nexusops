"""Phase 2.1 corrective migration: legacy ``environment_type`` classification.

Phase 2 defaulted every pre-existing environment to ``DEV``. This module proves
the corrective migration classifies the unambiguous slugs/names with a small,
case-normalised, exact-match mapping — and nothing more:

* ``production``/``prod`` → ``PROD``, ``staging``/``stage`` → ``STAGING``;
* ``dev``/``development`` and anything unknown stay ``DEV``;
* matching is case-insensitive and trims surrounding whitespace, and
  ``slug`` wins over ``name`` when a row disagrees;
* only rows still carrying the Phase 2 default ``DEV`` are candidates, so an
  operator's explicit post-Phase-2 classification is never overwritten;
* environment ids, deployments, uniqueness and organization ownership are
  untouched (the statement updates one descriptive column in place);
* the correction applies to every organization, independently.

The scratch databases and migration helpers come from the Phase 2 migration test
module — same database, same Alembic code path a deployment uses.
"""

from __future__ import annotations

import uuid

import pytest

from .test_migration_phase2 import (
    PRE_PHASE2_REVISION,
    Statement,
    _exec,
    _rows,
    _run_migration,
)

pytestmark = pytest.mark.integration

#: The integrity-only revision: Phase 2 applied, the type correction **not** yet.
POST_PHASE2_REVISION = "c3d4e5f6a7b8"

#: ``(name, slug, expected_type)`` — one legacy environment each, all distinct
#: literal slugs so the Phase 2 merge step never collapses two cases into one.
ENV_TYPE_CASES: list[tuple[str, str, str]] = [
    ("production", "production", "PROD"),
    ("Production", "Production", "PROD"),
    ("Prod", "prod", "PROD"),
    ("staging", "staging", "STAGING"),
    ("Stage", "stage", "STAGING"),
    ("development", "development", "DEV"),
    ("dev", "dev", "DEV"),
    ("qa", "qa", "DEV"),
    ("Weird", "weird", "DEV"),
    ("Production", "mystery", "PROD"),  # slug unknown; the name classifies it
    ("staging", "PROD", "PROD"),  # slug wins over a disagreeing name
]


def _seed_typed_environments(database: str) -> dict:
    """Insert one legacy environment per case, in two organizations."""
    acme, globex = uuid.uuid4(), uuid.uuid4()
    acme_project, globex_project = uuid.uuid4(), uuid.uuid4()

    statements: list[Statement] = [
        (
            "INSERT INTO organizations "
            "(id, name, slug, description, status, is_provisional) VALUES "
            "(%s, 'Acme', 'acme', '', 'ACTIVE', false), "
            "(%s, 'Globex', 'globex', '', 'ACTIVE', false)",
            (acme, globex),
        ),
        (
            "INSERT INTO projects "
            "(id, org_id, name, description, repository_url, default_branch) VALUES "
            "(%s, %s, 'Ymart', '', 'https://git.example/ymart.git', 'main'), "
            "(%s, %s, 'Warehouse', '', '', 'main')",
            (acme_project, acme, globex_project, globex),
        ),
    ]

    expectations: list[tuple[uuid.UUID, str]] = []
    for index, (name, slug, expected) in enumerate(ENV_TYPE_CASES):
        app_id, env_id = uuid.uuid4(), uuid.uuid4()
        expectations.append((env_id, expected))
        statements.append(
            (
                "INSERT INTO applications "
                "(id, org_id, project_id, name, slug, description, repository_url, build_config) "
                "VALUES (%s, %s, %s, %s, %s, '', '', '{}')",
                (app_id, acme, acme_project, f"App {index}", f"app-{index}"),
            )
        )
        statements.append(
            (
                "INSERT INTO deployment_environments "
                "(id, org_id, application_id, name, slug, healthcheck_path, auto_deploy, config, "
                " created_at, updated_at) VALUES "
                "(%s, %s, %s, %s, %s, '', false, '{}', now(), now())",
                (env_id, acme, app_id, name, slug),
            )
        )

    # A second organization with its own production environment: the correction
    # is per-org and must be applied there too.
    other_app, other_env = uuid.uuid4(), uuid.uuid4()
    expectations.append((other_env, "PROD"))
    statements.append(
        (
            "INSERT INTO applications "
            "(id, org_id, project_id, name, slug, description, repository_url, build_config) "
            "VALUES (%s, %s, %s, 'Ingest', 'ingest', '', '', '{}')",
            (other_app, globex, globex_project),
        )
    )
    statements.append(
        (
            "INSERT INTO deployment_environments "
            "(id, org_id, application_id, name, slug, healthcheck_path, auto_deploy, config, "
            " created_at, updated_at) VALUES "
            "(%s, %s, %s, 'production', 'production', '', false, '{}', now(), now())",
            (other_env, globex, other_app),
        )
    )

    _exec(database, statements)
    return {
        "acme": acme,
        "globex": globex,
        "expectations": expectations,
        "total": len(ENV_TYPE_CASES) + 1,
    }


def test_corrects_legacy_environment_types(scratch_database: str) -> None:
    """Every case is classified as documented, ids and ownership intact."""
    _run_migration(scratch_database, PRE_PHASE2_REVISION)
    seeded = _seed_typed_environments(scratch_database)
    _run_migration(scratch_database, "head")

    rows = _rows(
        scratch_database,
        "SELECT id, org_id, environment_type FROM deployment_environments",
    )
    by_id = {str(row[0]): (str(row[1]), row[2]) for row in rows}

    # No environment was lost to the promotion/merge/classification.
    assert len(by_id) == seeded["total"], sorted(by_id)

    for env_id, expected in seeded["expectations"]:
        assert str(env_id) in by_id, f"environment {env_id} disappeared"
        _org_id, actual = by_id[str(env_id)]
        assert actual == expected, f"environment {env_id}: expected {expected}, got {actual}"

    # Organization ownership is preserved (both tenants keep their own rows).
    orgs = {
        str(row[0])
        for row in _rows(scratch_database, "SELECT DISTINCT org_id FROM deployment_environments")
    }
    assert orgs == {str(seeded["acme"]), str(seeded["globex"])}


def test_only_dev_defaulted_rows_are_corrected(scratch_database: str) -> None:
    """An explicit non-DEV classification survives the corrective migration.

    The correction runs *after* Phase 2, so an operator could already have set a
    type deliberately. A row that is not the Phase 2 default (``DEV``) — even if
    its slug says ``production`` — must be left exactly as it is.
    """
    _run_migration(scratch_database, POST_PHASE2_REVISION)

    org, project, environment = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    _exec(
        scratch_database,
        [
            (
                "INSERT INTO organizations "
                "(id, name, slug, description, status, is_provisional) VALUES "
                "(%s, 'Acme', 'acme', '', 'ACTIVE', false)",
                (org,),
            ),
            (
                "INSERT INTO projects "
                "(id, org_id, name, description, repository_url, default_branch) VALUES "
                "(%s, %s, 'Ymart', '', '', 'main')",
                (project, org),
            ),
            (
                "INSERT INTO deployment_environments "
                "(id, org_id, project_id, name, slug, environment_type, healthcheck_path, "
                " auto_deploy, config) VALUES "
                "(%s, %s, %s, 'production', 'production', 'STAGING', '', false, '{}')",
                (environment, org, project),
            ),
        ],
    )

    _run_migration(scratch_database, "head")

    assert _rows(
        scratch_database,
        "SELECT environment_type FROM deployment_environments WHERE id = %s",
        (environment,),
    ) == [("STAGING",)]


def test_corrective_migration_is_reachable_from_head() -> None:
    """The correction is part of ``head`` and adds no extra Alembic head."""
    from alembic.script import ScriptDirectory

    from .test_migration_phase2 import _alembic_config

    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple alembic heads: {heads}"
    revisions = {rev.revision for rev in script.walk_revisions("base", "heads")}
    assert {"c3d4e5f6a7b8", "d4e5f6a7b8c9"} <= revisions
