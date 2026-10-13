"""Phase 5.2.1.2 — the organization DEK envelope gets a tenant table of its own.

Phase 5.2.1 put ``dek_ciphertext``/``dek_generation`` on ``organizations``. That
table is one of the documented **RLS-exempt** tables — it *is* the tenant and
cannot be scoped by its own id — so the envelope sat outside every database-level
tenant net, and the confidentiality of every organization's key material rested on
the KEK provider alone. The independent audit of 5.2.1 recorded that as F1: any
read path that could reach an organization row (a listing, a join, a bulk export,
a future report) could read another tenant's envelope, and PostgreSQL would not
have refused.

This revision moves the envelope into ``organization_dek_envelopes``, an ordinary
``OrgScoped`` tenant table, and drops the two columns from ``organizations``. The
move is what turns the boundary into a database property instead of a convention:

* ``org_id`` is NOT NULL with a foreign key to ``organizations`` (``ON DELETE
  CASCADE``), so ownership is explicit and an organization cannot leave an
  envelope behind.
* ``uq_organization_dek_envelopes_org_id`` makes "one authoritative current
  envelope and generation per organization" a schema guarantee — a second row for
  one tenant is refused by the database rather than prevented by a service
  remembering to check.
* the same two RLS policies every other tenant table carries (tenant + system) are
  created here, plus the explicit app-role grant, because the tenancy migration's
  blanket ``GRANT ... ON ALL TABLES`` ran long before this table existed.
* the pair invariant survives unchanged, joined by the explicit non-negative
  generation bound the 5.2.1 migration documented but did not create (audit
  finding F3): generation 0 means "no DEK yet", so a ciphertext carrying it would
  be an orphan, and a negative generation is not a state this model can produce —
  only a writer that bypassed the model can, which is exactly what a CHECK is for.

**Populated envelopes are moved, never discarded.** The upgrade copies every
non-NULL envelope with its generation *before* dropping the source columns and
raises if the counts disagree: a migration that silently dropped the only copy of
a wrapped DEK would strand that organization permanently, and the count check is
cheap.

The downgrade restores rather than destroys. It recreates the two columns, copies
every envelope back, verifies the copy, and only then drops the new table — so a
downgrade that cannot verify what it moved is a **stopped migration** with the key
material still in place, not lost key material. (Phase 5.2.1's own downgrade took
the opposite stance and refused to run at all while any envelope existed; that
refusal is gone because the data now has somewhere to go. The 5.2.1 *revision* is
not modified — this revision owns the reversal.)

Revision ID: a7b8c9d0e1f2
Revises: f5a6b7c8d9e0
Created: 2026-10-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Mirrors ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated so the migration
#: stays reproducible if the constant moves (the same choice 5.1 made).
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

TABLE = "organization_dek_envelopes"

#: The constraint the 5.2.1 revision created on ``organizations``; dropped here
#: with the columns it constrains, and recreated by the downgrade.
CK_ORGANIZATIONS_DEK_PAIR = "ck_organizations_dek_pair_valid"
DEK_PAIR_PREDICATE = "(dek_ciphertext IS NULL) = (dek_generation = 0)"

#: The predicate is copied verbatim from 5.2.1 — the invariant is not being
#: redefined, only relocated.
MOVE_ENVELOPES = """
INSERT INTO organization_dek_envelopes
    (id, org_id, dek_ciphertext, dek_generation, created_at, updated_at)
SELECT gen_random_uuid(), o.id, o.dek_ciphertext, o.dek_generation, now(), now()
  FROM organizations o
 WHERE o.dek_ciphertext IS NOT NULL
