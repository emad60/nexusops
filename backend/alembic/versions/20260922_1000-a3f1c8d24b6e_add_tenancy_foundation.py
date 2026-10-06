"""add tenancy foundation

Phase 1 of the platform roadmap: organizations, memberships, an ``org_id`` on
every tenant table, the PostgreSQL role split and row-level security.

Ordering within this migration matters and is not arbitrary:

1. ``organizations`` / ``memberships`` are created first because everything
   downstream references them.
2. The bootstrap organization is provisioned from the **oldest existing user**
   (named after them, flagged ``is_provisional``, never after the vendor) and
   every existing user is given a membership in it. On a clean database no
   organization is created at all — the first registration does that instead, so
   nothing is ever silently attached to an invented tenant.
3. ``org_id`` columns are added nullable, backfilled to the bootstrap
   organization, then set NOT NULL. A table with rows that somehow escaped the
   backfill fails loudly here rather than shipping orphan rows.
4. Uniqueness that used to be instance-wide (server/tag/project names, secret
   keys) becomes per-organization: two tenants both naming a server ``web-01``
   is normal, and the old constraints made org B's name an existence oracle for
   org A.
5. The agent token hash moves out of ``servers`` into ``agent_credentials``. The
   hash must be resolvable *before* an organization is known (auth has to
   identify the node first), and ``servers`` cannot both be RLS-enforced and
   readable pre-org. The routing table carries no tenant payload beyond
   ``(node, org)``, so it can stay outside RLS without weakening the boundary.
6. Roles and grants for the application role, then the policies themselves.

Revision ID: a3f1c8d24b6e
Revises: b3d7f9e2c6a4
Create Date: 2026-09-22 10:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a3f1c8d24b6e"
down_revision: str | None = "b3d7f9e2c6a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Reserved GUC value meaning "no tenant filter". Mirrors
#: ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated rather than imported so
#: the migration stays reproducible if the constant is ever moved.
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

#: Organization-owned tables (``OrgScoped`` models). Every one of these gets an
#: ``org_id`` column and a tenant + system policy pair.
ORG_SCOPED_TABLES: tuple[str, ...] = (
    "alerts",
    "applications",
    "audit_logs",
    "container_images",
    "containers",
    "deployment_environments",
    "deployment_steps",
    "deployments",
    "docker_hosts",
    "incident_events",
    "incidents",
    "log_entries",
    "metric_snapshots",
    "monitor_checks",
    "monitors",
    "notification_channels",
    "notification_deliveries",
    "projects",
    "secrets",
    "server_credentials",
    "server_tags",
    "servers",
    "system_events",
    "tags",
)

#: Tables where a NULL ``org_id`` is meaningful: events that happened before any
#: organization was known (a failed login for an address with no account, or
#: instance bootstrap). Those rows are invisible under organization scope — the
#: ORM guard and the RLS policy both drop them — and readable only through a
#: system scope.
NULLABLE_ORG_TABLES: frozenset[str] = frozenset({"audit_logs", "system_events"})

#: Tables carrying an ``org_id`` that are deliberately **not** under RLS, because
#: they have to be readable before an organization is known. Kept in sync with
#: ``app.core.tenancy.RLS_EXEMPT_ORG_TABLES`` and asserted by the catalog test.
RLS_EXEMPT_TABLES: tuple[str, ...] = (
    "api_keys",
    "agent_credentials",
    "memberships",
    "organizations",
    "roles",
)

if set(ORG_SCOPED_TABLES) & set(RLS_EXEMPT_TABLES):
    raise RuntimeError("ORG_SCOPED_TABLES and RLS_EXEMPT_TABLES must be disjoint")


APP_CURRENT_ORG_FUNCTION = """
CREATE OR REPLACE FUNCTION app_current_org() RETURNS uuid
LANGUAGE sql STABLE PARALLEL SAFE AS $$
    SELECT CASE
        WHEN current_setting('app.current_org', true) ~ '^[0-9a-fA-F-]{36}$'
        THEN current_setting('app.current_org', true)::uuid
        ELSE NULL
    END
