"""Add the operations framework table (node-agent-architecture.md §5).

One tenant-owned table holding the compare-and-set work queue the node agent
pulls from. It carries ``org_id`` like every other organization-owned table, so
it gets the same two policies the tenancy migration installed elsewhere: a tenant
policy that both filters (``USING``) and validates writes (``WITH CHECK``), and a
system policy for the cross-tenant expiry sweep.

The app role is granted on the table here because the blanket ``GRANT ... ON ALL
TABLES`` in the tenancy migration ran before this table existed. The
``ALTER DEFAULT PRIVILEGES`` set there would probably cover it, but relying on
that across two migrations is the kind of implicit coupling that breaks a
restored database, so the grant is explicit and idempotent.

Revision ID: e7c4a2b9d1f3
Revises: c4e2a1f7b9d3
Created: 2026-10-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "e7c4a2b9d1f3"
down_revision: str | None = "c4e2a1f7b9d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Reserved GUC value meaning "no tenant filter". Mirrors
#: ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated so the migration stays
#: reproducible if the constant moves.
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

#: The whitelist, spelled out here as a literal so this migration keeps enforcing
#: the set that shipped even if the enum later grows — a new type is a new
#: migration, which is exactly the review gate the architecture asks for.
_OPERATION_TYPES = (
    "container.start",
    "container.stop",
    "container.restart",
    "container.remove",
    "logs.tail",
)

_OPERATION_STATUSES = (
    "PENDING",
    "CLAIMED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "EXPIRED",
    "CANCELLED",
)


def _quoted_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


GRANT_TO_APP_ROLE = """
DO $$
DECLARE
    app_role text := current_setting('nexusops.migration.role', true);
BEGIN
    IF app_role IS NULL OR app_role = '' THEN
        RAISE NOTICE 'nexusops: POSTGRES_APP_USER is empty; skipping operations grant';
        RETURN;
    END IF;
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON operations TO ' || quote_ident(app_role);
END $$;
"""


def upgrade() -> None:
    op.create_table(
        "operations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id", ondelete="CASCADE", name="fk_operations_org_id_organizations"
            ),
            nullable=False,
        ),
        sa.Column(
            "node_id",
            sa.Uuid(),
            sa.ForeignKey("servers.id", ondelete="CASCADE", name="fk_operations_node_id_servers"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("params", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "requested_by_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="SET NULL", name="fk_operations_requested_by_id_users"
            ),
            nullable=True,
        ),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
        # ``op.f`` marks these as final names. Without it the naming convention
        # (``ck_%(table_name)s_%(constraint_name)s``) prefixes the already-final
        # name again and the database ends up with
        # ``ck_operations_ck_operations_status_valid`` — a name the model's
        # ``status_check`` never produces, which shows up as model/migration
        # drift (and would make every future autogenerate noisy).
        sa.CheckConstraint(
            f"status IN ({_quoted_list(_OPERATION_STATUSES)})",
            name=op.f("ck_operations_status_valid"),
        ),
        sa.CheckConstraint(
            f"type IN ({_quoted_list(_OPERATION_TYPES)})",
            name=op.f("ck_operations_type_valid"),
        ),
    )
    op.create_index("ix_operations_org_id", "operations", ["org_id"])
    op.create_index("ix_operations_node_id", "operations", ["node_id"])
    op.create_index("ix_operations_status", "operations", ["status"])
    op.create_index("ix_operations_created_at", "operations", ["created_at"])
    op.create_index("ix_operations_node_status", "operations", ["node_id", "status"])
    op.create_index("ix_operations_expires_at", "operations", ["expires_at"])

    # --- row-level security -------------------------------------------------
    # `app_current_org()` was created by the tenancy migration and resolves the
    # GUC to a UUID or NULL, so a malformed/empty value denies rather than raises.
    op.execute("ALTER TABLE operations ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY operations_tenant ON operations AS PERMISSIVE FOR ALL TO PUBLIC
        USING (org_id = app_current_org())
        WITH CHECK (org_id = app_current_org())
        """
    )
    op.execute(
        f"""
        CREATE POLICY operations_system ON operations AS PERMISSIVE FOR ALL TO PUBLIC
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
    op.execute("DROP POLICY IF EXISTS operations_tenant ON operations")
    op.execute("DROP POLICY IF EXISTS operations_system ON operations")
    op.execute("ALTER TABLE operations DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_operations_expires_at", table_name="operations")
    op.drop_index("ix_operations_node_status", table_name="operations")
    op.drop_index("ix_operations_created_at", table_name="operations")
    op.drop_index("ix_operations_status", table_name="operations")
    op.drop_index("ix_operations_node_id", table_name="operations")
    op.drop_index("ix_operations_org_id", table_name="operations")
    op.drop_table("operations")
