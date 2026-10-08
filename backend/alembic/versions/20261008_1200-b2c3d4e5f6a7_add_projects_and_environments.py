"""Phase 2 — projects & environments: env promotion, config, secret versions.

This is a **data** migration as much as a schema one. Three things happen:

1. ``deployment_environments`` moves from application scope to **project scope**
   (``application_id`` → ``project_id``). Every existing row's project is derived
   through ``application_id → applications.project_id``, so no environment is
   orphaned and no deployment loses its target.
2. Environments that collide once the application dimension is removed — e.g.
   ``API.production`` and ``Worker.production`` in the same project — are
   **merged** deterministically: the earliest-created row (tie-broken by id)
   survives, every deployment of a duplicate is re-pointed at the survivor
   *before* the duplicate is deleted (so the ``ON DELETE CASCADE`` on
   ``deployments.environment_id`` never fires), and no scalar field is lost
   (empty survivor fields are filled from the duplicate, ``auto_deploy`` is
   OR-ed, and config keys are unioned with the survivor winning on a clash).
3. ``secrets`` gains the environment scope level and a new append-only
   ``secret_versions`` table records every value a secret has ever held.

``secret_versions`` carries ``org_id`` like every other tenant table, so it gets
the same tenant + system policies and the same app-role grant as ``operations``.

Revision ID: b2c3d4e5f6a7
Revises: f1a2b3c4d5e6
Created: 2026-10-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Reserved GUC value meaning "no tenant filter". Mirrors
#: ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated so the migration stays
#: reproducible if the constant moves.
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

#: The environment kinds this migration will accept. Spelled as a literal on
#: purpose: a new kind is a new, reviewable migration (same rule as the
#: operations whitelist).
_ENVIRONMENT_TYPES = ("DEV", "STAGING", "PROD")


def _quoted_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


#: Deterministic duplicate resolution. A group is ``(org_id, project_id, slug)``
#: with more than one row — the same environment defined by two applications of
#: one project. The survivor is the earliest ``created_at`` (``id`` breaks ties)
#: so re-running the migration on the same data always picks the same row.
MERGE_DUPLICATE_ENVIRONMENTS = """
DO $$
DECLARE
    grp record;
    survivor uuid;
    dup_ids uuid[];
    dup_id uuid;
    dup_row deployment_environments%ROWTYPE;
BEGIN
    FOR grp IN
        SELECT org_id, project_id, slug
          FROM deployment_environments
         WHERE project_id IS NOT NULL
         GROUP BY org_id, project_id, slug
        HAVING count(*) > 1
    LOOP
        SELECT id INTO survivor
          FROM deployment_environments
         WHERE org_id = grp.org_id AND project_id = grp.project_id AND slug = grp.slug
         ORDER BY created_at ASC, id ASC
         LIMIT 1;

        SELECT array_agg(id) INTO dup_ids
          FROM deployment_environments
         WHERE org_id = grp.org_id AND project_id = grp.project_id AND slug = grp.slug
           AND id <> survivor;

        FOREACH dup_id IN ARRAY dup_ids LOOP
            SELECT * INTO dup_row FROM deployment_environments WHERE id = dup_id;

            -- Re-point before deleting, or the FK's ON DELETE CASCADE would take
            -- the deployments with it.
            UPDATE deployments SET environment_id = survivor WHERE environment_id = dup_id;

            UPDATE deployment_environments s
               SET server_id = COALESCE(s.server_id, dup_row.server_id),
                   healthcheck_path = CASE
                       WHEN s.healthcheck_path = '' THEN dup_row.healthcheck_path
                       ELSE s.healthcheck_path
                   END,
                   auto_deploy = s.auto_deploy OR dup_row.auto_deploy,
                   -- JSONB ``||``: duplicate keys are kept, the survivor wins on
                   -- a clash. Union, never a silent loss.
                   config = dup_row.config || s.config,
                   updated_at = now()
             WHERE s.id = survivor;

            DELETE FROM deployment_environments WHERE id = dup_id;
        END LOOP;
    END LOOP;
END $$;
"""

#: Seed one version row per pre-existing secret from its current value, so the
#: append-only history starts complete rather than empty. Historical values did
#: not exist before this migration (rotation overwrote in place) and cannot be
#: invented; the current value is version ``secrets.version``.
BACKFILL_SECRET_VERSIONS = """
INSERT INTO secret_versions (
    id, org_id, secret_id, version, ciphertext, digest, created_by_id, created_at, updated_at
)
SELECT gen_random_uuid(), s.org_id, s.id, s.version, s.ciphertext, s.digest,
       s.created_by_id, s.created_at, s.created_at
  FROM secrets s
 WHERE NOT EXISTS (
     SELECT 1 FROM secret_versions v
      WHERE v.secret_id = s.id AND v.version = s.version
 );