$$;
COMMENT ON FUNCTION app_current_org() IS
    'Active organization for this transaction, from the app.current_org GUC. '
    'Returns NULL for unset, empty, or non-uuid values (including the system '
    'sentinel), so the RLS policies fail closed instead of raising a cast error. '
    'Marked PARALLEL SAFE on the same grounds PostgreSQL marks current_setting '
    'parallel safe: parallel workers receive the session GUC state. If a worker '
    'ever did not, the value would be NULL and the policy would deny rows — the '
    'safe direction.';
"""


BOOTSTRAP_ORGANIZATION_SQL = """
DO $$
DECLARE
    first_user_id uuid;
    display_name text;
    new_org_id uuid;
    org_name text;
    org_slug text;
BEGIN
    -- Idempotence: never provision twice, and never touch a database that
    -- already has a deliberately created organization.
    IF EXISTS (SELECT 1 FROM organizations) THEN
        RAISE NOTICE 'nexusops: organizations already exist, skipping bootstrap';
        RETURN;
    END IF;

    SELECT u.id,
           COALESCE(NULLIF(btrim(u.full_name), ''), split_part(u.email, '@', 1))
      INTO first_user_id, display_name
      FROM users u
     ORDER BY u.created_at, u.id
     LIMIT 1;

    IF first_user_id IS NULL THEN
        -- Clean database: no tenant exists yet and none is invented here. The
        -- first registration creates and owns its organization instead.
        RETURN;
    END IF;

    new_org_id := gen_random_uuid();
    org_name := left(display_name || '''s Organization', 120);
    org_slug := btrim(lower(regexp_replace(display_name, '[^a-zA-Z0-9]+', '-', 'g')), '-');
    IF org_slug = '' THEN
        org_slug := 'organization';
    END IF;

    INSERT INTO organizations (
        id, name, slug, description, status, is_provisional, created_by_id,
        created_at, updated_at
    ) VALUES (
        new_org_id,
        org_name,
        left(org_slug, 140),
        'Auto-provisioned for data that pre-dates organizations. It is named '
        'after the first user of this instance and is expected to be renamed.',
        'ACTIVE',
        true,
        first_user_id,
        now(),
        now()
    );

    -- Every existing user joins the bootstrap organization with the role they
    -- already held, so the migration grants nobody new authority.
    INSERT INTO memberships (
        id, org_id, user_id, role_id, status, created_by_id, created_at, updated_at
    )
    SELECT gen_random_uuid(), new_org_id, u.id, u.role_id, 'ACTIVE', first_user_id, now(), now()
      FROM users u
    ON CONFLICT (org_id, user_id) DO NOTHING;

    RAISE NOTICE 'nexusops: provisioned a provisional organization for pre-existing data';
END $$;
"""

#: Creates/repairs the application role and grants it exactly the privileges it
#: needs. The password and role name arrive through session GUCs set with
#: parameterized statements, because utility statements such as CREATE ROLE
#: cannot take bind parameters directly.
APP_ROLE_SQL = """
DO $$
DECLARE
    app_role text := current_setting('nexusops.migration.role', true);
    app_pw   text := current_setting('nexusops.migration.password', true);
    role_exists boolean;
    q_role text;
BEGIN
    IF app_role IS NULL OR app_role = '' THEN
        RAISE NOTICE 'nexusops: POSTGRES_APP_USER is empty; no application role was created';
        RETURN;
    END IF;
    IF app_role = current_user THEN
        RAISE EXCEPTION
            'POSTGRES_APP_USER must differ from the migration/owner role: a table '
            'owner bypasses row-level security, so the policies would be inert';
    END IF;

    q_role := quote_ident(app_role);

    SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = app_role) INTO role_exists;
    IF role_exists THEN
        -- Repair a role that exists without LOGIN or with BYPASSRLS.
        EXECUTE 'ALTER ROLE ' || q_role
             || ' WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS';
    ELSE
        EXECUTE 'CREATE ROLE ' || q_role
             || ' WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS';
    END IF;

    IF app_pw IS NOT NULL AND app_pw <> '' THEN
        EXECUTE 'ALTER ROLE ' || q_role || ' WITH PASSWORD ' || quote_literal(app_pw);
    END IF;

    EXECUTE 'GRANT USAGE ON SCHEMA public TO ' || q_role;
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ' || q_role;
    EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ' || q_role;
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE '
         || 'ON TABLES TO ' || q_role;
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO '
         || q_role;
END $$;
"""

SERVER_TAGS_TRIGGER = """
CREATE OR REPLACE FUNCTION nexusops_server_tag_set_org() RETURNS trigger AS $$
BEGIN
    SELECT s.org_id INTO NEW.org_id FROM servers s WHERE s.id = NEW.server_id;
    IF NEW.org_id IS NULL THEN
        RAISE EXCEPTION 'server_tags.server_id % does not reference a visible server',
            NEW.server_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- SECURITY DEFINER so the value comes from the referenced server's own row and
-- can never be spoofed by the caller's scope: a cross-organization pair is then
-- rejected by the RLS WITH CHECK instead of being created. The function is owned
-- by the migration role and reads exactly one column of one table.
CREATE TRIGGER server_tags_set_org
BEFORE INSERT OR UPDATE ON server_tags
FOR EACH ROW EXECUTE FUNCTION nexusops_server_tag_set_org();
"""


def _drop_constraint(table: str, name: str) -> None:
    op.execute(sa.text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{name}"'))


def _set_guc(name: str, value: str) -> None:
    """Carry a value into a PL/pgSQL block.

    ``CREATE ROLE``/``ALTER ROLE`` are utility statements and cannot take bind
    parameters, so the application role name and password travel through session
    GUCs set with a parameterized statement and are quoted inside the block with
    ``quote_ident()``/``quote_literal()``. The password is cleared as soon as the
    block returns.
    """
    op.get_bind().execute(
        sa.text("SELECT set_config(:name, :value, false)"),
        {"name": name, "value": value},
    )


def upgrade() -> None:
    settings_role, settings_password = _app_role_credentials()

    # --- 1. Tenancy tables ---------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("is_provisional", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("renamed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED')", name=op.f("ck_organizations_status_valid")
        ),
        sa.CheckConstraint(
            f"id <> '{SYSTEM_ORG_SENTINEL}'::uuid",
            name=op.f("ck_organizations_id_not_system_sentinel"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_organizations_created_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("name", name=op.f("uq_organizations_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_organizations_slug")),
    )
    op.create_index(
        op.f("ix_organizations_created_at"), "organizations", ["created_at"], unique=False
    )

    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED')", name=op.f("ck_memberships_status_valid")
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_memberships_created_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_memberships_org_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_memberships_role_id_roles"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_memberships_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memberships")),
        sa.UniqueConstraint("org_id", "user_id", name="uq_memberships_org_user"),
    )
    op.create_index(op.f("ix_memberships_created_at"), "memberships", ["created_at"], unique=False)
    op.create_index(op.f("ix_memberships_org_id"), "memberships", ["org_id"], unique=False)
    op.create_index(op.f("ix_memberships_user_id"), "memberships", ["user_id"], unique=False)
    op.create_index(
        "ix_memberships_user_status", "memberships", ["user_id", "status"], unique=False
    )

    # Organizational column on the two pre-org identity tables that need one.
    # Both stay outside RLS: their rows have to be findable before an
    # organization is known (``api_keys.org_id`` *is* the key's boundary;
    # ``roles.org_id`` is NULL for every row in v1).
    op.add_column("roles", sa.Column("org_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_roles_org_id"), "roles", ["org_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_roles_org_id_organizations"),
        "roles",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column("api_keys", sa.Column("org_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_api_keys_org_id"), "api_keys", ["org_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_api_keys_org_id_organizations"),
        "api_keys",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # --- 2. Agent credential routing table -----------------------------------
    op.create_table(
        "agent_credentials",
        sa.Column("server_id", sa.Uuid(), nullable=False),
        sa.Column("org_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_agent_credentials_created_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_agent_credentials_org_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["server_id"],
            ["servers.id"],
            name=op.f("fk_agent_credentials_server_id_servers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("server_id", name=op.f("pk_agent_credentials")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_agent_credentials_token_hash")),
    )
    op.create_index(
        op.f("ix_agent_credentials_created_at"), "agent_credentials", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_agent_credentials_org_id"), "agent_credentials", ["org_id"], unique=False
    )

    # --- 3. org_id on every tenant table (nullable first) --------------------
    for table in ORG_SCOPED_TABLES:
        op.add_column(table, sa.Column("org_id", sa.Uuid(), nullable=True))

    # --- 4. Bootstrap organization + backfill --------------------------------
    op.execute(BOOTSTRAP_ORGANIZATION_SQL)
    _backfill_org_ids()

    # --- 5. Enforce NOT NULL, add foreign keys and indexes -------------------
    for table in ORG_SCOPED_TABLES:
        nullable = table in NULLABLE_ORG_TABLES
        if not nullable:
            _assert_fully_backfilled(table)
            op.alter_column(table, "org_id", existing_type=sa.Uuid(), nullable=False)
        op.create_foreign_key(
            op.f(f"fk_{table}_org_id_organizations"),
            table,
            "organizations",
            ["org_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(op.f(f"ix_{table}_org_id"), table, ["org_id"], unique=False)

    op.execute(sa.text("ALTER TABLE api_keys ALTER COLUMN org_id SET NOT NULL"))
    op.execute(sa.text("ALTER TABLE agent_credentials ALTER COLUMN org_id SET NOT NULL"))

    # --- 6. Per-organization uniqueness -------------------------------------
    # Name uniqueness was instance-wide, which both rejected legitimate
    # collisions between tenants and turned a name into an existence oracle for
    # every other organization.
    _drop_constraint("tags", "uq_tags_name")
    op.create_unique_constraint("uq_tags_org_name", "tags", ["org_id", "name"])
    _drop_constraint("servers", "uq_servers_name")
    op.create_unique_constraint("uq_servers_org_name", "servers", ["org_id", "name"])
    _drop_constraint("projects", "uq_projects_name")
    op.create_unique_constraint("uq_projects_org_name", "projects", ["org_id", "name"])
    _drop_constraint("secrets", "uq_secrets_project_key")
    op.create_unique_constraint(
        "uq_secrets_org_project_key", "secrets", ["org_id", "project_id", "key"]
    )
    op.drop_index("ux_secrets_global_key", table_name="secrets")
    op.create_index(
        "ux_secrets_org_global_key",
        "secrets",
        ["org_id", "key"],
        unique=True,
        postgresql_where=sa.text("project_id IS NULL"),
    )

    # --- 7. server_tags.org_id is trigger-maintained ------------------------
    op.execute(SERVER_TAGS_TRIGGER)

    # --- 8. Application role, then the policies -----------------------------
    _set_guc("nexusops.migration.role", settings_role)
    _set_guc("nexusops.migration.password", settings_password or "")
    op.execute(APP_ROLE_SQL)
    _set_guc("nexusops.migration.password", "")

    op.execute(APP_CURRENT_ORG_FUNCTION)
    for table in ORG_SCOPED_TABLES:
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


def _app_role_credentials() -> tuple[str, str | None]:
    """Application role name/password from settings (never hard-coded)."""
    from app.core.config import get_settings

    settings = get_settings()
    return settings.postgres_app_user, settings.postgres_app_password


def _backfill_org_ids() -> None:
    """Point every pre-existing row at the bootstrap organization.

    ``audit_logs`` is append-only, enforced by a BEFORE UPDATE trigger, so it has
    to be disabled for the duration of the backfill and re-enabled immediately
    after — the immutability guarantee is a property of steady-state operation,
    not of a schema migration that has to add a column to history.
    """
    op.execute("ALTER TABLE audit_logs DISABLE TRIGGER audit_logs_no_update")
    try:
        for table in ORG_SCOPED_TABLES:
            op.execute(
                f"UPDATE {table} SET org_id = (SELECT id FROM organizations ORDER BY created_at, id LIMIT 1) "
                f"WHERE org_id IS NULL"
            )
    finally:
        op.execute("ALTER TABLE audit_logs ENABLE TRIGGER audit_logs_no_update")

    op.execute(
        "UPDATE api_keys SET org_id = (SELECT id FROM organizations ORDER BY created_at, id LIMIT 1) "
        "WHERE org_id IS NULL"
    )
    # Carry existing agent tokens across before the column disappears.
    op.execute(
        """
        INSERT INTO agent_credentials (server_id, org_id, token_hash, rotated_at, created_at, updated_at)
        SELECT s.id, s.org_id, s.agent_token_hash, s.agent_enrolled_at, now(), now()
          FROM servers s
         WHERE s.agent_token_hash IS NOT NULL
        ON CONFLICT (server_id) DO NOTHING
        """
    )
    op.drop_index(op.f("ix_servers_agent_token_hash"), table_name="servers")
    op.drop_column("servers", "agent_token_hash")


def _assert_fully_backfilled(table: str) -> None:
    """Fail with a specific message instead of a bare NOT NULL violation."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM {table} WHERE org_id IS NULL) THEN
                RAISE EXCEPTION
                    'cannot scope {table}: rows exist but no organization could be '
                    'provisioned for them (users table is empty). Create an '
                    'organization first, then re-run the migration.';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    for table in ORG_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_system ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute("DROP FUNCTION IF EXISTS app_current_org()")

    op.execute("DROP TRIGGER IF EXISTS server_tags_set_org ON server_tags")
    op.execute("DROP FUNCTION IF EXISTS nexusops_server_tag_set_org()")

    op.add_column("servers", sa.Column("agent_token_hash", sa.String(length=64), nullable=True))
    op.execute(
        """
        UPDATE servers s SET agent_token_hash = c.token_hash
          FROM agent_credentials c WHERE c.server_id = s.id
        """
    )
    op.create_index(
        op.f("ix_servers_agent_token_hash"), "servers", ["agent_token_hash"], unique=False
    )
    op.drop_index(op.f("ix_agent_credentials_org_id"), table_name="agent_credentials")
    op.drop_index(op.f("ix_agent_credentials_created_at"), table_name="agent_credentials")
    op.drop_table("agent_credentials")

    op.drop_index("ux_secrets_org_global_key", table_name="secrets")
    op.create_index(
        "ux_secrets_global_key",
        "secrets",
        ["key"],
        unique=True,
        postgresql_where=sa.text("project_id IS NULL"),
    )
    op.drop_constraint("uq_secrets_org_project_key", "secrets", type_="unique")
    op.create_unique_constraint(op.f("uq_secrets_project_key"), "secrets", ["project_id", "key"])
    op.drop_constraint("uq_projects_org_name", "projects", type_="unique")
    op.create_unique_constraint(op.f("uq_projects_name"), "projects", ["name"])
    op.drop_constraint("uq_servers_org_name", "servers", type_="unique")
    op.create_unique_constraint(op.f("uq_servers_name"), "servers", ["name"])
    op.drop_constraint("uq_tags_org_name", "tags", type_="unique")
    op.create_unique_constraint(op.f("uq_tags_name"), "tags", ["name"])

    for table in ORG_SCOPED_TABLES:
        op.drop_index(op.f(f"ix_{table}_org_id"), table_name=table)
        op.drop_constraint(op.f(f"fk_{table}_org_id_organizations"), table, type_="foreignkey")
        op.drop_column(table, "org_id")

    for table in ("api_keys", "roles"):
        op.drop_constraint(op.f(f"fk_{table}_org_id_organizations"), table, type_="foreignkey")
        op.drop_index(op.f(f"ix_{table}_org_id"), table_name=table)
        op.drop_column(table, "org_id")

    op.drop_index("ix_memberships_user_status", table_name="memberships")
    op.drop_index(op.f("ix_memberships_user_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_org_id"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_created_at"), table_name="memberships")
    op.drop_table("memberships")

    op.drop_index(op.f("ix_organizations_created_at"), table_name="organizations")
    op.drop_table("organizations")
