"""Phase 5.1 migration (`c8d9e0f1a2b3`) against a populated Phase 4.2 database.

The migration is additive — two new tables, their policies, their grants and two
permission codenames — but "additive" is a claim, and this module tests it the
way the earlier phase migrations test theirs:

* a **populated** instance is built in the schema it was written for (Phase 4.2),
  migrated forward, and every pre-existing row is checked: nothing is rewritten,
  backfilled or re-pointed, including the routing tables the new
  ``certificates.domain_id`` reference points at.
* the new schema is then checked as a *database*, not as a document: columns,
  the two closed vocabularies, the uniqueness semantics, the partial index that
  allows one in-flight generation, the foreign keys and their delete rules, RLS
  on both tables, and the app-role grants.
* the slice boundary is asserted in the negative too. Phase 5.1 must not
  forward-reference Phase 5.2: no ``dns_providers``/``acme_accounts`` table, no
  ``dns_provider_id`` column, no key/chain ciphertext and no ``deke_id`` — so
  there is no placeholder a later slice would have to clean up.
* ``downgrade`` is exercised for real (Alembic's own ``command.downgrade``): the
  new schema and the codenames must disappear, the pre-existing data must
  survive, and a second ``upgrade`` must restore exactly what was removed.

Every statement is parameterized — the fixtures are constant, but test SQL that
interpolates is a habit worth never forming.
"""

from __future__ import annotations

import json
import uuid

import psycopg
import pytest

from .test_migration_phase2 import (
    Statement,
    _alembic_config,
    _exec,
    _rows,
    _run_downgrade,
    _run_migration,
)

pytestmark = pytest.mark.integration

#: The Phase 4.2 head — the schema Phase 5.1 is written on top of.
PRE_PHASE5_REVISION = "b7c8d9e0f1a2"
#: The Phase 5.1 revision this module pins.
PHASE5_REVISION = "c8d9e0f1a2b3"

ORG = "55555555-5555-5555-5555-555555555555"
OTHER_ORG = "66666666-6666-6666-6666-666666666666"
PROJECT = "bbbb5555-0000-0000-0000-000000000001"
NODE = "bbbb5555-0000-0000-0000-000000000002"
DOMAIN = "bbbb5555-0000-0000-0000-000000000003"
#: The same name, tracked by the *other* organization — the platform model, where
#: two tenants may know a name but only one may hold it verified.
OTHER_DOMAIN = "bbbb5555-0000-0000-0000-00000000000a"
ROUTE = "bbbb5555-0000-0000-0000-000000000004"
MONITOR = "bbbb5555-0000-0000-0000-000000000005"
OPERATION = "bbbb5555-0000-0000-0000-000000000006"

DOMAIN_NAME = "phase5.example.com"
HOSTNAME = "app.phase5.example.com"

#: Columns Phase 5.2 introduces with the key envelope and the providers. None of
#: them may exist yet: a column that references a table or an envelope is added in
#: the slice that creates it.
LATER_SLICE_COLUMNS = (
    "dns_provider_id",
    "suspended_at",
    "suspension_reason",
    "key_ciphertext",
    "chain_ciphertext",
    "fingerprint",
    "not_before",
    "not_after",
    "deke_id",
    "issued_at",
    "revoked_at",
    "revocation_state",
)
LATER_SLICE_TABLES = ("dns_providers", "acme_accounts", "certificate_deliveries")

PERMISSION_CODENAMES = ("certificate.read", "certificate.manage")
#: ``role -> codenames`` — the matrix the registry seeds (phase5-design.md §4.1).
EXPECTED_GRANTS = {
    "Admin": ("certificate.manage", "certificate.read"),
    "Operator": ("certificate.manage", "certificate.read"),
    "Developer": ("certificate.read",),
    "Viewer": ("certificate.read",),
}