"""

GRANT_TO_APP_ROLE = """
DO $$
DECLARE
    app_role text := current_setting('nexusops.migration.role', true);
BEGIN
    IF app_role IS NULL OR app_role = '' THEN
        RAISE NOTICE 'nexusops: POSTGRES_APP_USER is empty; skipping secret_versions grant';
        RETURN;
    END IF;
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON secret_versions TO ' || quote_ident(app_role);
END $$;
"""


def _drop_constraint(table: str, name: str) -> None:
    op.execute(
        sa.text(
            "ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}".format(
                table=table, name=name
            )
        )
    )


def upgrade() -> None:
    # --- 1. projects.config -------------------------------------------------
    # The base layer of config layering (domain-model.md §2.2.1). Structured
    # data only; a server default lets existing rows take the empty object
    # without a second pass.
    op.add_column(
        "projects",
        sa.Column("config", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    # --- 2. Promote environments to project scope ---------------------------
    op.add_column("deployment_environments", sa.Column("project_id", sa.Uuid(), nullable=True))
    op.add_column(
        "deployment_environments",
        sa.Column("environment_type", sa.String(length=16), nullable=False, server_default="DEV"),
    )

    # Every environment has an application (NOT NULL, ON DELETE CASCADE), so the
    # project is always derivable — this is a move, not a guess.
    op.execute(
        sa.text(
            "UPDATE deployment_environments e SET project_id = a.project_id "
            "FROM applications a WHERE a.id = e.application_id"
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM deployment_environments WHERE project_id IS NULL) THEN
                    RAISE EXCEPTION
                        'cannot promote deployment_environments: rows exist with no '
                        'derivable project (application missing). Restore the applications '
                        'table before re-running.';
                END IF;
            END $$;
            """
        )
    )

    # Merge same-slug environments within a project *before* the unique
    # constraint and before the old application link disappears.
    op.execute(MERGE_DUPLICATE_ENVIRONMENTS)

    # --- 3. Swap the link, constraints and indexes --------------------------
    _drop_constraint("deployment_environments", "uq_envs_application_name")
    _drop_constraint(
        "deployment_environments", "fk_deployment_environments_application_id_applications"
    )
    op.drop_index("ix_deployment_environments_application_id", table_name="deployment_environments")
    op.drop_column("deployment_environments", "application_id")

    op.alter_column("deployment_environments", "project_id", nullable=False)
    op.create_foreign_key(
        "fk_deployment_environments_project_id_projects",
        "deployment_environments",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_deployment_environments_project_id", "deployment_environments", ["project_id"]
    )
    op.create_index(
        "ix_deployment_environments_environment_type",
        "deployment_environments",
        ["environment_type"],
    )
    op.create_unique_constraint(
        "uq_envs_project_slug", "deployment_environments", ["project_id", "slug"]
    )
    op.create_check_constraint(
        op.f("ck_deployment_environments_environment_type_valid"),
        "deployment_environments",
        f"environment_type IN ({_quoted_list(_ENVIRONMENT_TYPES)})",
    )
    op.execute(
        sa.text(
            "ALTER TABLE deployment_environments ALTER COLUMN environment_type DROP DEFAULT"
        )
    )

    # --- 4. secrets: environment scope --------------------------------------
    op.add_column("secrets", sa.Column("environment_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_secrets_environment_id_deployment_environments",
        "secrets",
        "deployment_environments",
        ["environment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_secrets_environment_id", "secrets", ["environment_id"])

    # Replace the two-level uniqueness with one partial index per scope level
    # (NULLs are distinct in a plain UNIQUE, so each level needs its own index).
    _drop_constraint("secrets", "uq_secrets_org_project_key")
    op.drop_index("ux_secrets_org_global_key", table_name="secrets")
    op.create_index(
        "ux_secrets_org_scope_key",
        "secrets",
        ["org_id", "key"],
        unique=True,
        postgresql_where=sa.text("project_id IS NULL"),
    )
    op.create_index(
        "ux_secrets_project_scope_key",
        "secrets",
        ["org_id", "project_id", "key"],
        unique=True,
        postgresql_where=sa.text("project_id IS NOT NULL AND environment_id IS NULL"),
    )
    op.create_index(
        "ux_secrets_environment_scope_key",
        "secrets",
        ["org_id", "environment_id", "key"],
        unique=True,
        postgresql_where=sa.text("environment_id IS NOT NULL"),
    )
    op.create_check_constraint(
        op.f("ck_secrets_environment_requires_project"),
        "secrets",
        "project_id IS NOT NULL OR environment_id IS NULL",
    )

    # --- 5. secret_versions (append-only history) ---------------------------
    op.create_table(
        "secret_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
                name="fk_secret_versions_org_id_organizations",
            ),
            nullable=False,
        ),
        sa.Column(
            "secret_id",
            sa.Uuid(),
            sa.ForeignKey(
                "secrets.id", ondelete="CASCADE", name="fk_secret_versions_secret_id_secrets"
            ),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("digest", sa.String(length=16), nullable=False, server_default=""),
        sa.Column(
            "created_by_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="SET NULL", name="fk_secret_versions_created_by_id_users"
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "secret_id", "version", name="uq_secret_versions_secret_version"
        ),
    )
    op.create_index("ix_secret_versions_org_id", "secret_versions", ["org_id"])
    op.create_index("ix_secret_versions_secret_id", "secret_versions", ["secret_id"])
    op.create_index("ix_secret_versions_created_at", "secret_versions", ["created_at"])

    op.execute(BACKFILL_SECRET_VERSIONS)

    # --- 6. Row-level security + app-role grant -----------------------------
    op.execute("ALTER TABLE secret_versions ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY secret_versions_tenant ON secret_versions AS PERMISSIVE FOR ALL TO PUBLIC
        USING (org_id = app_current_org())
        WITH CHECK (org_id = app_current_org())
        """
    )
    op.execute(
        f"""
        CREATE POLICY secret_versions_system ON secret_versions AS PERMISSIVE FOR ALL TO PUBLIC
        USING (current_setting('app.current_org', true) = '{SYSTEM_ORG_SENTINEL}')
        WITH CHECK (current_setting('app.current_org', true) = '{SYSTEM_ORG_SENTINEL}')
        """
    )

    from app.core.config import get_settings

    settings = get_settings()
    op.execute(
        sa.text("SELECT set_config('nexusops.migration.role', :role, false)").bindparams(
            role=settings.postgres_app_user
        )
    )
    op.execute(GRANT_TO_APP_ROLE)
    op.execute(sa.text("SELECT set_config('nexusops.migration.role', '', false)"))


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS secret_versions_tenant ON secret_versions")
    op.execute("DROP POLICY IF EXISTS secret_versions_system ON secret_versions")
    op.execute("ALTER TABLE secret_versions DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_secret_versions_created_at", table_name="secret_versions")
    op.drop_index("ix_secret_versions_secret_id", table_name="secret_versions")
    op.drop_index("ix_secret_versions_org_id", table_name="secret_versions")
    op.drop_table("secret_versions")

    _drop_constraint("secrets", "ck_secrets_environment_requires_project")
    op.drop_index("ux_secrets_environment_scope_key", table_name="secrets")
    op.drop_index("ux_secrets_project_scope_key", table_name="secrets")
    op.drop_index("ux_secrets_org_scope_key", table_name="secrets")
    op.create_index(
        "ux_secrets_org_global_key",
        "secrets",
        ["org_id", "key"],
        unique=True,
        postgresql_where=sa.text("project_id IS NULL"),
    )
    op.create_unique_constraint(
        "uq_secrets_org_project_key", "secrets", ["org_id", "project_id", "key"]
    )
    op.drop_index("ix_secrets_environment_id", table_name="secrets")
    op.drop_constraint(
        "fk_secrets_environment_id_deployment_environments", "secrets", type_="foreignkey"
    )
    op.drop_column("secrets", "environment_id")

    _drop_constraint("deployment_environments", "ck_deployment_environments_environment_type_valid")
    _drop_constraint("deployment_environments", "uq_envs_project_slug")
    op.drop_index("ix_deployment_environments_environment_type", table_name="deployment_environments")
    op.drop_index("ix_deployment_environments_project_id", table_name="deployment_environments")
    op.drop_constraint(
        "fk_deployment_environments_project_id_projects",
        "deployment_environments",
        type_="foreignkey",
    )
    op.add_column(
        "deployment_environments", sa.Column("application_id", sa.Uuid(), nullable=True)
    )
    # Best-effort reverse mapping: an environment returns to the first
    # application of its project. Environments merged during the upgrade cannot
    # be split apart again — the migration is one-way for a merge, which the
    # Phase 2 report states.
    op.execute(
        sa.text(
            """
            UPDATE deployment_environments e SET application_id = (
                SELECT a.id FROM applications a
                 WHERE a.project_id = e.project_id
                 ORDER BY a.name, a.id LIMIT 1
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM deployment_environments WHERE application_id IS NULL) THEN
                    RAISE EXCEPTION
                        'cannot downgrade: a surviving environment has no application to '
                        'return to (its project has no applications)';
                END IF;
            END $$;
            """
        )
    )
    op.alter_column("deployment_environments", "application_id", nullable=False)
    op.create_foreign_key(
        "fk_deployment_environments_application_id_applications",
        "deployment_environments",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_deployment_environments_application_id", "deployment_environments", ["application_id"]
    )
    op.create_unique_constraint(
        "uq_envs_application_name", "deployment_environments", ["application_id", "name"]
    )
    op.drop_column("deployment_environments", "environment_type")
    op.drop_column("deployment_environments", "project_id")

    op.drop_column("projects", "config")
