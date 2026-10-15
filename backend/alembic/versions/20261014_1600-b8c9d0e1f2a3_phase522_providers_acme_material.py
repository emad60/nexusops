"""Phase 5.2.2 — DNS credentials, ACME accounts, and the certificate material columns.

Adds, in one migration from ``a7b8c9d0e1f2`` with a single head:

* ``dns_providers`` — the customer's DNS API credential and the zones it may
  touch. A **dedicated table**, not a reuse of the deployable secret store: that
  store's values are delivered *to nodes*, and a control-plane-only CA/DNS
  credential must never be conflated with one that may leave the platform
  (phase5-design.md §5.3). The credential is Fernet(org DEK) with the DEK
  generation recorded beside it, and ``zone_allowlist`` is what the issuance path
  checks **before** any provider call.
* ``acme_accounts`` — one account per **organization per directory** (§5.4), with
  its key wrapped under the same envelope. Rate-limit blast radius and revocation
  ownership are per tenant, so a shared platform account is not an option the
  schema allows: ``uq_acme_accounts_org_directory`` makes a second account for one
  organization and directory a database error.
* the ``certificates`` columns 5.1 deliberately left out — ``dns_provider_id``
  (**added with the table it references**, so the FK is always satisfiable),
  ``suspended_at``/``suspension_reason`` — plus their index, their RESTRICT
  delete rule and the suspension pair CHECK.
* the ``certificate_generations`` material columns — ``key_ciphertext``,
  ``chain_ciphertext``, ``fingerprint``, ``not_before``/``not_after``,
  ``deke_id``, ``issued_at``, ``revoked_at``, ``revocation_state`` and the
  generation-level suspension pair.

Two structural changes make the literature safe rather than merely present:

**The ``state`` vocabulary is widened in the same revision that adds the material
columns and the envelope that protects them.** 5.1 shipped a truncated CHECK
precisely so a material-less ``ISSUED`` row was unrepresentable; widening it
alone would have reopened that window, so the widening is paired with:

**``ck_certificate_generations_material_guard``** — a generation is *either* in a
pre-issuance state *or* it carries ``key_ciphertext``, ``chain_ciphertext``,
``deke_id``, ``issued_at``, ``not_before`` and ``not_after``. That is the
acceptance criterion of this slice expressed as a constraint: an issued (or
superseded, suspended, expired, revoked) generation cannot exist without its
material, and ``deke_id`` can never be a placeholder for a key that is not there.
``deke_id`` stays nullable — a pre-issuance row legitimately has none — and is
required the instant the state stops being pre-issuance.

Every new table is tenant-owned and gets the same two RLS policies plus the
explicit app-role grant as every other tenant table (the tenancy migration's
blanket ``GRANT ... ON ALL TABLES`` ran long before these tables existed).

Nothing here is destructive: the only columns dropped are the old ``state`` CHECK
(immediately replaced by the wider one plus the guard) and, on downgrade, columns
this revision added. The downgrade removes the material columns **and refuses
outright while any generation carries material** — a rollback that silently
discarded a private key the CA still considers valid would be destruction of
evidence, and a stopped migration with the data intact is the honest outcome.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Created: 2026-10-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Mirrors ``app.models.tenancy.SYSTEM_ORG_SENTINEL``; duplicated so the migration
#: stays reproducible if the constant moves (the same choice 5.1 and 5.2.1 made).
SYSTEM_ORG_SENTINEL = "00000000-0000-0000-0000-000000000000"

#: The closed vocabularies, as literals on purpose (a new state is a new
#: migration). ``test_migration_drift.py`` asserts these still equal the enums.
GENERATION_STATES = (
    "PENDING",
    "ORDERING",
    "CHALLENGE_PUBLISHED",
    "VALIDATING",
    "FAILED",
    "ISSUED",
    "SUPERSEDED",
    "SUSPENDED",
    "EXPIRED",
    "REVOCATION_PENDING",
    "REVOKED",
    "REVOCATION_FAILED",
    "REVOKED_LOCAL_ONLY",
)
#: The states in which a generation carries no material *by construction* — the
#: in-flight ones plus ``FAILED``. The guard CHECK's first branch; its complement
#: is ``material_bearing()``.
PRE_ISSUANCE_STATES = ("PENDING", "ORDERING", "CHALLENGE_PUBLISHED", "VALIDATING", "FAILED")
REVOCATION_STATES = (
    "NOT_REQUESTED",
    "PENDING",
    "REVOKED",
    "FAILED",
    "REVOKED_LOCAL_ONLY",
)
DNS_PROVIDER_KINDS = ("cloudflare",)
KEY_ALGORITHMS = ("ecdsa-p256",)

NEW_TENANT_TABLES = ("dns_providers", "acme_accounts")

#: The constraint 5.1 created and this revision replaces.
CK_GENERATIONS_STATE = "ck_certificate_generations_state_valid"

#: Full names, because ``op.f`` marks an already-conventional name as final: the
#: ``ck_%(table_name)s_%(constraint_name)s`` convention would otherwise expand an
#: explicitly passed name a second time.
CK_GENERATIONS_MATERIAL_GUARD = "ck_certificate_generations_material_guard"
CK_CERTIFICATES_SUSPENSION_PAIR = "ck_certificates_suspension_pair_valid"
CK_GENERATIONS_SUSPENSION_PAIR = "ck_certificate_generations_suspension_pair_valid"

#: The material guard: a pre-issuance row needs nothing, every other row needs all
#: six fields. Spelled as SQL here (a CHECK cannot call Python), derived from the
#: same two lists the model derives its predicate from.
MATERIAL_GUARD_PREDICATE = (
    f"state IN ({', '.join(repr(state) for state in PRE_ISSUANCE_STATES)}) OR ("
    "key_ciphertext IS NOT NULL AND chain_ciphertext IS NOT NULL AND deke_id IS NOT NULL "
    "AND issued_at IS NOT NULL AND not_before IS NOT NULL AND not_after IS NOT NULL)"
)
SUSPENSION_PAIR_PREDICATE = "(suspended_at IS NULL) = (suspension_reason = '')"


def _in_list(column: str, values: Sequence[str]) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


def _drop_constraint(table: str, name: str) -> None:
    """Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS``.

    ``op.drop_constraint`` is not obviously exempt from the naming convention, and
    a name that silently failed to match would leave the 5.1 CHECK in place — the
    whole vocabulary widening would then be a no-op that the drift test would
    report as a missing constraint rather than as a refused issuance.
    """
    op.execute(sa.text(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{name}"'))


def _grant(table: str) -> None:
    """Grant the app role the four DML verbs on *table*.

    Not ownership, and not ``BYPASSRLS``: the policies are only load-bearing
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


