"""Phase 5.1 — certificate metadata and the pre-issuance lifecycle.

Adds, in one migration with a single head:

* ``certificates`` — the certificate **identity**: which verified domain it is
  for, its canonical primary common name, its additional identifiers, the
  challenge type, the renewal preference, the denormalized expiry the renewal
  sweep reads, and a **derived** status. No key material, no provider, no DEK:
  ``dns_provider_id``, ``suspended_at``/``suspension_reason`` and the material
  columns belong to Phase 5.2 and are introduced there, in the same slice that
  creates what they reference. Nothing here forward-references a table that does
  not exist.
* ``certificate_generations`` — one ACME order + one key pair per row, with the
  **pre-issuance states only**. The ``state`` CHECK is deliberately narrower than
  the design's eventual vocabulary: ``ISSUED`` (and every other material-bearing
  state) is *unrepresentable* rather than merely unused, because a row in one of
  those states would have to carry a private key and this phase has no envelope
  to encrypt it with. There is no ``deke_id`` column and no placeholder value for
  one, and the material guard CHECK arrives with the columns it guards (5.2).

Both are tenant-owned and carry the same two RLS policies plus an explicit
app-role grant as every other tenant table (the tenancy migration's blanket
``GRANT ... ON ALL TABLES`` ran long before these tables existed).

Three structural promises live in the database rather than in prose:

* ``uq_certificates_org_cn`` — one certificate row per name per organization.
* ``uq_cert_generations_one_live`` — a partial unique index over the in-flight
  states, so a second concurrent issuance for one certificate is a database
  error instead of two racing orders.
* ``uq_certificate_generations_cert_number`` — monotonic generation numbers, so a
  rewound or duplicated renewal is refused.

The migration also seeds the two codenames it introduces — ``certificate.read``
and ``certificate.manage`` — into ``permissions`` and grants them to the built-in
roles exactly as ``app/core/permissions.py``'s ``ROLE_MATRIX`` does
(Owner via the wildcard, Admin/Operator read+manage, Developer/Viewer read).
The registry is code, but *stored* grants are data: without this an existing
instance would ship the endpoints with no role able to reach them.

A note on one deliberate deviation from ``docs/phase5-design.md`` §3.1: the
certificate ``status`` column is ``String(24)``, not ``String(16)``. The design's
own vocabulary does not fit in 16 characters (``REVOCATION_PENDING`` and
``REVOKED_LOCAL_ONLY`` are 18), and truncating a state name is worse than
widening the column.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Created: 2026-10-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "c8d9e0f1a2b3"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Mirrors ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated so the migration
#: stays reproducible if the constant moves.
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

#: The closed vocabularies, kept as literals on purpose (a new state is a new
#: migration). ``test_migration_drift.py`` asserts they still equal the enums.
CERTIFICATE_STATUSES = (
    "PENDING",
    "ISSUED",
    "FAILED",
    "EXPIRED",
    "SUSPENDED",
    "REVOCATION_PENDING",
    "REVOKED",
    "REVOKED_LOCAL_ONLY",
)
GENERATION_STATES = ("PENDING", "ORDERING", "CHALLENGE_PUBLISHED", "VALIDATING", "FAILED")
#: The in-flight subset: the predicate of the one-live-generation partial index.
#: ``FAILED`` is outside it so a retry is not blocked by the row it replaces.
LIVE_GENERATION_STATES = ("PENDING", "ORDERING", "CHALLENGE_PUBLISHED", "VALIDATING")
CHALLENGE_TYPES = ("dns-01",)
KEY_ALGORITHMS = ("ecdsa-p256",)

NEW_TENANT_TABLES = ("certificates", "certificate_generations")

#: The codenames this slice registers, with the group/description the registry
#: emits. ``role -> codenames`` is the agreed matrix (phase5-design.md §4.1, O3):
#: Owner holds the wildcard and needs no rows.
NEW_PERMISSIONS: tuple[tuple[str, str, str], ...] = (
    (
        "certificate.read",
        "Certificates",
        "View certificates and their issuance/lifecycle metadata",
    ),
    (
        "certificate.manage",
        "Certificates",
        "Request, renew, revoke and bind certificates; manage DNS credentials",
    ),
)
ROLE_GRANTS: dict[str, tuple[str, ...]] = {
    "Admin": ("certificate.read", "certificate.manage"),
    "Operator": ("certificate.read", "certificate.manage"),
    "Developer": ("certificate.read",),
    "Viewer": ("certificate.read",),
}


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


def _seed_certificate_permissions() -> None:
    """Register the two codenames and grant them to the built-in roles.

    Idempotent in both halves (``ON CONFLICT DO NOTHING``), so re-running the
    migration against an instance whose registry was already seeded by
    ``scripts/seed.py`` changes nothing.
    """
    for codename, group, description in NEW_PERMISSIONS:
        op.execute(
            sa.text(
                'INSERT INTO permissions (id, codename, description, "group", '
                "created_at, updated_at) "
                "VALUES (gen_random_uuid(), :codename, :description, :group, now(), now()) "
                "ON CONFLICT (codename) DO NOTHING"
            ).bindparams(codename=codename, description=description, group=group)
        )
    for role_name, codenames in ROLE_GRANTS.items():
        op.execute(
            sa.text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
                f"WHERE r.name = :role AND {_in_list('p.codename', codenames)} "
                "ON CONFLICT DO NOTHING"
            ).bindparams(role=role_name)
        )


def _drop_certificate_permissions() -> None:
    """Remove the grants and the codename rows.

    ``role_permissions`` cascades from ``permissions``, so deleting the codename
    rows is the whole removal — but the grant rows are deleted explicitly first,
    because the downgrade must be legible about what it takes away.
    """
    names = [codename for codename, _group, _description in NEW_PERMISSIONS]
    op.execute(
        sa.text(
            "DELETE FROM role_permissions WHERE permission_id IN "
            f"(SELECT id FROM permissions WHERE {_in_list('codename', names)})"
        )
    )
    op.execute(sa.text(f"DELETE FROM permissions WHERE {_in_list('codename', names)}"))


def upgrade() -> None:
    # --- 1. certificates ------------------------------------------------------
    op.create_table(
        "certificates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
                name="fk_certificates_org_id_organizations",
            ),
            nullable=False,
        ),
        # RESTRICT: a certificate is issued *for* a name, so removing the domain
        # would orphan material the CA still honours. `domain_service` turns the
        # resulting IntegrityError into a named 409.
        sa.Column(
            "domain_id",
            sa.Uuid(),
            sa.ForeignKey(
                "domains.id", ondelete="RESTRICT", name="fk_certificates_domain_id_domains"
            ),
            nullable=False,
        ),
        sa.Column("primary_cn", sa.String(length=253), nullable=False),
        sa.Column("sans", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        # 24, not the design's 16: REVOCATION_PENDING/REVOKED_LOCAL_ONLY are 18
        # characters and must not be truncated (see the module docstring).
        sa.Column("status", sa.String(length=24), nullable=False, server_default="PENDING"),
        # The FK target is created below; the reference is added immediately after
        # so `certificates` and `certificate_generations` can reference each other.
        sa.Column("current_generation_id", sa.Uuid(), nullable=True),
        sa.Column("challenge_type", sa.String(length=8), nullable=False, server_default="dns-01"),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "key_algorithm", sa.String(length=16), nullable=False, server_default="ecdsa-p256"
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=False, server_default=""),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_in_list("status", CERTIFICATE_STATUSES), name="status_valid"),
        sa.CheckConstraint(
            _in_list("challenge_type", CHALLENGE_TYPES), name="challenge_type_valid"
        ),
        sa.CheckConstraint(_in_list("key_algorithm", KEY_ALGORITHMS), name="key_algorithm_valid"),
        sa.CheckConstraint("char_length(primary_cn) BETWEEN 4 AND 253", name="primary_cn_length"),
        sa.CheckConstraint(
            "jsonb_typeof(sans) = 'array' AND jsonb_array_length(sans) <= 100", name="sans_shape"
        ),
        sa.UniqueConstraint("org_id", "primary_cn", name="uq_certificates_org_cn"),
    )
    op.create_index("ix_certificates_org_id", "certificates", ["org_id"])
    op.create_index("ix_certificates_created_at", "certificates", ["created_at"])
    op.create_index("ix_certificates_domain_id", "certificates", ["domain_id"])
    op.create_index("ix_certificates_org_status", "certificates", ["org_id", "status"])
    op.create_index("ix_certificates_expiry_sweep", "certificates", ["status", "expires_at"])

    # --- 2. certificate_generations ------------------------------------------
    op.create_table(
        "certificate_generations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
                name="fk_certificate_generations_org_id_organizations",
            ),
            nullable=False,
        ),
        sa.Column(
            "certificate_id",
            sa.Uuid(),
            sa.ForeignKey(
                "certificates.id",
                ondelete="CASCADE",
                name="fk_certificate_generations_certificate_id_certificates",
            ),
            nullable=False,
        ),
        sa.Column("generation", sa.Integer(), nullable=False),
        # Pre-issuance only: ISSUED and the other material-bearing states are
        # Phase 5.2's vocabulary, introduced with the envelope they require.
        sa.Column("state", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column("order_state", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_error", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_in_list("state", GENERATION_STATES), name="state_valid"),
        sa.CheckConstraint("generation >= 1", name="generation_positive"),
        sa.CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
        sa.UniqueConstraint(
            "certificate_id", "generation", name="uq_certificate_generations_cert_number"
        ),
    )
    op.create_index("ix_certificate_generations_org_id", "certificate_generations", ["org_id"])
    op.create_index(
        "ix_certificate_generations_created_at", "certificate_generations", ["created_at"]
    )
    op.create_index(
        "ix_certificate_generations_sweep",
        "certificate_generations",
        ["state", "next_attempt_at"],
    )
    # At most one in-flight generation per certificate: a second concurrent
    # issuance is a database error, not two racing orders.
    op.create_index(
        "uq_cert_generations_one_live",
        "certificate_generations",
        ["certificate_id"],
        unique=True,
        postgresql_where=sa.text(_in_list("state", LIVE_GENERATION_STATES)),
    )

    # --- 3. the certificate → generation pointer ------------------------------
    # Added now that its target exists. SET NULL rather than RESTRICT: the
    # pointer is optional, and a generation may only be removed together with its
    # certificate, so nothing may be left dangling.
    op.create_foreign_key(
        "fk_certificates_current_generation_id_certificate_generations",
        "certificates",
        "certificate_generations",
        ["current_generation_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- 4. row-level security ------------------------------------------------
    _tenant_policies("certificates")
    _tenant_policies("certificate_generations")

    # --- 5. app-role grants for the new tables --------------------------------
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

    # --- 6. the codenames this slice introduces -------------------------------
    _seed_certificate_permissions()


def downgrade() -> None:
    _drop_certificate_permissions()

    op.drop_constraint(
        "fk_certificates_current_generation_id_certificate_generations",
        "certificates",
        type_="foreignkey",
    )

    _drop_tenant_policies("certificate_generations")
    op.drop_index("uq_cert_generations_one_live", table_name="certificate_generations")
    op.drop_index("ix_certificate_generations_sweep", table_name="certificate_generations")
    op.drop_index("ix_certificate_generations_created_at", table_name="certificate_generations")
    op.drop_index("ix_certificate_generations_org_id", table_name="certificate_generations")
    op.drop_table("certificate_generations")

    _drop_tenant_policies("certificates")
    op.drop_index("ix_certificates_expiry_sweep", table_name="certificates")
    op.drop_index("ix_certificates_org_status", table_name="certificates")
    op.drop_index("ix_certificates_domain_id", table_name="certificates")
    op.drop_index("ix_certificates_created_at", table_name="certificates")
    op.drop_index("ix_certificates_org_id", table_name="certificates")
    op.drop_table("certificates")
