"""Phase 3 migration (``a1b2c3d4e5f6``) against realistic legacy data.

Phase 3 is mostly additive, but two of its changes touch rows that already
exist, so ``upgrade head`` succeeding proves nothing on its own:

* ``servers.capabilities`` is added NOT NULL. It is backfilled with ``{}`` —
  the *unreported* state — deliberately, because dispatch treats an empty map as
  unverified and a fabricated empty object must never read as "has every
  capability".
* ``operations`` gains ``available_until`` (queue deadline) and
  ``execution_deadline`` (post-claim). Existing rows predate the split, so their
  original single ``expires_at`` is carried across as ``available_until`` —
  nothing is silently extended, and no operation becomes executable forever.

This module builds its own scratch databases, seeds the pre-Phase-3 shapes a real
instance would have (nodes, docker connection, containers, metric history,
operations), runs the migration through Alembic's own ``upgrade``, and checks
that the data survived and that the new RLS/unique constraints are in place.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest
from alembic.script import ScriptDirectory

from .test_migration_phase2 import (
    _alembic_config,
    _exec,
    _rows,
    _run_migration,
)

pytestmark = pytest.mark.integration

#: The revision immediately before Phase 3 — the environment-type precedence fix
#: (Phase 2.2). A production instance upgrading to Phase 3 starts here.
PRE_PHASE3_REVISION = "e5f6a7b8c9d0"
PHASE3_REVISION = "a1b2c3d4e5f6"

ORG = "33333333-3333-3333-3333-333333333333"
NODE = "33333333-0000-0000-0000-00000000000a"
NODE_OTHER = "33333333-0000-0000-0000-00000000000b"
HOST = "33333333-0000-0000-0000-0000000000f0"
CONTAINER = "33333333-0000-0000-0000-0000000000c1"
#: A queued operation whose single legacy deadline has not passed yet.
OP_PENDING = "33333333-0000-0000-0000-0000000000a1"
OP_DONE = "33333333-0000-0000-0000-00000000000d"


def _seed_legacy(database: str) -> None:
    """The pre-Phase-3 shapes: a node with telemetry, and operation history."""
    _exec(
        database,
        [
            # Two nodes so the new UNIQUE(docker_hosts.server_id) is meaningful.
            (
                "INSERT INTO organizations "
                "(id, name, slug, description, status, is_provisional) "
                "VALUES (%s, 'Acme', 'acme', '', 'ACTIVE', false)",
                (ORG,),
            ),
            (
                "INSERT INTO servers "
                "(id, name, hostname, ip_address, os_name, os_version, arch, environment, "
                " location, description, status, cpu_cores, memory_total_mb, disk_total_gb, "
                " agent_version, heartbeat_interval_seconds, uptime_seconds, simulated, extra, org_id) "
                "VALUES "
                "(%s, 'web-01', 'web01.internal', '10.0.0.11', 'Ubuntu', '24.04', 'x86_64', "
                " 'production', '', '', 'ONLINE', 8, 16384, 512, '1.0.0', 30, 864000, false, '{}', %s), "
                "(%s, 'web-02', 'web02.internal', '10.0.0.12', 'Ubuntu', '24.04', 'x86_64', "
                " 'production', '', '', 'ONLINE', 4, 8192, 256, '1.0.0', 30, 3600, false, '{}', %s)",
                (NODE, ORG, NODE_OTHER, ORG),
            ),
            (
                "INSERT INTO docker_hosts "
                "(id, server_id, name, endpoint_url, tls_verify, status, last_error, org_id) "
                "VALUES (%s, %s, 'agent', 'agent://web-01', false, 'OK', '', %s)",
                (HOST, NODE, ORG),
            ),
            (
                "INSERT INTO containers "
                "(id, docker_host_id, server_id, container_id, name, image_ref, command, status, "
                " health, ports, env_keys, labels, mounts, restart_count, observed_at, simulated, org_id) "
                "VALUES (%s, %s, %s, 'ab12cd34ef56', 'api', 'ghcr.io/acme/api:1.0.0', '', 'RUNNING', "
                " 'NONE', '[]', '[]', '{}', '[]', 0, now(), false, %s)",
                (CONTAINER, HOST, NODE, ORG),
            ),
            (
                "INSERT INTO metric_snapshots "
                "(server_id, granularity, recorded_at, cpu_percent, mem_used_mb, mem_percent, "
                " disk_used_gb, disk_percent, net_rx_kb_s, net_tx_kb_s, load1, uptime_seconds, extra, org_id) "
                "VALUES (%s, 'RAW', now(), 12.5, 4096.2, 25.0, 128.4, 25.1, 812.4, 233.1, 0.42, 864000, '{}', %s)",
                (NODE, ORG),
            ),
            (
                # A queued op and a finished op — both must survive the split.
                "INSERT INTO operations "
                "(id, org_id, node_id, type, status, params, result, expires_at) "
                "VALUES "
                "(%s, %s, %s, 'logs.tail', 'PENDING', '{\"container_id\": \"ab12cd34ef56\"}', NULL, "
                " now() + interval '90 seconds'), "
                "(%s, %s, %s, 'container.restart', 'SUCCEEDED', '{\"container_id\": \"ab12cd34ef56\"}', "
                " '{\"status\": \"RUNNING\"}', now() - interval '5 minutes')",
                (OP_PENDING, ORG, NODE, OP_DONE, ORG, NODE),
            ),
        ],
    )


def test_upgrade_preserves_existing_nodes_containers_metrics_and_operations(
    scratch_database: str,
) -> None:
    _run_migration(scratch_database, PRE_PHASE3_REVISION)
    _seed_legacy(scratch_database)
    _run_migration(scratch_database, "head")

    # --- nodes are preserved, not renamed or duplicated ----------------------
    nodes = _rows(
        scratch_database,
        "SELECT id, name, agent_version, status, protocol_version, capabilities, "
        " credential_revoked_at FROM servers ORDER BY name",
    )
    assert [(str(r[0]), r[1], r[2], r[3]) for r in nodes] == [
        (NODE, "web-01", "1.0.0", "ONLINE"),
        (NODE_OTHER, "web-02", "1.0.0", "ONLINE"),
    ], nodes
    for row in nodes:
        # A pre-v2 node reports nothing: NULL protocol (== protocol 1) and an
        # EMPTY capability map (unreported), never a populated lie.
        assert row[4] is None, "an un-upgraded agent must not be assumed protocol 2"
        assert row[5] == {}, "capabilities backfills to the unreported empty map"
        assert row[6] is None, "no credential was revoked by the migration"

    # --- containers and metric history are untouched -------------------------
    containers = _rows(scratch_database, "SELECT name, status FROM containers")
    assert containers == [("api", "RUNNING")], containers
    metrics = _rows(scratch_database, "SELECT cpu_percent, net_rx_kb_s FROM metric_snapshots")
    assert metrics == [(12.5, 812.4)], metrics

    # --- operations: the old deadline becomes the queue deadline -------------
    ops = _rows(
        scratch_database,
        "SELECT id, status, available_until, execution_deadline, expires_at "
        "FROM operations ORDER BY created_at",
    )
    by_id = {str(row[0]): row for row in ops}
    pending = by_id[OP_PENDING]
    assert pending[1] == "PENDING"
    assert pending[2] is not None, "available_until is backfilled for legacy rows"
    assert pending[2] == pending[4], "available_until carries the original expires_at"
    assert pending[3] is None, "no execution clock opens until a row is claimed"

    done = by_id[OP_DONE]
    assert done[1] == "SUCCEEDED"
    assert done[2] == done[4], "a terminal row keeps its original deadline as the queue bound"


def test_new_constraints_and_rls_are_in_place(scratch_database: str) -> None:
    _run_migration(scratch_database, PRE_PHASE3_REVISION)
    _seed_legacy(scratch_database)
    _run_migration(scratch_database, "head")

    # One docker connection per node — a second row for the same server fails.
    with pytest.raises(psycopg.errors.UniqueViolation):
        _exec(
            scratch_database,
            [
                (
                    "INSERT INTO docker_hosts "
                    "(id, server_id, name, endpoint_url, tls_verify, status, last_error, org_id) "
                    "VALUES (%s, %s, 'manual', 'tcp://10.0.0.9:2375', false, 'OK', '', %s)",
                    (uuid.uuid4(), NODE, ORG),
                )
            ],
        )

    # enrollment_tokens is tenant-owned and RLS-covered like every other table.
    policies = {
        row[0]
        for row in _rows(
            scratch_database,
            "SELECT polname FROM pg_policy WHERE polrelid = 'enrollment_tokens'::regclass",
        )
    }
    assert {"enrollment_tokens_tenant", "enrollment_tokens_system"} <= policies
    assert _rows(
        scratch_database,
        "SELECT relrowsecurity FROM pg_class WHERE relname = 'enrollment_tokens'",
    ) == [(True,)]

    # The unique hash is enforced by the database, not only in code.
    with pytest.raises(psycopg.errors.UniqueViolation):
        _exec(
            scratch_database,
            [
                (
                    "INSERT INTO enrollment_tokens "
                    "(id, org_id, name, token_hash, single_use, expires_at, note, created_at, updated_at) "
                    "VALUES (%s, %s, '', 'deadbeef', true, now() + interval '1 hour', '', now(), now()), "
                    "(%s, %s, '', 'deadbeef', true, now() + interval '1 hour', '', now(), now())",
                    (uuid.uuid4(), ORG, uuid.uuid4(), ORG),
                )
            ],
        )


def test_migration_from_zero_adds_the_phase3_shape(scratch_database: str) -> None:
    """A fresh database reaches the same shape the models describe."""
    _run_migration(scratch_database, "head")

    columns = {
        (row[0], row[1])
        for row in _rows(
            scratch_database,
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'public'",
        )
    }
    assert ("enrollment_tokens", "token_hash") in columns
    assert ("servers", "capabilities") in columns
    assert ("servers", "protocol_version") in columns
    assert ("servers", "credential_revoked_at") in columns
    assert ("agent_credentials", "previous_token_hash") in columns
    assert ("agent_credentials", "previous_expires_at") in columns
    assert ("agent_credentials", "pending_token_ciphertext") in columns
    assert ("operations", "available_until") in columns
    assert ("operations", "execution_deadline") in columns

    # The one-docker-connection-per-node constraint is present from zero too.
    constraints = {
        row[0]
        for row in _rows(
            scratch_database,
            "SELECT conname FROM pg_constraint WHERE conrelid = 'docker_hosts'::regclass",
        )
    }
    assert "uq_docker_hosts_server_id" in constraints


def test_exactly_one_alembic_head() -> None:
    """Phase 3 adds one migration; heads must not fork."""
    script = ScriptDirectory.from_config(_alembic_config("postgres"))
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple alembic heads: {heads}"
    # And the Phase 3 revision is reachable, i.e. actually applied by `head` —
    # later phases extend the chain from here rather than replacing it.
    assert any(rev.revision == PHASE3_REVISION for rev in script.walk_revisions("base", "heads"))
