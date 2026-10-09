"""Phase 2.1 — enforce append-only ``secret_versions`` in the database.

Phase 2 created ``secret_versions`` as an *append-only* history but granted the
runtime application role ``UPDATE`` and ``DELETE`` on it, with the "append-only"
guarantee enforced only in the service layer (no UPDATE/DELETE path). A grant is
not a guarantee: any ordinary SQL path running as the app role — a bug, a
migration script, a compromised worker — could rewrite or erase history, and
nothing in PostgreSQL objected.

This migration makes the guarantee real, without changing the documented
lifecycle:

* ``REVOKE UPDATE, DELETE`` from the application role. The runtime can no longer
  modify or delete a version row at all; it keeps ``SELECT`` (history reads) and
  ``INSERT`` (create / rotate / rollback append new versions).
* A row-level ``BEFORE UPDATE OR DELETE`` trigger refuses ``UPDATE`` outright, and
  refuses ``DELETE`` unless the row's **parent secret is already gone**. That
  second condition is the cascade discriminator: PostgreSQL runs referential
  actions (``ON DELETE CASCADE``) *after* the parent row is deleted, so a version
  removed as part of deleting its Secret sees no parent and is allowed, while a
  direct ``DELETE FROM secret_versions`` sees the parent and is refused. The
  trigger fires for every role — including the owner — so even a migration script
  cannot rewrite history; the only way a version row leaves the table is by
  deleting the Secret that owns it.

Deletion policy (unchanged, and now explicit): deleting a Secret is a **hard
delete that cascades its version history** (``secrets`` → ``secret_versions``
``ON DELETE CASCADE``). History is retained for the lifetime of the Secret, not
in perpetuity; the deletion itself is recorded in the append-only ``audit_logs``
(``secret.delete``). See docs/secrets-architecture.md §3.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Created: 2026-10-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: UPDATE is refused outright. DELETE is refused unless the parent ``secrets`` row
#: is already deleted — true only inside the FK's ``ON DELETE CASCADE``, because
#: PostgreSQL performs referential actions after the parent row is removed.
SECRET_VERSION_GUARD = """
CREATE OR REPLACE FUNCTION nexusops_block_secret_version_mutation() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'secret_versions is append-only (attempted UPDATE of version %)',
            OLD.version;
    END IF;
    IF EXISTS (SELECT 1 FROM secrets s WHERE s.id = OLD.secret_id) THEN
        RAISE EXCEPTION
            'secret_versions rows are removed only by deleting their parent secret '
            '(attempted DELETE of version %)',
            OLD.version;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
"""

SECRET_VERSION_GUARD_DROP = """
DROP FUNCTION IF EXISTS nexusops_block_secret_version_mutation() CASCADE;
"""

#: Remove the Phase 2 grant that let the runtime rewrite history. Mirrors the
#: grant block's GUC hand-off so the app role name never becomes a literal.
REVOKE_FROM_APP_ROLE = """
DO $$
DECLARE
    app_role text := current_setting('nexusops.migration.role', true);
BEGIN
    IF app_role IS NULL OR app_role = '' THEN
        RAISE NOTICE 'nexusops: POSTGRES_APP_USER is empty; skipping secret_versions revoke';
        RETURN;
    END IF;
    EXECUTE 'REVOKE UPDATE, DELETE ON secret_versions FROM ' || quote_ident(app_role);
END $$;
"""

#: Restore the Phase 2 grant so ``downgrade`` returns the schema to its prior
#: state exactly (the trigger is dropped first, so the restored grant does not
#: reintroduce a mutation path while the migration is still applied).
GRANT_BACK_TO_APP_ROLE = """
DO $$
DECLARE
    app_role text := current_setting('nexusops.migration.role', true);
BEGIN
    IF app_role IS NULL OR app_role = '' THEN
        RETURN;
    END IF;
    EXECUTE 'GRANT UPDATE, DELETE ON secret_versions TO ' || quote_ident(app_role);
END $$;
"""


def _set_app_role_in_guc() -> None:
    """Publish the app-role name to the migration GUC the revoke block reads."""
    from app.core.config import get_settings

    settings = get_settings()
    op.execute(
        sa.text("SELECT set_config('nexusops.migration.role', :role, false)").bindparams(
            role=settings.postgres_app_user
        )
    )


def _clear_app_role_guc() -> None:
    op.execute(sa.text("SELECT set_config('nexusops.migration.role', '', false)"))


def upgrade() -> None:
    op.execute(SECRET_VERSION_GUARD)
    op.execute(
        "CREATE TRIGGER secret_versions_no_mutation "
        "BEFORE UPDATE OR DELETE ON secret_versions "
        "FOR EACH ROW EXECUTE FUNCTION nexusops_block_secret_version_mutation()"
    )
    _set_app_role_in_guc()
    op.execute(REVOKE_FROM_APP_ROLE)
    _clear_app_role_guc()


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS secret_versions_no_mutation ON secret_versions")
    op.execute(SECRET_VERSION_GUARD_DROP)
    _set_app_role_in_guc()
    op.execute(GRANT_BACK_TO_APP_ROLE)
    _clear_app_role_guc()
