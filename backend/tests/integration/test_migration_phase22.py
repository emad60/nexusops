"""Phase 2.2 — the environment-type correction follows the documented precedence.

The documented rule is **slug first**: a recognised slug alias decides the type;
only when the slug names nothing recognised does a name alias decide; otherwise
the row defaults to ``DEV``. The earlier correction used a flat ``slug OR name``
test and so mis-typed rows whose slug says ``staging`` but whose name says
``production``. Migration ``e5f6a7b8c9d0`` fixes exactly that fingerprint while
preserving any other value an operator has deliberately set.
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

#: The revision right after the earlier (flat OR) correction — the state an
#: already-migrated database is in before this precedence fix.
POST_PHASE21_REVISION = "d4e5f6a7b8c9"

#: ``(name, slug, expected)`` covering every branch of the slug-first rule,
#: including the conflicting combinations the rule is written to resolve.
PRECEDENCE_CASES: list[tuple[str, str, str]] = [
    ("production", "staging", "STAGING"),  # slug (staging) beats name (production)
    ("prod", "stage", "STAGING"),
    ("Production", "STAGING", "STAGING"),  # case-insensitive, slug still wins
    ("staging", "production", "PROD"),  # slug (production) beats name (staging)
    ("staging", "prod", "PROD"),
    ("Production", "mystery", "PROD"),  # slug unrecognised -> name decides
    ("staging", "mystery-one", "STAGING"),  # slug unrecognised -> name decides
    ("qa", "mystery-two", "DEV"),  # neither recognised -> DEV
]


def _seed_legacy(database: str, cases: list[tuple[str, str, str]]) -> list[uuid.UUID]:
    """Create one legacy (application-scoped) environment per case."""
    org, project = uuid.uuid4(), uuid.uuid4()
    statements: list[Statement] = [
        (
            "INSERT INTO organizations (id, name, slug, description, status, is_provisional) "
            "VALUES (%s, 'Acme', 'acme', '', 'ACTIVE', false)",
            (org,),
        ),
        (
            "INSERT INTO projects (id, org_id, name, description, repository_url, default_branch) "
            "VALUES (%s, %s, 'Ymart', '', 'https://git.example/ymart.git', 'main')",
            (project, org),
        ),
    ]

    env_ids: list[uuid.UUID] = []
    for index, (name, slug, _expected) in enumerate(cases):
        app_id, env_id = uuid.uuid4(), uuid.uuid4()
        env_ids.append(env_id)
        statements.append(
            (
                "INSERT INTO applications "
                "(id, org_id, project_id, name, slug, description, repository_url, build_config) "
                "VALUES (%s, %s, %s, %s, %s, '', '', '{}')",
                (app_id, org, project, f"App {index}", f"app-{index}"),
            )
        )
        statements.append(
            (
                "INSERT INTO deployment_environments "
                "(id, org_id, application_id, name, slug, healthcheck_path, auto_deploy, config, "
                " created_at, updated_at) VALUES "
                "(%s, %s, %s, %s, %s, '', false, '{}', now(), now())",
                (env_id, org, app_id, name, slug),
            )
        )

    _exec(database, statements)
    return env_ids


def test_recognised_slug_alias_wins_over_a_conflicting_name(scratch_database: str) -> None:
    """Every branch of the slug-first rule, end to end through ``head``."""
    _run_migration(scratch_database, PRE_PHASE2_REVISION)
    env_ids = _seed_legacy(scratch_database, PRECEDENCE_CASES)
    _run_migration(scratch_database, "head")

    rows = _rows(scratch_database, "SELECT id, environment_type FROM deployment_environments")
    by_id = {str(row[0]): row[1] for row in rows}
    assert len(by_id) == len(PRECEDENCE_CASES), sorted(by_id)

    for env_id, (name, slug, expected) in zip(env_ids, PRECEDENCE_CASES, strict=True):
        assert by_id[str(env_id)] == expected, (
            f"slug={slug!r} name={name!r}: expected {expected}, got {by_id[str(env_id)]}"
        )


def test_correction_preserves_operator_set_values(scratch_database: str) -> None:
    """Only the previous migration's ``PROD`` output is corrected.

    A row already migrated to a *different* value is an operator decision and
    must survive; a row still carrying the erroneous ``PROD`` is fixed.
    """
    _run_migration(scratch_database, POST_PHASE21_REVISION)

    org, project = uuid.uuid4(), uuid.uuid4()
    erroneous, operator_dev, operator_staging, legitimate_prod = (uuid.uuid4() for _ in range(4))

    _exec(
        scratch_database,
        [
            (
                "INSERT INTO organizations (id, name, slug, description, status, is_provisional) "
                "VALUES (%s, 'Acme', 'acme', '', 'ACTIVE', false)",
                (org,),
            ),
            (
                "INSERT INTO projects (id, org_id, name, description, repository_url, default_branch) "
                "VALUES (%s, %s, 'Ymart', '', '', 'main')",
                (project, org),
            ),
            # The stale fingerprint: staging slug, prod name, previous PROD output.
            (
                "INSERT INTO deployment_environments "
                "(id, org_id, project_id, name, slug, environment_type, healthcheck_path, "
                " auto_deploy, config) VALUES "
                "(%s, %s, %s, 'production', 'staging', 'PROD', '', false, '{}'), "
                "(%s, %s, %s, 'prod', 'stage', 'DEV', '', false, '{}'), "
                "(%s, %s, %s, 'Production', 'Staging', 'STAGING', '', false, '{}'), "
                "(%s, %s, %s, 'staging', 'production', 'PROD', '', false, '{}')",
                (
                    erroneous,
                    org,
                    project,
                    operator_dev,
                    org,
                    project,
                    operator_staging,
                    org,
                    project,
                    legitimate_prod,
                    org,
                    project,
                ),
            ),
        ],
    )

    _run_migration(scratch_database, "head")

    types = {
        str(row[0]): row[1]
        for row in _rows(
            scratch_database, "SELECT id, environment_type FROM deployment_environments"
        )
    }
    assert types[str(erroneous)] == "STAGING", "the stale PROD fingerprint is corrected"
    assert types[str(operator_dev)] == "DEV", "an operator's DEV is preserved"
    assert types[str(operator_staging)] == "STAGING", "an operator's STAGING is preserved"
    assert types[str(legitimate_prod)] == "PROD", "a genuine production slug is untouched"
