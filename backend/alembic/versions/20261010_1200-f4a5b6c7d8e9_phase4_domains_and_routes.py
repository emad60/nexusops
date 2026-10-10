"""Phase 4 — domains, routes and the routing schema.

Adds, in one migration with a single head:

* ``domains`` — organization-owned DNS names with their verification lifecycle.
  Tenant-owned, so it carries the same two RLS policies as every other tenant
  table plus an explicit app-role grant. The **partial unique index on
  ``lower(name)`` where the row is verified** is the platform-wide
  one-verified-owner rule; it is what makes anti-takeover a database fact.
* ``routes`` — one hostname+path served from one container on one node. HTTP
  only: ``scheme = 'http'`` is a CHECK constraint, and there is no
  ``certificate_id`` column until Phase 5 adds one by migration. The partial
  unique index on ``(node_id, hostname, path) WHERE enabled`` is the
  one-nginx-one-answer rule.
* ``monitors.target_type`` / ``monitors.route_id`` — the polymorphic target model.
  Every existing row is backfilled to ``URL`` by the column default, so monitor
  IDs, ownership, check history, incidents and notification associations are all
  untouched.
* ``servers.proxy_state`` — the bounded last-known proxy state (live bundle
  fingerprint, last apply outcome). Never configuration text.
* ``operations.type`` — the closed whitelist gains exactly the three ``nginx.*``
  types Phase 4 approves, by recreating the CHECK constraint. No other value is
  added and nothing is removed.

Nothing in this migration modifies existing data beyond the monitor backfill and
the constraint widening: nodes, capabilities, credentials, secrets, deployments
and operation history are left exactly as they were.

Revision ID: f4a5b6c7d8e9
Revises: a1b2c3d4e5f6
Created: 2026-10-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "f4a5b6c7d8e9"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Mirrors ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated so the migration
#: stays reproducible if the constant moves.
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

#: The operation whitelist after Phase 4. Kept as literals so the constraint is
#: reproducible even if an enum member is renamed later.
OPERATION_TYPES_BEFORE = ("container.start", "container.stop", "container.restart", "container.remove", "logs.tail")
OPERATION_TYPES_AFTER = OPERATION_TYPES_BEFORE + ("nginx.bootstrap", "nginx.apply", "nginx.status")

DOMAIN_STATUSES = ("PENDING", "VERIFYING", "VERIFIED", "STALE", "UNVERIFIED", "FAILED")
ROUTE_CONFIG_STATES = ("PENDING", "IN_SYNC", "STALE", "FAILED")

NEW_TENANT_TABLES = ("domains", "routes")


def _in_list(column: str, values: Sequence[str]) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def _grant(table: str) -> None:
    """Grant the app role on *table*; the migration role GUC carries the name.

    The tenancy migration's blanket ``GRANT ... ON ALL TABLES`` ran before these
    tables existed, so the grant is repeated here rather than relying on
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


