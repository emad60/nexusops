"""Fix pre-existing model/migration drift (surfaced by the new drift check).

Two objects the models declare were never actually created by the initial
migrations. Both are invisible in normal use — which is exactly why they went
unnoticed — and were found by ``tests/integration/test_migration_drift.py``:

* ``fk_applications_current_deployment_id_deployments`` — the initial migration
  declared the constraint with ``use_alter=True`` inside ``op.create_table``.
  SQLAlchemy omits a ``use_alter`` constraint from the CREATE TABLE and expects a
  follow-up ``ALTER TABLE`` that the migration never emitted, so applications
  had no referential link (or ``SET NULL`` behavior) to their current deployment.
* ``ix_deployment_steps_created_at`` — ``TimestampMixin`` indexes ``created_at``
  on every table, but the migration that added the column to ``deployment_steps``
  (``c7e8b4f2a6d1``) created it without the matching index.

Revision ID: f1a2b3c4d5e6
Revises: e7c4a2b9d1f3
Created: 2026-10-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

#: Constraint names the operations migration produced before it wrapped them in
#: ``op.f`` — the naming convention prefixed an already-final name. Databases
#: migrated before that fix still carry the doubled form; normalise them here so
#: every database ends up with the names the models generate.
_RENAME_DUPLICATED_OPERATIONS_CHECKS = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_operations_ck_operations_status_valid'
    ) THEN
        ALTER TABLE operations
            RENAME CONSTRAINT ck_operations_ck_operations_status_valid
            TO ck_operations_status_valid;
    END IF;
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_operations_ck_operations_type_valid'
    ) THEN
        ALTER TABLE operations
            RENAME CONSTRAINT ck_operations_ck_operations_type_valid
            TO ck_operations_type_valid;
    END IF;
END $$;
"""

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e7c4a2b9d1f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(_RENAME_DUPLICATED_OPERATIONS_CHECKS)

    # Orphaned pointers (if any) would block the constraint, and the model's
    # intent is SET NULL semantics — so clear them first rather than fail.
    op.execute(
        sa.text(
            "UPDATE applications SET current_deployment_id = NULL "
            "WHERE current_deployment_id IS NOT NULL "
            "AND current_deployment_id NOT IN (SELECT id FROM deployments)"
        )
    )
    op.create_foreign_key(
        "fk_applications_current_deployment_id_deployments",
        "applications",
        "deployments",
        ["current_deployment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_deployment_steps_created_at", "deployment_steps", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_deployment_steps_created_at", table_name="deployment_steps")
    op.drop_constraint(
        "fk_applications_current_deployment_id_deployments", "applications", type_="foreignkey"
    )