"""

def _drop_constraint(table: str, name: str) -> None:
    """Raw ``ALTER TABLE ... DROP CONSTRAINT``, as the tenancy migration does.

    ``op.drop_constraint`` would be the tidier call, but it is not obviously
    exempt from the ``ck_%(table_name)s_%(constraint_name)s`` convention, and a
    name that silently failed to match would leave the old pair check in place
    (or, worse, the columns without it).
    """
    op.execute(sa.text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{name}"'))


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


def _grant(table: str) -> None:
    """Grant the app role the four DML verbs on *table*.

    Not ownership, and not ``BYPASSRLS``: the policies above are only load-bearing
    because the role that serves traffic is neither the table's owner nor exempt.
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
    # --- 1. the tenant table --------------------------------------------------
    op.create_table(
        TABLE,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
                name="fk_organization_dek_envelopes_org_id_organizations",
            ),
            nullable=False,
        ),
        sa.Column("dek_ciphertext", sa.Text(), nullable=True),
        sa.Column("dek_generation", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        # Short names: the ``ck_%(table_name)s_%(constraint_name)s`` convention
        # expands an explicitly given name, so passing the full name here would
        # land ``ck_organization_dek_envelopes_ck_organization_dek_envelopes_...``.
        sa.CheckConstraint("dek_generation >= 0", name="dek_generation_non_negative"),
        sa.CheckConstraint(DEK_PAIR_PREDICATE, name="dek_pair_valid"),
        sa.UniqueConstraint("org_id", name="uq_organization_dek_envelopes_org_id"),
    )
    op.create_index("ix_organization_dek_envelopes_org_id", TABLE, ["org_id"])
    op.create_index("ix_organization_dek_envelopes_created_at", TABLE, ["created_at"])

    # --- 2. carry every existing envelope across, then check the copy ---------
    op.execute(sa.text(MOVE_ENVELOPES))
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                moved integer;
                landed integer;
            BEGIN
                SELECT count(*) INTO moved FROM organizations WHERE dek_ciphertext IS NOT NULL;
                SELECT count(*) INTO landed
                  FROM organization_dek_envelopes WHERE dek_ciphertext IS NOT NULL;
                IF moved <> landed THEN
                    RAISE EXCEPTION
                        'refusing to drop the organization DEK columns: % populated envelope(s) '
                        'in organizations but % in organization_dek_envelopes. The move did not '
                        'carry every wrapped DEK, and dropping the source columns would destroy '
                        'the only copy of the missing key material.',
                        moved, landed;
                END IF;
            END $$;
            """
        )
    )

    # --- 3. retire the columns on organizations -------------------------------
    _drop_constraint("organizations", CK_ORGANIZATIONS_DEK_PAIR)
    op.drop_column("organizations", "dek_generation")
    op.drop_column("organizations", "dek_ciphertext")

    # --- 4. row-level security, then the app-role grant -----------------------
    _tenant_policies(TABLE)

    from app.core.config import get_settings

    settings = get_settings()
    op.execute(
        sa.text("SELECT set_config('nexusops.migration.role', :role, false)").bindparams(
            role=settings.postgres_app_user
        )
    )
    _grant(TABLE)
    op.execute(sa.text("SELECT set_config('nexusops.migration.role', '', false)"))


def downgrade() -> None:
    """Restore the envelope onto ``organizations`` — without losing any of it."""
    op.add_column("organizations", sa.Column("dek_ciphertext", sa.Text(), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("dek_generation", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute(
        sa.text(
            """
            UPDATE organizations o
               SET dek_ciphertext = e.dek_ciphertext,
                   dek_generation = e.dek_generation
              FROM organization_dek_envelopes e
             WHERE e.org_id = o.id
               AND e.dek_ciphertext IS NOT NULL
            """
        )
    )
    # Verified *before* the table is dropped: a mismatch stops the migration with
    # both copies still present rather than removing the newer one.
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                stored integer;
                restored integer;
            BEGIN
                SELECT count(*) INTO stored
                  FROM organization_dek_envelopes WHERE dek_ciphertext IS NOT NULL;
                SELECT count(*) INTO restored
                  FROM organizations WHERE dek_ciphertext IS NOT NULL;
                IF stored <> restored THEN
                    RAISE EXCEPTION
                        'refusing to drop organization_dek_envelopes: % populated envelope(s) '
                        'were stored but % are present on organizations afterwards. The table '
                        'is left in place so the unverified key material still has a home.',
                        stored, restored;
                END IF;
            END $$;
            """
        )
    )
    op.create_check_constraint(
        op.f(CK_ORGANIZATIONS_DEK_PAIR), "organizations", DEK_PAIR_PREDICATE
    )

    _drop_tenant_policies(TABLE)
    op.drop_index("ix_organization_dek_envelopes_created_at", table_name=TABLE)
    op.drop_index("ix_organization_dek_envelopes_org_id", table_name=TABLE)
    op.drop_table(TABLE)