def _tenant_policies(table: str) -> None:
    """The two-policy shape every tenant table uses: tenant + system scope."""
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY {table}_tenant ON {table} AS PERMISSIVE FOR ALL TO PUBLIC
        USING (org_id = app_current_org())
        WITH CHECK (org_id = app_current_org())
        """
    )
    op.execute(
        f"""
        CREATE POLICY {table}_system ON {table} AS PERMISSIVE FOR ALL TO PUBLIC
        USING (current_setting('app.current_org', true) = '{SYSTEM_ORG_SENTINEL}')
        WITH CHECK (current_setting('app.current_org', true) = '{SYSTEM_ORG_SENTINEL}')
        """
    )


def _drop_tenant_policies(table: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {table}_system ON {table}")
    op.execute(f"DROP POLICY IF EXISTS {table}_tenant ON {table}")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def upgrade() -> None:
    # --- 1. domains ----------------------------------------------------------
    op.create_table(
        "domains",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id", ondelete="CASCADE", name="fk_domains_org_id_organizations"
            ),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="SET NULL", name="fk_domains_project_id_projects"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=253), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column("verification_token", sa.String(length=96), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ns_snapshot", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proof_lost_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stale_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("dns_reachability", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_in_list("status", DOMAIN_STATUSES), name="status_valid"),
        sa.CheckConstraint("char_length(name) BETWEEN 4 AND 253", name="name_length"),
        sa.CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
        sa.UniqueConstraint("org_id", "name", name="uq_domains_org_id_name"),
    )
    op.create_index("ix_domains_org_id", "domains", ["org_id"])
    op.create_index("ix_domains_project_id", "domains", ["project_id"])
    op.create_index("ix_domains_status", "domains", ["status"])
    op.create_index("ix_domains_created_at", "domains", ["created_at"])
    op.create_index("ix_domains_org_status", "domains", ["org_id", "status"])
    op.create_index("ix_domains_verification_sweep", "domains", ["status", "next_check_at"])
    # Platform-wide ownership: at most one VERIFIED row per name, whatever the
    # organization. Any number of organizations may *track* a name.
    op.create_index(
        "uq_domains_verified_name",
        "domains",
        [sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("status = 'VERIFIED'"),
    )
    _tenant_policies("domains")

    # --- 2. routes -----------------------------------------------------------
    op.create_table(
        "routes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id", ondelete="CASCADE", name="fk_routes_org_id_organizations"
            ),
            nullable=False,
        ),
        sa.Column(
            "domain_id",
            sa.Uuid(),
            sa.ForeignKey("domains.id", ondelete="CASCADE", name="fk_routes_domain_id_domains"),
            nullable=False,
        ),
        sa.Column("hostname", sa.String(length=253), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False, server_default="/"),
        sa.Column(
            "node_id",
            sa.Uuid(),
            sa.ForeignKey("servers.id", ondelete="CASCADE", name="fk_routes_node_id_servers"),
            nullable=False,
        ),
        sa.Column(
            "container_id",
            sa.Uuid(),
            sa.ForeignKey(
                "containers.id", ondelete="SET NULL", name="fk_routes_container_id_containers"
            ),
            nullable=True,
        ),
        sa.Column("port", sa.Integer(), nullable=False),
        # Phase 4 serves HTTP only. Phase 5 widens this by its own migration.
        sa.Column("scheme", sa.String(length=8), nullable=False, server_default="http"),
        sa.Column("headers", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rate_limit", JSONB, nullable=True),
        sa.Column("redirect", JSONB, nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("config_state", sa.String(length=16), nullable=False, server_default="PENDING"),
        sa.Column(
            "monitor_id",
            sa.Uuid(),
            sa.ForeignKey("monitors.id", ondelete="SET NULL", name="fk_routes_monitor_id_monitors"),
            nullable=True,
        ),
        sa.Column("monitor_optout", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_bundle_id", sa.String(length=64), nullable=True),
        sa.Column("last_apply_error", sa.String(length=500), nullable=False, server_default=""),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_in_list("config_state", ROUTE_CONFIG_STATES), name="config_state_valid"),
        sa.CheckConstraint("scheme = 'http'", name="scheme_http_only"),
        sa.CheckConstraint("port BETWEEN 1 AND 65535", name="port_range"),
        sa.CheckConstraint("path LIKE '/%'", name="path_absolute"),
        sa.CheckConstraint("char_length(path) <= 255", name="path_length"),
        sa.CheckConstraint("char_length(hostname) BETWEEN 4 AND 253", name="hostname_length"),
    )
    op.create_index("ix_routes_org_id", "routes", ["org_id"])
    op.create_index("ix_routes_created_at", "routes", ["created_at"])
    op.create_index("ix_routes_domain", "routes", ["domain_id"])
    op.create_index("ix_routes_node_id", "routes", ["node_id"])
    op.create_index("ix_routes_container_id", "routes", ["container_id"])
    op.create_index("ix_routes_org_state", "routes", ["org_id", "config_state"])
    op.create_index(
        "uq_routes_node_host_path",
        "routes",
        ["node_id", "hostname", "path"],
        unique=True,
        postgresql_where=sa.text("enabled"),
    )
    _tenant_policies("routes")

    # --- 3. monitors: polymorphic targets ------------------------------------
    op.add_column(
        "monitors",
        sa.Column("target_type", sa.String(length=8), nullable=False, server_default="URL"),
    )
    op.add_column(
        "monitors",
        sa.Column(
            "route_id",
            sa.Uuid(),
            sa.ForeignKey("routes.id", ondelete="CASCADE", name="fk_monitors_route_id_routes"),
            nullable=True,
        ),
    )
    op.create_index("ix_monitors_route_id", "monitors", ["route_id"])
    # Existing rows are URL targets by definition: the server default backfilled
    # them and ``route_id`` is NULL, which the shape constraint below requires.
    op.create_check_constraint("target_type_valid", "monitors", _in_list("target_type", ("URL", "ROUTE")))
    op.create_check_constraint(
        "target_shape", "monitors", "(target_type = 'ROUTE') = (route_id IS NOT NULL)"
    )

    # --- 4. servers: bounded proxy state -------------------------------------
    op.add_column("servers", sa.Column("proxy_state", JSONB, nullable=True))
    op.execute("UPDATE servers SET proxy_state = '{}'::jsonb WHERE proxy_state IS NULL")
    op.alter_column("servers", "proxy_state", existing_type=JSONB, nullable=False)

    # --- 5. operations: the closed whitelist gains the nginx family -----------
    # The naming convention expands a bare constraint name, so the *suffix* is
    # what identifies the constraint in both directions.
    op.drop_constraint("type_valid", "operations", type_="check")
    op.create_check_constraint("type_valid", "operations", _in_list("type", OPERATION_TYPES_AFTER))

    # --- 6. app-role grants for the new tables --------------------------------
    from app.core.config import get_settings

    settings = get_settings()
    op.execute(
        sa.text("SELECT set_config('nexusops.migration.role', :role, false)").bindparams(
            role=settings.postgres_app_user
        )
    )
    for table in NEW_TENANT_TABLES:
        _grant(table)
    op.execute(sa.text("SELECT set_config('nexusops.migration.role', '', false)"))


def downgrade() -> None:
    op.drop_constraint("type_valid", "operations", type_="check")
    op.create_check_constraint("type_valid", "operations", _in_list("type", OPERATION_TYPES_BEFORE))

    op.alter_column("servers", "proxy_state", existing_type=JSONB, nullable=True)
    op.drop_column("servers", "proxy_state")

    op.drop_constraint("target_shape", "monitors", type_="check")
    op.drop_constraint("target_type_valid", "monitors", type_="check")
    op.drop_index("ix_monitors_route_id", table_name="monitors")
    op.drop_column("monitors", "route_id")
    op.drop_column("monitors", "target_type")

    _drop_tenant_policies("routes")
    op.drop_index("uq_routes_node_host_path", table_name="routes")
    op.drop_index("ix_routes_org_state", table_name="routes")
    op.drop_index("ix_routes_container_id", table_name="routes")
    op.drop_index("ix_routes_node_id", table_name="routes")
    op.drop_index("ix_routes_domain", table_name="routes")
    op.drop_index("ix_routes_created_at", table_name="routes")
    op.drop_index("ix_routes_org_id", table_name="routes")
    op.drop_table("routes")

    _drop_tenant_policies("domains")
    op.drop_index("uq_domains_verified_name", table_name="domains")
    op.drop_index("ix_domains_verification_sweep", table_name="domains")
    op.drop_index("ix_domains_org_status", table_name="domains")
    op.drop_index("ix_domains_created_at", table_name="domains")
    op.drop_index("ix_domains_status", table_name="domains")
    op.drop_index("ix_domains_project_id", table_name="domains")
    op.drop_index("ix_domains_org_id", table_name="domains")
    op.drop_table("domains")