def _assert_no_material() -> None:
    """Refuse the downgrade while any generation carries key material.

    The check runs *before* the first column is dropped, so a refusal leaves the
    schema untouched rather than half-rolled-back. It is the same stance 5.2.1's
    downgrade took for a wrapped DEK, applied to the material this revision adds:
    a migration that cannot safely undo itself stops, and says so.
    """
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                carrying integer;
            BEGIN
                SELECT count(*) INTO carrying
                  FROM certificate_generations
                 WHERE key_ciphertext IS NOT NULL
                    OR chain_ciphertext IS NOT NULL
                    OR deke_id IS NOT NULL;
                IF carrying > 0 THEN
                    RAISE EXCEPTION
                        'refusing to downgrade past 5.2.2: % certificate generation(s) carry '
                        'key material, and this revision is the only thing that defines where it '
                        'lives. Revoke and remove them first, or restore from a backup taken '
                        'before the upgrade.', carrying;
                END IF;
            END $$;
            """
        )
    )


def upgrade() -> None:
    # --- 1. dns_providers ------------------------------------------------------
    op.create_table(
        "dns_providers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
                name="fk_dns_providers_org_id_organizations",
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="cloudflare"),
        # Fernet(org DEK). Never returned by any endpoint; the fingerprint below is
        # what an operator sees instead.
        sa.Column("credentials_ciphertext", sa.Text(), nullable=False),
        sa.Column("credential_fingerprint", sa.String(length=64), nullable=False),
        # Which organization-DEK generation encrypted the blob, so a DEK rotation
        # can find this row again (§6.3) and the payload's context binding can be
        # checked. NOT NULL and >= 1: unlike a generation row, this table only ever
        # exists *with* a credential, so there is no "no DEK yet" case.
        sa.Column("deke_id", sa.Integer(), nullable=False),
        sa.Column("scopes", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("zone_allowlist", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verify_error", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("auto_cleanup", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_in_list("kind", DNS_PROVIDER_KINDS), name="kind_valid"),
        sa.CheckConstraint("char_length(name) BETWEEN 1 AND 120", name="name_length"),
        sa.CheckConstraint("char_length(credential_fingerprint) = 64", name="credential_fingerprint_length"),
        sa.CheckConstraint(
            "jsonb_typeof(zone_allowlist) = 'array' AND jsonb_array_length(zone_allowlist) <= 200",
            name="zone_allowlist_shape",
        ),
        sa.CheckConstraint("jsonb_typeof(scopes) = 'object'", name="scopes_shape"),
        sa.CheckConstraint("deke_id >= 1", name="deke_id_positive"),
        # Operator-facing handle: two rows called "Cloudflare production" would make
        # every later reference ambiguous.
        sa.UniqueConstraint("org_id", "name", name="uq_dns_providers_org_name"),
    )
    op.create_index("ix_dns_providers_org_id", "dns_providers", ["org_id"])
    op.create_index("ix_dns_providers_created_at", "dns_providers", ["created_at"])
    op.create_index("ix_dns_providers_org_kind", "dns_providers", ["org_id", "kind"])
    op.create_index("ix_dns_providers_deke_id", "dns_providers", ["deke_id"])

    # --- 2. acme_accounts ------------------------------------------------------
    op.create_table(
        "acme_accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey(
                "organizations.id",
                ondelete="CASCADE",
                name="fk_acme_accounts_org_id_organizations",
            ),
            nullable=False,
        ),
        # Explicit configuration, never inferred from ENVIRONMENT: a production
        # issuance that finds no production configuration fails closed rather than
        # quietly minting a staging certificate (§5.4).
        sa.Column("directory_url", sa.String(length=255), nullable=False),
        # The CA's account URL (the JWS ``kid``). NULL until 5.3 registers the
        # account; the row is created by the code path that will register it.
        sa.Column("account_url", sa.String(length=512), nullable=True),
        sa.Column("key_ciphertext", sa.Text(), nullable=False),
        sa.Column("key_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("deke_id", sa.Integer(), nullable=False),
        sa.Column("key_algorithm", sa.String(length=16), nullable=False, server_default="ecdsa-p256"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(_in_list("key_algorithm", KEY_ALGORITHMS), name="key_algorithm_valid"),
        sa.CheckConstraint("char_length(directory_url) BETWEEN 8 AND 255", name="directory_url_length"),
        sa.CheckConstraint("char_length(key_fingerprint) = 64", name="key_fingerprint_length"),
        sa.CheckConstraint("deke_id >= 1", name="deke_id_positive"),
        # The identity of an account is (organization, directory): staging and
        # production are two rows, and a duplicate registration for the same pair is
        # a database error rather than a second account at the CA.
        sa.UniqueConstraint("org_id", "directory_url", name="uq_acme_accounts_org_directory"),
    )
    op.create_index("ix_acme_accounts_org_id", "acme_accounts", ["org_id"])
    op.create_index("ix_acme_accounts_created_at", "acme_accounts", ["created_at"])
    op.create_index("ix_acme_accounts_org_id_created", "acme_accounts", ["org_id", "created_at"])

    # --- 3. certificates: the credential override and the suspension pair -------
    # dns_provider_id arrives *with* the table it references, so the FK is always
    # satisfiable and there is no window in which the column exists and its target
    # does not.
    op.add_column("certificates", sa.Column("dns_provider_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_certificates_dns_provider_id_dns_providers",
        "certificates",
        "dns_providers",
        ["dns_provider_id"],
        ["id"],
        # RESTRICT: deleting a credential a certificate still names would silently
        # change which token signs for it on the next renewal — the worst kind of
        # failure, because it keeps working. `dns_provider_service` turns the
        # IntegrityError into a named 409.
        ondelete="RESTRICT",
    )
    op.add_column("certificates", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "certificates",
        sa.Column("suspension_reason", sa.String(length=64), nullable=False, server_default=""),
    )
    op.create_check_constraint(
        op.f(CK_CERTIFICATES_SUSPENSION_PAIR), "certificates", SUSPENSION_PAIR_PREDICATE
    )
    op.create_index("ix_certificates_dns_provider_id", "certificates", ["dns_provider_id"])

    # --- 4. certificate_generations: the material ---------------------------------
    op.add_column("certificate_generations", sa.Column("key_ciphertext", sa.Text(), nullable=True))
    op.add_column(
        "certificate_generations", sa.Column("chain_ciphertext", sa.Text(), nullable=True)
    )
    op.add_column(
        "certificate_generations", sa.Column("fingerprint", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "certificate_generations", sa.Column("not_before", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "certificate_generations", sa.Column("not_after", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("certificate_generations", sa.Column("deke_id", sa.Integer(), nullable=True))
    op.add_column(
        "certificate_generations", sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "certificate_generations", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "certificate_generations",
        sa.Column("revocation_state", sa.String(length=24), nullable=False, server_default="NOT_REQUESTED"),
    )
    op.add_column(
        "certificate_generations", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "certificate_generations",
        sa.Column("suspension_reason", sa.String(length=64), nullable=False, server_default=""),
    )
    op.create_check_constraint(
        op.f("ck_certificate_generations_revocation_state_valid"),
        "certificate_generations",
        _in_list("revocation_state", REVOCATION_STATES),
    )
    op.create_check_constraint(
        op.f("ck_certificate_generations_fingerprint_length"),
        "certificate_generations",
        "fingerprint IS NULL OR char_length(fingerprint) = 64",
    )
    op.create_check_constraint(
        op.f("ck_certificate_generations_deke_id_positive"),
        "certificate_generations",
        "deke_id IS NULL OR deke_id >= 1",
    )
    op.create_check_constraint(
        op.f("ck_certificate_generations_validity_window"),
        "certificate_generations",
        "not_after IS NULL OR not_before IS NULL OR not_after > not_before",
    )
    op.create_check_constraint(
        op.f(CK_GENERATIONS_SUSPENSION_PAIR),
        "certificate_generations",
        SUSPENSION_PAIR_PREDICATE,
    )
    op.create_index("ix_certificate_generations_deke_id", "certificate_generations", ["deke_id"])

    # --- 5. widen the state vocabulary, and guard the material in one step -------
    # The old CHECK is dropped and the wider one created *in the same transaction*
    # and immediately followed by the guard: there is no committed state in which a
    # generation may name a material-bearing state and hold no material.
    _drop_constraint("certificate_generations", CK_GENERATIONS_STATE)
    op.create_check_constraint(
        op.f(CK_GENERATIONS_STATE), "certificate_generations", _in_list("state", GENERATION_STATES)
    )
    op.create_check_constraint(
        op.f(CK_GENERATIONS_MATERIAL_GUARD), "certificate_generations", MATERIAL_GUARD_PREDICATE
    )

    # --- 6. row-level security, then the app-role grants -------------------------
    for table in NEW_TENANT_TABLES:
        _tenant_policies(table)

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
    """Remove this slice — refusing outright while any generation holds material."""
    _assert_no_material()

    # The vocabulary goes back to the pre-issuance-only set, and the guard goes with
    # the columns it guards. Dropping the guard *first* is deliberate: it is the only
    # constraint that would refuse the states the narrowed CHECK is about to, so a
    # failure between the two leaves the stricter constraint in place rather than a
    # table with neither.
    _drop_constraint("certificate_generations", CK_GENERATIONS_MATERIAL_GUARD)
    _drop_constraint("certificate_generations", CK_GENERATIONS_STATE)
    op.create_check_constraint(
        op.f(CK_GENERATIONS_STATE),
        "certificate_generations",
        _in_list("state", PRE_ISSUANCE_STATES),
    )

    op.drop_index("ix_certificate_generations_deke_id", table_name="certificate_generations")
    _drop_constraint("certificate_generations", CK_GENERATIONS_SUSPENSION_PAIR)
    for name, _column in (
        ("ck_certificate_generations_validity_window", "not_after"),
        ("ck_certificate_generations_deke_id_positive", "deke_id"),
        ("ck_certificate_generations_fingerprint_length", "fingerprint"),
        ("ck_certificate_generations_revocation_state_valid", "revocation_state"),
    ):
        _drop_constraint("certificate_generations", name)
    for column in (
        "suspension_reason",
        "suspended_at",
        "revocation_state",
        "revoked_at",
        "issued_at",
        "deke_id",
        "not_after",
        "not_before",
        "fingerprint",
        "chain_ciphertext",
        "key_ciphertext",
    ):
        op.drop_column("certificate_generations", column)

    op.drop_index("ix_certificates_dns_provider_id", table_name="certificates")
    _drop_constraint("certificates", CK_CERTIFICATES_SUSPENSION_PAIR)
    op.drop_column("certificates", "suspension_reason")
    op.drop_column("certificates", "suspended_at")
    op.drop_constraint(
        "fk_certificates_dns_provider_id_dns_providers", "certificates", type_="foreignkey"
    )
    op.drop_column("certificates", "dns_provider_id")

    for table in ("acme_accounts", "dns_providers"):
        _drop_tenant_policies(table)

    op.drop_index("ix_acme_accounts_org_id_created", table_name="acme_accounts")
    op.drop_index("ix_acme_accounts_created_at", table_name="acme_accounts")
    op.drop_index("ix_acme_accounts_org_id", table_name="acme_accounts")
    op.drop_table("acme_accounts")

    op.drop_index("ix_dns_providers_deke_id", table_name="dns_providers")
    op.drop_index("ix_dns_providers_org_kind", table_name="dns_providers")
    op.drop_index("ix_dns_providers_created_at", table_name="dns_providers")
    op.drop_index("ix_dns_providers_org_id", table_name="dns_providers")
    op.drop_table("dns_providers")