def _seed_phase4(database: str) -> None:
    """A populated pre-Phase-5 instance: tenancy, routing, a monitor, an operation."""
    statements: list[Statement] = [
        (
            "INSERT INTO organizations (id, name, slug, description, status, is_provisional) "
            "VALUES (%s, 'Acme', 'acme', '', 'ACTIVE', false), "
            "(%s, 'Globex', 'globex', '', 'ACTIVE', false)",
            (ORG, OTHER_ORG),
        ),
        (
            "INSERT INTO projects "
            "(id, org_id, name, description, repository_url, default_branch) "
            "VALUES (%s, %s, 'Ymart', '', 'https://git.example/ymart.git', 'main')",
            (PROJECT, ORG),
        ),
        (
            "INSERT INTO servers "
            "(id, org_id, name, hostname, ip_address, os_name, os_version, arch, environment, "
            " location, description, status, cpu_cores, memory_total_mb, disk_total_gb, "
            " agent_version, heartbeat_interval_seconds, uptime_seconds, simulated, extra, "
            " protocol_version, capabilities, proxy_state) "
            "VALUES (%s, %s, 'node-legacy', 'node-legacy.example.com', '10.0.0.5', 'Ubuntu', "
            " '24.04', 'x86_64', 'PROD', '', '', 'ONLINE', 4, 8192, 200, '1.2.0', 30, 86400, "
            " false, '{}', 2, '{\"nginx\": {\"present\": true}}', '{}')",
            (NODE, ORG),
        ),
        (
            "INSERT INTO domains "
            "(id, org_id, name, status, verification_token, ns_snapshot, last_error, "
            " dns_reachability, verified_at) "
            "VALUES (%s, %s, %s, 'VERIFIED', 'nxs-verify-token', '[]', '', '{}', now())",
            (DOMAIN, ORG, DOMAIN_NAME),
        ),
        (
            "INSERT INTO domains "
            "(id, org_id, name, status, verification_token, ns_snapshot, last_error, "
            " dns_reachability) "
            "VALUES (%s, %s, %s, 'PENDING', 'nxs-verify-other', '[]', '', '{}')",
            (OTHER_DOMAIN, OTHER_ORG, DOMAIN_NAME),
        ),
        (
            "INSERT INTO routes "
            "(id, org_id, domain_id, hostname, path, node_id, port, scheme, headers, enabled, "
            " config_state, monitor_optout, last_apply_error) "
            "VALUES (%s, %s, %s, %s, '/', %s, 8081, 'http', '[]', true, 'IN_SYNC', false, '')",
            (ROUTE, ORG, DOMAIN, HOSTNAME, NODE),
        ),
        (
            "INSERT INTO monitors "
            "(id, org_id, name, url, method, interval_seconds, timeout_seconds, expected_status, "
            " expected_body, headers, skip_tls_verify, follow_redirects, enabled, status, "
            " consecutive_failures, consecutive_successes, next_check_at, failure_threshold, "
            " success_threshold, target_type) "
            "VALUES (%s, %s, 'legacy probe', 'http://phase5.example.com/health', 'GET', 60, "
            " 10.0, 200, NULL, '{}', false, true, true, 'UP', 0, 3, now(), 3, 2, 'URL')",
            (MONITOR, ORG),
        ),
        (
            "INSERT INTO operations "
            "(id, org_id, node_id, type, status, params, available_until, expires_at, attempts) "
            "VALUES (%s, %s, %s, 'container.start', 'SUCCEEDED', '{}', "
            " '2026-10-09T12:00:00Z', '2026-10-09T12:05:00Z', 1)",
            (OPERATION, ORG, NODE),
        ),
    ]
    _exec(database, statements)


def _migrate_from_phase4(database: str) -> None:
    _run_migration(database, PRE_PHASE5_REVISION)
    _seed_phase4(database)
    _run_migration(database, "head")


def _integrity_error(database: str, statements: list[Statement]) -> None:
    with pytest.raises(psycopg.errors.IntegrityError):
        _exec(database, statements)


def _columns(database: str, table: str) -> set[str]:
    return {
        str(row[0])
        for row in _rows(
            database,
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s",
            (table,),
        )
    }


def _tables(database: str) -> set[str]:
    return {
        str(row[0])
        for row in _rows(
            database,
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'",
        )
    }


def _indexes(database: str, table: str) -> dict[str, str]:
    """``{index_name: index_definition}`` for one table."""
    return {
        str(row[0]): str(row[1])
        for row in _rows(
            database,
            "SELECT indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = 'public' AND tablename = %s",
            (table,),
        )
    }


def _foreign_keys(database: str, table: str) -> dict[str, tuple[str, str]]:
    """``{constraint: (referred_table, delete_rule_letter)}`` for one table."""
    rows = _rows(
        database,
        "SELECT conname, confrelid::regclass::text, confdeltype FROM pg_constraint "
        "WHERE conrelid = %s::regclass AND contype = 'f'",
        (table,),
    )
    return {str(row[0]): (str(row[1]), str(row[2])) for row in rows}


