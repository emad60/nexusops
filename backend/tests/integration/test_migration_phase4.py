"""Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database.

Phase 4 is mostly additive, but it does touch three existing tables, and each of
those touches is a way an already-running instance could lose data or start
rejecting its own rows:

* ``monitors`` gains the polymorphic target columns. Every pre-existing row must
  come out ``URL`` with ``route_id IS NULL`` — the check history, incidents and
  notification associations hanging off those ids must be exactly as they were.
* ``servers`` gains ``proxy_state``, which must be backfilled to ``{}`` and made
  ``NOT NULL`` without the migration failing on a populated table.
* ``operations.type`` has its CHECK constraint dropped and recreated with the
  three ``nginx.*`` types appended. Existing rows must survive the swap, and the
  whitelist must still be closed afterwards.

The module also pins the two structural promises that make the routing design a
database fact rather than a convention: the verified-name partial unique index
and the HTTP-only ``scheme`` check. It runs Alembic's own ``upgrade`` against a
scratch database, so the code path is the one a deployment uses.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest

from .test_migration_phase2 import Statement, _exec, _rows, _run_migration

pytestmark = pytest.mark.integration

#: The Phase 3 head. Everything below is written in that schema.
PRE_PHASE4_REVISION = "a1b2c3d4e5f6"
#: This migration's own revision — the Phase 4 head.
PHASE4_REVISION = "f4a5b6c7d8e9"

ORG = "33333333-3333-3333-3333-333333333333"
OTHER_ORG = "44444444-4444-4444-4444-444444444444"
PROJECT = "aaaa3333-0000-0000-0000-000000000001"
NODE = "aaaa3333-0000-0000-0000-000000000002"
LEGACY_MONITOR = "aaaa3333-0000-0000-0000-000000000003"
LEGACY_OPERATION = "aaaa3333-0000-0000-0000-000000000004"

#: Fixed values the "untouched" assertions compare against after the migration.
MONITOR_URL = "http://legacy.example.com/health"
MONITOR_NEXT_CHECK = "2026-10-09T12:00:00+00:00"


def _seed_phase3(database: str) -> None:
    """A populated pre-Phase-4 instance: a node, a URL monitor, a live operation."""
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
            # A real node with an enrolled credential: the migration must not
            # disturb credentials or capabilities.
            "INSERT INTO servers "
            "(id, org_id, name, hostname, ip_address, os_name, os_version, arch, environment, "
            " location, description, status, cpu_cores, memory_total_mb, disk_total_gb, "
            " agent_version, heartbeat_interval_seconds, uptime_seconds, simulated, extra, "
            " protocol_version, capabilities) "
            "VALUES (%s, %s, 'node-legacy', 'node-legacy.example.com', '10.0.0.5', 'Ubuntu', "
            " '24.04', 'x86_64', 'PROD', '', '', 'ONLINE', 4, 8192, 200, '1.2.0', 30, 86400, "
            " false, '{}', 2, '{\"nginx\": {\"present\": true}}')",
            (NODE, ORG),
        ),
        (
            "INSERT INTO monitors "
            "(id, org_id, name, project_id, url, method, interval_seconds, timeout_seconds, "
            " expected_status, expected_body, headers, skip_tls_verify, follow_redirects, "
            " enabled, status, consecutive_failures, consecutive_successes, next_check_at, "
            " last_check_at, last_success_at, last_failure_at, failure_threshold, "
            " success_threshold, created_at, updated_at) "
            "VALUES (%s, %s, 'legacy probe', %s, %s, 'GET', 60, 10.0, 200, NULL, '{}', false, "
            " true, true, 'UP', 0, 3, %s, %s, %s, NULL, 3, 2, now(), now())",
            (
                LEGACY_MONITOR,
                ORG,
                PROJECT,
                MONITOR_URL,
                MONITOR_NEXT_CHECK,
                MONITOR_NEXT_CHECK,
                MONITOR_NEXT_CHECK,
            ),
        ),
        (
            "INSERT INTO monitor_checks (org_id, monitor_id, checked_at, result, "
            " response_time_ms, status_code, error) VALUES (%s, %s, %s, 'SUCCESS', 12.5, 200, '')",
            (ORG, LEGACY_MONITOR, MONITOR_NEXT_CHECK),
        ),
        (
            "INSERT INTO operations "
            "(id, org_id, node_id, type, status, params, available_until, expires_at, attempts) "
            "VALUES (%s, %s, %s, 'container.start', 'SUCCEEDED', '{}', "
            " '2026-10-09T12:00:00Z', '2026-10-09T12:05:00Z', 1)",
            (LEGACY_OPERATION, ORG, NODE),
        ),
    ]
    _exec(database, statements)


def _migrate_from_phase3(database: str) -> None:
    _run_migration(database, PRE_PHASE4_REVISION)
    _seed_phase3(database)
    _run_migration(database, "head")


def _integrity_error(database: str, statements: list[Statement]) -> None:
    with pytest.raises(psycopg.errors.IntegrityError):
        _exec(database, statements)


# --- 1. monitors -----------------------------------------------------------------


def test_existing_monitors_become_url_targets_with_history_intact(scratch_database: str) -> None:
    _migrate_from_phase3(scratch_database)

    rows = _rows(
        scratch_database,
        "SELECT id, url, next_check_at, target_type, route_id FROM monitors",
    )
    assert len(rows) == 1
    monitor_id, url, next_check, target_type, route_id = rows[0]
    assert str(monitor_id) == LEGACY_MONITOR
    assert url == MONITOR_URL
    assert str(next_check).startswith("2026-10-09 12:00:00")
    assert target_type == "URL"
    assert route_id is None

    # The check row still points at the same monitor: no id churn.
    checks = _rows(scratch_database, "SELECT monitor_id, result FROM monitor_checks")
    assert [(str(row[0]), row[1]) for row in checks] == [(LEGACY_MONITOR, "SUCCESS")]


def test_a_route_monitor_must_name_a_route(scratch_database: str) -> None:
    """The polymorphic shape is enforced in both directions."""
    _migrate_from_phase3(scratch_database)
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO monitors "
                "(id, org_id, name, url, method, interval_seconds, timeout_seconds, "
                " expected_status, expected_body, headers, skip_tls_verify, follow_redirects, "
                " enabled, status, consecutive_failures, consecutive_successes, next_check_at, "
                " failure_threshold, success_threshold, target_type, route_id) "
                "VALUES (%s, %s, 'route probe', 'http://route.example.com/', 'GET', 60, 10.0, "
                " 200, NULL, '{}', false, true, true, 'PENDING', 0, 0, now(), 3, 2, 'ROUTE', NULL)",
                (str(uuid.uuid4()), ORG),
            )
        ],
    )


# --- 2. operations ---------------------------------------------------------------


def test_existing_operations_survive_and_the_whitelist_stays_closed(
    scratch_database: str,
) -> None:
    _migrate_from_phase3(scratch_database)

    rows = _rows(scratch_database, "SELECT id, type, status FROM operations")
    assert [(str(row[0]), row[1], row[2]) for row in rows] == [
        (LEGACY_OPERATION, "container.start", "SUCCEEDED")
    ]

    # The three nginx types are now accepted...
    for op_type in ("nginx.bootstrap", "nginx.apply", "nginx.status"):
        _exec(
            scratch_database,
            [
                (
                    "INSERT INTO operations "
                    "(id, org_id, node_id, type, status, params, available_until, expires_at, "
                    " attempts) VALUES (%s, %s, %s, %s, 'PENDING', '{}', now() + interval '1 hour', "
                    " now() + interval '2 hours', 0)",
                    (str(uuid.uuid4()), ORG, NODE, op_type),
                )
            ],
        )

    # ...and nothing else is. A generic execute primitive never becomes a row.
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO operations "
                "(id, org_id, node_id, type, status, params, available_until, expires_at, attempts) "
                "VALUES (%s, %s, %s, 'node.exec', 'PENDING', '{}', now() + interval '1 hour', "
                " now() + interval '2 hours', 0)",
                (str(uuid.uuid4()), ORG, NODE),
            )
        ],
    )


# --- 3. servers ------------------------------------------------------------------


def test_servers_get_an_empty_proxy_state(scratch_database: str) -> None:
    _migrate_from_phase3(scratch_database)

    rows = _rows(
        scratch_database,
        "SELECT proxy_state, capabilities, protocol_version FROM servers",
    )
    assert rows == [({}, {"nginx": {"present": True}}, 2)]


# --- 4. the routing tables' structural promises ----------------------------------


def test_tenant_tables_carry_rls_policies(scratch_database: str) -> None:
    _migrate_from_phase3(scratch_database)

    rows = _rows(
        scratch_database,
        # relkind = 'r' excludes the pre-tenancy ``domains`` *view* that happens to
        # share the table's name.
        "SELECT relname, relrowsecurity FROM pg_class "
        "WHERE relkind = 'r' AND relname IN ('domains', 'routes') ORDER BY relname",
    )
    assert rows == [("domains", True), ("routes", True)]

    policies = _rows(
        scratch_database,
        "SELECT tablename, policyname FROM pg_policies "
        "WHERE tablename IN ('domains', 'routes') ORDER BY tablename, policyname",
    )
    assert policies == [
        ("domains", "domains_system"),
        ("domains", "domains_tenant"),
        ("routes", "routes_system"),
        ("routes", "routes_tenant"),
    ]


def test_only_one_organization_may_hold_a_verified_name(scratch_database: str) -> None:
    """The anti-takeover rule is a partial unique index, not a convention."""
    _migrate_from_phase3(scratch_database)

    def _domain(org: str, status: str) -> Statement:
        return (
            "INSERT INTO domains "
            "(id, org_id, name, status, verification_token, ns_snapshot, last_error, "
            " dns_reachability) "
            "VALUES (%s, %s, 'contested.example.com', %s, 'nxs-verify-token', '[]', '', '{}')",
            (str(uuid.uuid4()), org, status),
        )

    # Any number of organizations may *track* the name, verified or not...
    _exec(scratch_database, [_domain(ORG, "VERIFIED"), _domain(OTHER_ORG, "PENDING")])
    # ...but a second organization may not make its copy the verified one.
    _integrity_error(
        scratch_database,
        [
            (
                "UPDATE domains SET status = 'VERIFIED' WHERE org_id = %s",
                (OTHER_ORG,),
            )
        ],
    )


def test_routes_are_http_only(scratch_database: str) -> None:
    _migrate_from_phase3(scratch_database)
    _exec(
        scratch_database,
        [
            (
                "INSERT INTO domains "
                "(id, org_id, name, status, verification_token, ns_snapshot, last_error, "
                " dns_reachability) "
                "VALUES (%s, %s, 'http.example.com', 'VERIFIED', 'nxs-verify-token', '[]', '', "
                " '{}')",
                (str(uuid.uuid4()), ORG),
            )
        ],
    )
    domain_id = str(_rows(scratch_database, "SELECT id FROM domains")[0][0])

    # A plain http route is accepted...
    _exec(
        scratch_database,
        [
            (
                "INSERT INTO routes "
                "(id, org_id, domain_id, hostname, path, node_id, port, scheme, headers, enabled, "
                " config_state, monitor_optout, last_apply_error) "
                "VALUES (%s, %s, %s, 'http.example.com', '/', %s, 8080, 'http', '[]', false, "
                " 'PENDING', false, '')",
                (str(uuid.uuid4()), ORG, domain_id, NODE),
            )
        ],
    )

    # ...https is a Phase 5 migration, not a value anyone can write today.
    _integrity_error(
        scratch_database,
        [
            (
                "INSERT INTO routes "
                "(id, org_id, domain_id, hostname, path, node_id, port, scheme, headers, enabled, "
                " config_state, monitor_optout, last_apply_error) "
                "VALUES (%s, %s, %s, 'https.example.com', '/', %s, 8080, 'https', '[]', false, "
                " 'PENDING', false, '')",
                (str(uuid.uuid4()), ORG, domain_id, NODE),
            )
        ],
    )


def test_the_phase4_revision_is_in_the_chain_and_does_not_fork_it() -> None:
    """Phase 4 adds one migration; the chain still has exactly one head."""
    from alembic.script import ScriptDirectory

    from .test_migration_phase2 import _alembic_config

    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple alembic heads: {heads}"
    assert any(rev.revision == PHASE4_REVISION for rev in script.walk_revisions("base", "heads"))
