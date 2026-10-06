"""Model / migration drift: the schema in the database must match the models.

Before this test, a model change without a migration was only caught late — when
a *different* integration test happened to run ``alembic upgrade head`` against a
fresh database and then failed for an unrelated-looking reason. This makes the
comparison explicit and local: Alembic's own autogenerate diff between the
migrated database and ``Base.metadata`` must be empty.

The comparison runs as the **owner** role. That is deliberate: reflection needs
to see every table, and the point here is the shape of the schema, not tenant
isolation (the RLS-enforced role could not even describe another schema's tables).
"""

from __future__ import annotations

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from app.models import Base
from sqlalchemy import create_engine, text

from tests.conftest import TEST_OWNER_DATABASE_URL

pytestmark = pytest.mark.integration


def test_models_and_migrations_do_not_drift() -> None:
    """``Base.metadata`` and the migrated database must describe the same schema."""
    engine = create_engine(TEST_OWNER_DATABASE_URL)
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            diff = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    assert diff == [], (
        "models and migrations have drifted; run `make makemigrations m=...`:\n"
        + "\n".join(f"  - {entry}" for entry in diff)
    )


def test_operations_type_check_matches_the_enum() -> None:
    """The DB whitelist and ``OperationType`` are the same closed set.

    The migration spells the set as a literal on purpose (a new type is a new
    migration). This asserts the two never disagree: an enum member the CHECK
    rejects would be a runtime 500, and a value the CHECK accepts that the app
    does not know is an exec surface nobody reviewed.
    """
    from app.models.enums import OperationType

    engine = create_engine(TEST_OWNER_DATABASE_URL)
    try:
        with engine.connect() as conn:
            definition = conn.execute(
                text(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conname = 'ck_operations_type_valid'"
                )
            ).scalar_one()
    finally:
        engine.dispose()

    for op_type in OperationType:
        assert f"'{op_type}'" in definition, f"{op_type} missing from the DB whitelist"

    # Reserved Phase 2 types must not be accepted by the database either.
    for reserved in ("nginx.reload", "certificate.install", "secret.env.apply"):
        assert reserved not in definition