def _permission_grants(database: str) -> dict[str, tuple[str, ...]]:
    """``{role: codenames}`` for the codenames this slice introduces."""
    rows = _rows(
        database,
        "SELECT r.name, p.codename FROM roles r "
        "JOIN role_permissions rp ON rp.role_id = r.id "
        "JOIN permissions p ON p.id = rp.permission_id "
        "WHERE p.codename IN ('certificate.read', 'certificate.manage') "
        "ORDER BY r.name, p.codename",
    )
    grants: dict[str, list[str]] = {}
    for role, codename in rows:
        grants.setdefault(str(role), []).append(str(codename))
    return {role: tuple(codenames) for role, codenames in grants.items()}


def _insert_certificate(
    database: str,
    *,
    certificate_id: str,
    primary_cn: str,
    domain_id: str = DOMAIN,
    org_id: str = ORG,
    status: str = "PENDING",
    challenge_type: str = "dns-01",
    key_algorithm: str = "ecdsa-p256",
    sans: object = None,
) -> None:
    """One certificate row, with every vocabulary value overridable.

    ``sans`` is passed as a JSON document and cast on the server, so the helper
    stays parameterized even when a test deliberately hands it the wrong shape.
    """
    _exec(
        database,
        [
            (
                "INSERT INTO certificates "
                "(id, org_id, domain_id, primary_cn, sans, status, challenge_type, auto_renew, "
                " key_algorithm, last_error) "
                "VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, true, %s, '')",
                (
                    certificate_id,
                    org_id,
                    domain_id,
                    primary_cn,
                    json.dumps([] if sans is None else sans),
                    status,
                    challenge_type,
                    key_algorithm,
                ),
            )
        ],
    )


def _insert_generation(
    database: str,
    *,
    certificate_id: str,
    generation: int,
    state: str = "PENDING",
    org_id: str = ORG,
) -> str:
    generation_id = str(uuid.uuid4())
    _exec(
        database,
        [
            (
                "INSERT INTO certificate_generations "
                "(id, org_id, certificate_id, generation, state, order_state, last_error, "
                " attempt_count) "
                "VALUES (%s, %s, %s, %s, %s, '{}', '', 0)",
                (generation_id, org_id, certificate_id, generation, state),
            )
        ],
    )
    return generation_id


# --- 1. an existing instance ----------------------------------------------------


def test_a_populated_instance_migrates_without_losing_anything(scratch_database: str) -> None:
    _migrate_from_phase4(scratch_database)

    assert _rows(
        scratch_database,
        "SELECT name, status FROM domains WHERE id = %s",
        (DOMAIN,),
    ) == [(DOMAIN_NAME, "VERIFIED")]
    assert _rows(
        scratch_database,
        "SELECT hostname, path, enabled, config_state FROM routes WHERE id = %s",
        (ROUTE,),
    ) == [(HOSTNAME, "/", True, "IN_SYNC")]
    assert _rows(
        scratch_database,
        "SELECT name, status, proxy_state FROM servers WHERE id = %s",
        (NODE,),
    ) == [("node-legacy", "ONLINE", {})]
    assert _rows(
        scratch_database,
        "SELECT type, status FROM operations WHERE id = %s",
        (OPERATION,),
    ) == [("container.start", "SUCCEEDED")]
    assert _rows(
        scratch_database,
        "SELECT count(*) FROM organizations",
    ) == [(2,)]

    # The new tables arrive empty: nothing is backfilled, invented or guessed.
    assert _rows(scratch_database, "SELECT count(*) FROM certificates") == [(0,)]
    assert _rows(scratch_database, "SELECT count(*) FROM certificate_generations") == [(0,)]


# --- 2. the new schema ---------------------------------------------------------


def test_the_two_tables_carry_the_specified_columns(scratch_database: str) -> None:
    _migrate_from_phase4(scratch_database)

    assert _columns(scratch_database, "certificates") == {
        "id",
        "org_id",
        "domain_id",
        "primary_cn",
        "sans",
        "status",
        "current_generation_id",
        "challenge_type",
        "auto_renew",
        "key_algorithm",
        "expires_at",
        "last_error",
        "created_at",
        "updated_at",
    }
    assert _columns(scratch_database, "certificate_generations") == {
        "id",
        "org_id",
        "certificate_id",
        "generation",
        "state",
        "order_state",
        "last_error",
        "next_attempt_at",
        "attempt_count",
        "created_at",
        "updated_at",
    }


