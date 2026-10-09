"""Phase 3 — Nodes & Agent v2 schema.

Adds, in one migration with a single head:

* ``enrollment_tokens`` — the organization-scoped, single-use, expiring,
  revocable ``nxk_`` credential an operator hands to a not-yet-enrolled machine.
  Tenant-owned, so it carries the same two RLS policies as every other tenant
  table, plus an explicit app-role grant.
* ``servers.capabilities`` (JSONB, default ``{}``), ``servers.protocol_version``
  and ``servers.credential_revoked_at`` — the capability gate and the negotiated
  protocol version. An empty ``capabilities`` map means *unreported*, never
  "has everything"; the default is therefore ``{}`` and dispatch treats it as
  unverified.
* ``agent_credentials`` rotation-grace columns — the previous hash accepted for
  a bounded window and the encrypted pending token delivered on the agent's next
  authenticated heartbeat. Only hashes/ciphertext are stored; no raw token.
* ``operations.available_until`` / ``operations.execution_deadline`` — the
  separate queue, execution and result-reporting deadlines that replace the
  single ``expires_at`` guess (docs/node-agent-architecture.md §7).
* ``docker_hosts`` uniqueness on ``server_id`` — exactly one docker connection
  per node, so the agent's auto-create cannot race into two rows.

No credential material is written by this migration: existing rotated/revoked
state is left exactly as it was.

Revision ID: a1b2c3d4e5f6
Revises: e5f6a7b8c9d0
Created: 2026-10-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Mirrors ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated so the migration
#: stays reproducible if the constant moves.
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

def _grant(table: str) -> None:
    """Grant the app role on *table*; the migration role GUC carries the name.

    The tenancy migration's blanket ``GRANT ... ON ALL TABLES`` ran before this
    table existed, so the grant is repeated here rather than relying on
    ``ALTER DEFAULT PRIVILEGES`` across migrations.
    """
    op.execute(
        f"""
        DO $$
        DECLARE
            app_role text := current_setting('nexusops.migration.role', true);
        BEGIN
            IF app_role IS NULL OR app_role = '' THEN
                RAISE NOTICE 'nexusops: POSTGRES_APP_USER is empty; skipping {table} grant';
                RETURN;
            END IF;
            EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO ' || quote_ident(app_role);
        END $$;
        """
    )


def upgrade() -> None:
    # --- 1. enrollment_tokens ------------------------------------------------
    op.create_table(
        "enrollment_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
                name="fk_enrollment_tokens_org_id_organizations",
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("single_use", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_id", sa.Uuid(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_by_node_id", sa.Uuid(), nullable=True),
        sa.Column("node_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["revoked_by_id"],
            ["users.id"],
            name="fk_enrollment_tokens_revoked_by_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["used_by_node_id"],
            ["servers.id"],
            name="fk_enrollment_tokens_used_by_node_id_servers",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["node_id"],
            ["servers.id"],
            name="fk_enrollment_tokens_node_id_servers",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name="fk_enrollment_tokens_created_by_id_users",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("token_hash", name="uq_enrollment_tokens_token_hash"),
    )
    op.create_index("ix_enrollment_tokens_org_id", "enrollment_tokens", ["org_id"])
    op.create_index("ix_enrollment_tokens_created_at", "enrollment_tokens", ["created_at"])

    op.execute("ALTER TABLE enrollment_tokens ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY enrollment_tokens_tenant ON enrollment_tokens AS PERMISSIVE FOR ALL TO PUBLIC
        USING (org_id = app_current_org())
        WITH CHECK (org_id = app_current_org())
        """
    )
    op.execute(
        f"""
        CREATE POLICY enrollment_tokens_system ON enrollment_tokens AS PERMISSIVE FOR ALL TO PUBLIC
        USING (current_setting('app.current_org', true) = '{SYSTEM_ORG_SENTINEL}')
        WITH CHECK (current_setting('app.current_org', true) = '{SYSTEM_ORG_SENTINEL}')
        """
    )

    # --- 2. servers: capabilities, protocol version, credential revocation ---
    op.add_column("servers", sa.Column("protocol_version", sa.Integer(), nullable=True))
    op.add_column(
        "servers", sa.Column("credential_revoked_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("servers", sa.Column("capabilities", JSONB, nullable=True))
    # Existing nodes have not reported capabilities. ``{}`` is the honest value:
    # unreported, and dispatch refuses until hello v2 populates it.
    op.execute("UPDATE servers SET capabilities = '{}'::jsonb WHERE capabilities IS NULL")
    op.alter_column("servers", "capabilities", existing_type=JSONB, nullable=False)

    # --- 3. agent_credentials: rotation grace --------------------------------
    op.add_column(
        "agent_credentials", sa.Column("previous_token_hash", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "agent_credentials",
        sa.Column("previous_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "agent_credentials", sa.Column("pending_token_ciphertext", sa.Text(), nullable=True)
    )
    op.add_column(
        "agent_credentials",
        sa.Column("rotation_applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_agent_credentials_previous_token_hash",
        "agent_credentials",
        ["previous_token_hash"],
    )

    # --- 4. operations: separate queue / execution / result deadlines --------
    op.add_column("operations", sa.Column("available_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "operations", sa.Column("execution_deadline", sa.DateTime(timezone=True), nullable=True)
    )
    # Existing rows predate the split: their single deadline was the best available
    # approximation of the queue deadline, so it is carried across. Nothing is
    # silently extended — the value is the row's original expires_at.
    op.execute("UPDATE operations SET available_until = expires_at WHERE available_until IS NULL")
    op.alter_column("operations", "available_until", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.create_index("ix_operations_available_until", "operations", ["available_until"])

    # --- 5. one docker connection per node -----------------------------------
    op.create_unique_constraint("uq_docker_hosts_server_id", "docker_hosts", ["server_id"])

    # --- 6. app-role grant for the new table ---------------------------------
    from app.core.config import get_settings

    settings = get_settings()
    op.execute(
        sa.text("SELECT set_config('nexusops.migration.role', :role, false)").bindparams(
            role=settings.postgres_app_user
        )
    )
    _grant("enrollment_tokens")
    op.execute(sa.text("SELECT set_config('nexusops.migration.role', '', false)"))


def downgrade() -> None:
    op.drop_constraint("uq_docker_hosts_server_id", "docker_hosts", type_="unique")

    op.drop_index("ix_operations_available_until", table_name="operations")
    op.drop_column("operations", "execution_deadline")
    op.drop_column("operations", "available_until")

    op.drop_constraint(
        "uq_agent_credentials_previous_token_hash", "agent_credentials", type_="unique"
    )
    op.drop_column("agent_credentials", "rotation_applied_at")
    op.drop_column("agent_credentials", "pending_token_ciphertext")
    op.drop_column("agent_credentials", "previous_expires_at")
    op.drop_column("agent_credentials", "previous_token_hash")

    op.drop_column("servers", "capabilities")
    op.drop_column("servers", "credential_revoked_at")
    op.drop_column("servers", "protocol_version")

    op.execute("DROP POLICY IF EXISTS enrollment_tokens_system ON enrollment_tokens")
    op.execute("DROP POLICY IF EXISTS enrollment_tokens_tenant ON enrollment_tokens")
    op.execute("ALTER TABLE enrollment_tokens DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_enrollment_tokens_created_at", table_name="enrollment_tokens")
    op.drop_index("ix_enrollment_tokens_org_id", table_name="enrollment_tokens")
    op.drop_table("enrollment_tokens")
