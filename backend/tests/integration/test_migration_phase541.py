"""Phase 5.4.1 migration — the association column, its tenant key, its refusal.

Three facts matter here and none of them follows from ``upgrade head`` succeeding
on the already-migrated test database:

1. the column, the composite FK and the referenced unique key are created on a
   database that was at the previous revision;
2. the FK is ``ON DELETE RESTRICT`` and *composite* — a bare ``certificate_id``
   key would not prove tenant consistency;
3. the downgrade refuses while a route is bound (dropping the column would erase
   associations silently) and succeeds once they are cleared.

The scratch database is the same fixture the other migration suites use, so this
exercises Alembic's own upgrade/downgrade path.
"""

from __future__ import annotations

import asyncio

import psycopg
import pytest
from app.models import Certificate, Domain, Organization, Route, Server
from app.models.enums import CertificateStatus, DomainStatus, OrganizationStatus
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tests.integration.test_migration_phase2 import (
    _migration_dsn,
    _owner_dsn,
    _rows,
    _run_downgrade,
    _run_migration,
)

pytestmark = pytest.mark.integration

PREVIOUS = "d0e1f2a3b4c5"
HEAD = "e1f2a3b4c5d6"


def _seed_bound_route(database: str) -> None:
    """One organization, one route bound to one certificate — via the models."""

    async def run() -> None:
        engine = create_async_engine(_migration_dsn(database))
        try:
            maker = async_sessionmaker(engine, expire_on_commit=False)
            async with maker() as session:
                org = Organization(
                    name="Migration Org",
                    slug="migration-org",
                    description="",
                    status=OrganizationStatus.ACTIVE,
                    is_provisional=False,
                )
                session.add(org)
                await session.flush()
                domain = Domain(
                    org_id=org.id,
                    name="migration.example.com",
                    status=DomainStatus.PENDING,
                    verification_token="t" * 32,
                )
                node = Server(
                    org_id=org.id, name="migration-node", hostname="migration.integration.test"
                )
                session.add_all([domain, node])
                await session.flush()
                certificate = Certificate(
                    org_id=org.id,
                    domain_id=domain.id,
                    primary_cn=domain.name,
                    status=CertificateStatus.PENDING,
                )
                route = Route(
                    org_id=org.id,
                    domain_id=domain.id,
                    hostname=domain.name,
                    path="/",
                    node_id=node.id,
                    port=8081,
                    enabled=False,
                )
                session.add_all([certificate, route])
                await session.flush()
                route.certificate_id = certificate.id
                await session.commit()
        finally:
            await engine.dispose()

    asyncio.run(run())


def _clear_bindings(database: str) -> None:
    with psycopg.connect(_owner_dsn(database)) as conn:
        conn.execute("UPDATE routes SET certificate_id = NULL")


def _column(database: str) -> list[tuple[object, ...]]:
    return _rows(
        database,
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name = 'routes' AND column_name = 'certificate_id'",
    )


def _fk(database: str) -> list[tuple[object, ...]]:
    """The composite key's columns and its delete action, straight from the catalog."""
    return _rows(
        database,
        """
        SELECT array_agg(a.attname ORDER BY k.ord)::text[], c.confdeltype
          FROM pg_constraint c
          JOIN unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
          JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
         WHERE c.conname = 'fk_routes_certificate_org'
         GROUP BY c.confdeltype
        """,
    )


def test_upgrade_adds_the_column_key_and_restrict_fk(scratch_database):
    _run_migration(scratch_database, PREVIOUS)
    with psycopg.connect(_owner_dsn(scratch_database)) as conn:
        assert not conn.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'routes' AND column_name = 'certificate_id'"
        ).fetchall()

    _run_migration(scratch_database, HEAD)

    assert _column(scratch_database) == [("YES",)]
    assert _fk(scratch_database) == [(["certificate_id", "org_id"], "r")]
    assert _rows(
        scratch_database,
        "SELECT conname FROM pg_constraint WHERE conname = 'uq_certificates_id_org'",
    )
    assert _rows(
        scratch_database,
        "SELECT indexname FROM pg_indexes WHERE indexname = 'ix_routes_certificate_id'",
    )


def test_downgrade_refuses_while_a_route_is_bound(scratch_database):
    _run_migration(scratch_database, HEAD)
    _seed_bound_route(scratch_database)

    with pytest.raises(DBAPIError) as refusal:
        _run_downgrade(scratch_database, PREVIOUS)
    assert "refusing to downgrade past 5.4.1" in str(refusal.value)

    # The refused migration left the schema and the row intact.
    assert _column(scratch_database) == [("YES",)]
    assert _rows(
        scratch_database, "SELECT certificate_id FROM routes WHERE certificate_id IS NOT NULL"
    )


def test_downgrade_removes_the_association_once_unbound(scratch_database):
    _run_migration(scratch_database, HEAD)
    _seed_bound_route(scratch_database)
    _clear_bindings(scratch_database)

    _run_downgrade(scratch_database, PREVIOUS)

    assert _column(scratch_database) == []
    assert _fk(scratch_database) == []
    assert not _rows(
        scratch_database,
        "SELECT conname FROM pg_constraint WHERE conname = 'uq_certificates_id_org'",
    )
    assert not _rows(
        scratch_database,
        "SELECT indexname FROM pg_indexes WHERE indexname = 'ix_routes_certificate_id'",
    )