def test_the_slice_boundary_is_not_forward_referenced(scratch_database: str) -> None:
    """Phase 5.1 introduces no column or table that belongs to a later slice."""
    _migrate_from_phase4(scratch_database)

    tables = _tables(scratch_database)
    for later in LATER_SLICE_TABLES:
        assert later not in tables, f"{later} belongs to a later slice"

    columns = _columns(scratch_database, "certificates") | _columns(
        scratch_database, "certificate_generations"
    )
    for later in LATER_SLICE_COLUMNS:
        assert later not in columns, f"{later} belongs to a later slice"


def test_the_closed_vocabularies_are_enforced_by_the_database(scratch_database: str) -> None:
    _migrate_from_phase4(scratch_database)
    _insert_certificate(scratch_database, certificate_id=str(uuid.uuid4()), primary_cn=DOMAIN_NAME)

    checks = {
        str(row[0]): str(row[1])
        for row in _rows(
            scratch_database,
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid IN ('certificates'::regclass, 'certificate_generations'::regclass) "
            "AND contype = 'c'",
        )
    }
    certificate_check = next(text for name, text in checks.items() if name.endswith("status_valid"))
    assert "'PENDING'" in certificate_check and "'ISSUED'" in certificate_check

    generation_check = next(text for name, text in checks.items() if name.endswith("state_valid"))
    for state in ("PENDING", "ORDERING", "CHALLENGE_PUBLISHED", "VALIDATING", "FAILED"):
        assert f"'{state}'" in generation_check
    # An issued (or any material-bearing) generation is unrepresentable here.
    for absent in ("ISSUED", "SUPERSEDED", "SUSPENDED", "REVOKED", "REVOKED_LOCAL_ONLY"):
        assert f"'{absent}'" not in generation_check

    for override in (
        {"status": "BOGUS"},
        # http-01 is not offered in v1 and has no value to write.
        {"challenge_type": "http-01"},
        # The key algorithm is fixed by the platform, never chosen.
        {"key_algorithm": "rsa-2048"},
        # ``sans`` must be a JSON array, not merely valid JSON.
        {"sans": {"not": "an array"}},
    ):
        with pytest.raises(psycopg.errors.IntegrityError):
            _insert_certificate(
                scratch_database,
                certificate_id=str(uuid.uuid4()),
                primary_cn="invalid.example.com",
                **override,  # type: ignore[arg-type]
            )

    # Too many identifiers is refused by the shape constraint rather than stored.
    with pytest.raises(psycopg.errors.IntegrityError):
        _insert_certificate(
            scratch_database,
            certificate_id=str(uuid.uuid4()),
            primary_cn="too-many.example.com",
            sans=["san.example.com"] * 101,
        )


def test_an_issued_generation_is_rejected_and_a_pre_issuance_one_is_not(
    scratch_database: str,
) -> None:
    _migrate_from_phase4(scratch_database)
    certificate_id = str(uuid.uuid4())
    _insert_certificate(scratch_database, certificate_id=certificate_id, primary_cn=DOMAIN_NAME)

    # Every state this phase can hold is writable...
    for index, state in enumerate(("PENDING", "FAILED"), start=1):
        _insert_generation(
            scratch_database, certificate_id=certificate_id, generation=index, state=state
        )
    # ...and no state that implies material is.
    for state in ("ISSUED", "SUPERSEDED", "EXPIRED", "REVOKED_LOCAL_ONLY"):
        _integrity_error(
            scratch_database,
            [
                (
                    "INSERT INTO certificate_generations "
                    "(id, org_id, certificate_id, generation, state, order_state, last_error, "
                    " attempt_count) "
                    "VALUES (%s, %s, %s, 90, %s, '{}', '', 0)",
                    (str(uuid.uuid4()), ORG, certificate_id, state),
                )
            ],
        )


def test_the_uniqueness_semantics_are_constraints(scratch_database: str) -> None:
    _migrate_from_phase4(scratch_database)
    first = str(uuid.uuid4())
    _insert_certificate(scratch_database, certificate_id=first, primary_cn=DOMAIN_NAME)
    _insert_generation(scratch_database, certificate_id=first, generation=1)

    # One certificate row per name per organization...
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO certificates "
                "(id, org_id, domain_id, primary_cn, sans, status, challenge_type, auto_renew, "
                " key_algorithm, last_error) "
                "VALUES (%s, %s, %s, %s, '[]', 'PENDING', 'dns-01', true, 'ecdsa-p256', '')",
                (str(uuid.uuid4()), ORG, DOMAIN, DOMAIN_NAME),
            )
        ],
    )
    # ...while another organization may request the same name for its own domain
    # row — uniqueness is per organization, and the platform-wide rule on the
    # *name* is the domain table's verified-name index, not this one.
    _insert_certificate(
        scratch_database,
        certificate_id=str(uuid.uuid4()),
        primary_cn=DOMAIN_NAME,
        domain_id=OTHER_DOMAIN,
        org_id=OTHER_ORG,
    )

    # At most one in-flight generation per certificate; a retry is still allowed.
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO certificate_generations "
                "(id, org_id, certificate_id, generation, state, order_state, last_error, "
                " attempt_count) "
                "VALUES (%s, %s, %s, 2, 'VALIDATING', '{}', '', 0)",
                (str(uuid.uuid4()), ORG, first),
            )
        ],
    )
    _insert_generation(scratch_database, certificate_id=first, generation=2, state="FAILED")

    # ...but a generation number is unique per certificate, whatever its state.
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO certificate_generations "
                "(id, org_id, certificate_id, generation, state, order_state, last_error, "
                " attempt_count) "
                "VALUES (%s, %s, %s, 2, 'FAILED', '{}', '', 0)",
                (str(uuid.uuid4()), ORG, first),
            )
        ],
    )
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO certificate_generations "
                "(id, org_id, certificate_id, generation, state, order_state, last_error, "
                " attempt_count) "
                "VALUES (%s, %s, %s, 0, 'PENDING', '{}', '', 0)",
                (str(uuid.uuid4()), ORG, first),
            )
        ],
    )
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO certificate_generations "
                "(id, org_id, certificate_id, generation, state, order_state, last_error, "
                " attempt_count) "
                "VALUES (%s, %s, %s, 3, 'PENDING', '{}', '', -1)",
                (str(uuid.uuid4()), ORG, first),
            )
        ],
    )


def test_the_indexes_and_foreign_keys_are_the_specified_ones(scratch_database: str) -> None:
    _migrate_from_phase4(scratch_database)

    certificate_indexes = _indexes(scratch_database, "certificates")
    for expected in (
        "ix_certificates_org_id",
        "ix_certificates_created_at",
        "ix_certificates_domain_id",
        "ix_certificates_org_status",
        "ix_certificates_expiry_sweep",
        "uq_certificates_org_cn",
    ):
        assert expected in certificate_indexes, expected

    generation_indexes = _indexes(scratch_database, "certificate_generations")
    for expected in (
        "ix_certificate_generations_org_id",
        "ix_certificate_generations_created_at",
        "ix_certificate_generations_sweep",
        "uq_certificate_generations_cert_number",
        "uq_cert_generations_one_live",
    ):
        assert expected in generation_indexes, expected

    # The one-live index is partial: it covers the in-flight states and no others.
    live = generation_indexes["uq_cert_generations_one_live"]
    assert "UNIQUE" in live
    assert "(certificate_id)" in live
    for state in ("PENDING", "ORDERING", "CHALLENGE_PUBLISHED", "VALIDATING"):
        assert f"'{state}'" in live
    assert "'FAILED'" not in live

    assert _foreign_keys(scratch_database, "certificates") == {
        "fk_certificates_org_id_organizations": ("organizations", "c"),
        # RESTRICT: a certificate is issued for a name, so the name cannot be
        # dropped while one exists.
        "fk_certificates_domain_id_domains": ("domains", "r"),
        # SET NULL: the pointer is optional and must never dangle.
        "fk_certificates_current_generation_id_certificate_generations": (
            "certificate_generations",
            "n",
        ),
    }
    assert _foreign_keys(scratch_database, "certificate_generations") == {
        "fk_certificate_generations_org_id_organizations": ("organizations", "c"),
        "fk_certificate_generations_certificate_id_certificates": ("certificates", "c"),
    }


def test_the_certificate_generation_pointer_resolves_and_is_released(
    scratch_database: str,
) -> None:
    """The mutual reference is safe: it is nullable, and it clears rather than dangles."""
    _migrate_from_phase4(scratch_database)
    certificate_id = str(uuid.uuid4())
    _insert_certificate(scratch_database, certificate_id=certificate_id, primary_cn=DOMAIN_NAME)
    generation_id = _insert_generation(
        scratch_database, certificate_id=certificate_id, generation=1
    )
    _exec(
        scratch_database,
        [
            (
                "UPDATE certificates SET current_generation_id = %s WHERE id = %s",
                (generation_id, certificate_id),
            )
        ],
    )
    assert _rows(
        scratch_database,
        "SELECT current_generation_id FROM certificates WHERE id = %s",
        (certificate_id,),
    ) == [(uuid.UUID(generation_id),)]

    # A pointer at nothing is refused by the FK rather than stored.
    _integrity_error(
        scratch_database,
        [
            (
                "UPDATE certificates SET current_generation_id = %s WHERE id = %s",
                (str(uuid.uuid4()), certificate_id),
            )
        ],
    )

    # Removing the generation releases the pointer instead of breaking the row.
    _exec(
        scratch_database,
        [("DELETE FROM certificate_generations WHERE id = %s", (generation_id,))],
    )
    assert _rows(
        scratch_database,
        "SELECT current_generation_id FROM certificates WHERE id = %s",
        (certificate_id,),
    ) == [(None,)]

    # Deleting the certificate takes its generations with it (CASCADE).
    _insert_generation(scratch_database, certificate_id=certificate_id, generation=1)
    _exec(scratch_database, [("DELETE FROM certificates WHERE id = %s", (certificate_id,))])
    assert _rows(
        scratch_database,
        "SELECT count(*) FROM certificate_generations WHERE certificate_id = %s",
        (certificate_id,),
    ) == [(0,)]


def test_a_domain_with_a_certificate_cannot_be_deleted(scratch_database: str) -> None:
    _migrate_from_phase4(scratch_database)
    _insert_certificate(scratch_database, certificate_id=str(uuid.uuid4()), primary_cn=DOMAIN_NAME)

    _integrity_error(
        scratch_database,
        [("DELETE FROM domains WHERE id = %s", (DOMAIN,))],
    )
    # The route pointing at the same domain is a separate rule and still holds.
    assert _rows(scratch_database, "SELECT count(*) FROM domains WHERE id = %s", (DOMAIN,)) == [
        (1,)
    ]


def test_the_new_tables_are_tenant_tables(scratch_database: str) -> None:
    _migrate_from_phase4(scratch_database)

    rows = _rows(
        scratch_database,
        "SELECT relname, relrowsecurity FROM pg_class "
        "WHERE relkind = 'r' AND relname IN ('certificates', 'certificate_generations') "
        "ORDER BY relname",
    )
    assert rows == [("certificate_generations", True), ("certificates", True)]

    policies = _rows(
        scratch_database,
        "SELECT tablename, policyname FROM pg_policies "
        "WHERE tablename IN ('certificates', 'certificate_generations') "
        "ORDER BY tablename, policyname",
    )
    assert [tuple(row) for row in policies] == [
        ("certificate_generations", "certificate_generations_system"),
        ("certificate_generations", "certificate_generations_tenant"),
        ("certificates", "certificates_system"),
        ("certificates", "certificates_tenant"),
    ]


# --- 3. the codenames the slice introduces --------------------------------------


def test_the_codenames_and_their_grants_land_with_the_migration(
    scratch_database: str,
) -> None:
    """The registry is code, but stored grants are data: they arrive here.

    The rows are seeded explicitly rather than relying on ``scripts/seed.py``,
    which skips an instance that already has users — so without this migration an
    existing deployment would ship the endpoints with no role able to reach them.
    """
    _run_migration(scratch_database, PRE_PHASE5_REVISION)
    _exec(
        scratch_database,
        [
            (
                'INSERT INTO permissions (id, codename, description, "group", created_at, '
                "updated_at) VALUES "
                "(gen_random_uuid(), 'domain.read', 'x', 'Domains', now(), now()), "
                "(gen_random_uuid(), 'domain.manage', 'x', 'Domains', now(), now())",
                (),
            ),
            (
                "INSERT INTO roles (id, name, description, is_system, created_at, updated_at) "
                "VALUES "
                "(gen_random_uuid(), 'Owner', 'Owner (system)', true, now(), now()), "
                "(gen_random_uuid(), 'Admin', 'Admin (system)', true, now(), now()), "
                "(gen_random_uuid(), 'Operator', 'Operator (system)', true, now(), now()), "
                "(gen_random_uuid(), 'Developer', 'Developer (system)', true, now(), now()), "
                "(gen_random_uuid(), 'Viewer', 'Viewer (system)', true, now(), now())",
                (),
            ),
        ],
    )
    _run_migration(scratch_database, "head")

    codenames = {
        str(row[0])
        for row in _rows(
            scratch_database,
            "SELECT codename FROM permissions "
            "WHERE codename IN ('certificate.read', 'certificate.manage')",
        )
    }
    assert codenames == set(PERMISSION_CODENAMES)
    assert _permission_grants(scratch_database) == EXPECTED_GRANTS

    # The Owner holds the wildcard, so it needs no rows — and the migration must
    # not invent one, because a wildcard grant stored as an explicit list would
    # silently stop covering codenames added later.
    assert "Owner" not in _permission_grants(scratch_database)


# --- 4. reversibility -----------------------------------------------------------


def test_the_migration_is_reversible_and_reappliable(scratch_database: str) -> None:
    """Downgrade removes what the upgrade added; a second upgrade restores it."""
    _run_migration(scratch_database, PRE_PHASE5_REVISION)
    _seed_phase4(scratch_database)
    _exec(
        scratch_database,
        [
            (
                'INSERT INTO permissions (id, codename, description, "group", created_at, '
                "updated_at) VALUES "
                "(gen_random_uuid(), 'domain.read', 'x', 'Domains', now(), now())",
                (),
            ),
            (
                "INSERT INTO roles (id, name, description, is_system, created_at, updated_at) "
                "VALUES (gen_random_uuid(), 'Operator', 'Operator (system)', true, now(), now())",
                (),
            ),
        ],
    )

    _run_migration(scratch_database, PHASE5_REVISION)
    assert {"certificates", "certificate_generations"} <= _tables(scratch_database)
    _insert_certificate(scratch_database, certificate_id=str(uuid.uuid4()), primary_cn=DOMAIN_NAME)

    _run_downgrade(scratch_database, PRE_PHASE5_REVISION)
    tables = _tables(scratch_database)
    assert "certificates" not in tables
    assert "certificate_generations" not in tables
    # The codenames go with the schema they belong to...
    assert _rows(
        scratch_database,
        "SELECT count(*) FROM permissions "
        "WHERE codename IN ('certificate.read', 'certificate.manage')",
    ) == [(0,)]
    assert _permission_grants(scratch_database) == {}
    # ...the permissions the slice did not introduce are untouched...
    assert _rows(scratch_database, "SELECT codename FROM permissions ORDER BY codename") == [
        ("domain.read",)
    ]
    # ...and the pre-existing rows are exactly as they were.
    assert _rows(
        scratch_database,
        "SELECT name, status FROM domains WHERE id = %s",
        (DOMAIN,),
    ) == [(DOMAIN_NAME, "VERIFIED")]
    assert _rows(
        scratch_database,
        "SELECT hostname, path, enabled FROM routes WHERE id = %s",
        (ROUTE,),
    ) == [(HOSTNAME, "/", True)]
    assert _rows(
        scratch_database,
        "SELECT r.name FROM roles r ORDER BY r.name",
    ) == [("Operator",)]

    _run_migration(scratch_database, PHASE5_REVISION)
    assert {"certificates", "certificate_generations"} <= _tables(scratch_database)
    assert _columns(scratch_database, "certificates") == {
        "id",
        "org_id",
        "domain_id",
        "primary_cn",
        "sans",
        "status",
        "current_generation_id",
        "challenge_type",
        "auto_renew",
        "key_algorithm",
        "expires_at",
        "last_error",
        "created_at",
        "updated_at",
    }
    # Re-created empty, by design: the requests a downgrade discarded cannot be
    # reconstructed, and inventing them would be worse than losing them.
    assert _rows(scratch_database, "SELECT count(*) FROM certificates") == [(0,)]
    assert _rows(
        scratch_database,
        "SELECT relrowsecurity FROM pg_class WHERE relname = 'certificates'",
    ) == [(True,)]


def test_the_phase5_revision_extends_the_phase4_chain() -> None:
    """Exactly one head, and Phase 5.1 sits directly on the Phase 4.2 head."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert heads == [PHASE5_REVISION], f"unexpected alembic heads: {heads}"
    revision = script.get_revision(PHASE5_REVISION)
    assert revision.down_revision == PRE_PHASE5_REVISION
