"""The docker-host maintenance sweep must actually reach real hosts."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.tenancy import apply_scope_to_session, org_scope
from sqlalchemy import select

pytestmark = pytest.mark.integration


async def test_collect_recent_logs_is_incremental(org_db, monkeypatch):
    """Re-collection stores only lines newer than the newest stored row.

    The sweep re-reads the same docker tail every cycle; without the cutoff
    each pass duplicates the tail into the database until the row cap trims it.
    """
    from app.models import Container, DockerHost, LogEntry
    from app.providers.base import LogLine
    from app.services import container_service
    from sqlalchemy import func, select

    host = DockerHost(name="sim-collect", endpoint_url="sim://collect-test")
    org_db.add(host)
    await org_db.flush()
    row = Container(
        docker_host_id=host.id,
        container_id="abc123def456",
        name="web",
        status="RUNNING",
        observed_at=datetime.now(UTC),
    )
    org_db.add(row)
    await org_db.commit()

    base = datetime.now(UTC).replace(microsecond=0) - timedelta(minutes=5)
    lines = [
        LogLine(ts=base, stream="stdout", message="line-1"),
        LogLine(ts=base + timedelta(seconds=1), stream="stdout", message="line-2"),
    ]

    class FakeProvider:
        def logs(self, cid: str, tail: int = 100, follow: bool = False):
            return iter(lines)

    monkeypatch.setattr(container_service, "provider_for", lambda _host: FakeProvider())
    monkeypatch.setattr(container_service, "is_simulated", lambda _provider: False)

    stored = await container_service.collect_recent_logs(org_db, host)
    assert stored == 2

    # Same tail again: nothing new, nothing duplicated.
    stored = await container_service.collect_recent_logs(org_db, host)
    assert stored == 0

    total = await org_db.scalar(
        select(func.count()).select_from(LogEntry).where(LogEntry.container_id == row.id)
    )
    assert total == 2

    # A genuinely newer line is picked up on the next pass.
    lines.append(LogLine(ts=base + timedelta(seconds=2), stream="stdout", message="line-3"))
    stored = await container_service.collect_recent_logs(org_db, host)
    assert stored == 1


async def test_sweep_syncs_real_hosts_without_loop_errors(client, owner):
    """Regression: the sweep called asyncio.run() inside its own running loop,
    so every real-host sync failed with 'cannot be called from a running event
    loop' — masked while the only registered host was agent-backed, because
    provider_for() rejected it earlier in the loop."""
    from app.core.db import dispose_engine, get_sessionmaker
    from app.models import DockerHost

    # The sweep is cross-tenant and builds its own session; the row it must find
    # is created here with an explicit owner, like any real host has.
    org_id = uuid.UUID(owner["active_organization_id"])
    async with get_sessionmaker()() as setup:
        with org_scope(org_id):
            await apply_scope_to_session(setup)
            setup.add(DockerHost(name="sim-host", endpoint_url="sim://sweep-test"))
            await setup.commit()

    # The celery task builds its own event loop in a worker thread; drop pooled
    # connections first so it never touches a connection bound to this loop.
    await dispose_engine()
    try:
        from app.tasks.maintenance import sync_docker_hosts

        totals = await asyncio.to_thread(sync_docker_hosts)
    finally:
        await dispose_engine()

    assert totals["hosts"] >= 1
    assert totals["errors"] == 0


async def test_sweep_does_not_delete_agent_containers_on_simulated_hosts(owner, org_db):
    """Regression: sync_host_state listed the provider BEFORE registering the
    host's DB rows into the stateless simulated provider, so every sweep saw an
    empty listing, read all rows as "disappeared", and deleted them — including
    the agent-reported mirrors written by heartbeats. The simulated fleet only
    survived because simulation_tick re-created its own rows every cycle.
    """
    from app.core.tenancy import org_scope
    from app.models import Container, Server
    from app.schemas.agent import AgentContainerIn
    from app.services import container_service
    from app.services.server_service import ensure_docker_host, upsert_containers

    server = Server(name="srv-agent-mirror", hostname="mirror.test")
    org_db.add(server)
    await org_db.commit()
    host = await ensure_docker_host(org_db, server=server)
    await org_db.commit()
    with org_scope(uuid.UUID(owner["active_organization_id"])):
        await upsert_containers(
            org_db,
            server=server,
            entries=[
                AgentContainerIn(
                    container_id="agentweb001",
                    name="demo-web",
                    status="RUNNING",
                    image_ref="nginx:1.27",
                )
            ],
        )
        await org_db.commit()

        # The maintenance sweep's per-host reconciliation, as the task runs it
        # inside org_session(host.org_id).
        summary = await container_service.sync_host_state(org_db, host.id)
        await org_db.commit()

    rows = (
        (await org_db.execute(select(Container).where(Container.container_id == "agentweb001")))
        .scalars()
        .all()
    )
    assert len(rows) == 1, "the sweep deleted an agent-reported container"
    assert summary["removed"] == 0


async def test_staleness_sweep_alerts_carry_the_server_org(client, owner, org_db):
    """Regression: mark_stale_servers ran under the system scope and added Alert
    rows without org_id — the tenancy stamping handler only stamps in org scope,
    so every transition crashed the sweep with a NotNullViolation on
    alerts.org_id and servers never flipped OFFLINE again. Going through the
    celery task also covers its transition-iteration shape.
    """
    from datetime import timedelta

    from app.core.db import dispose_engine
    from app.models import Alert, Server
    from app.models.enums import ServerStatus

    server = Server(
        name="srv-stale",
        hostname="stale.test",
        status=ServerStatus.ONLINE,
        offline_after_seconds=30,
        last_heartbeat_at=datetime.now(UTC) - timedelta(seconds=120),
    )
    org_db.add(server)
    await org_db.commit()
    server_id = server.id

    # The task builds its own event loop and sessions; drop pooled connections
    # bound to this loop first (same ritual as the sweep test above).
    await dispose_engine()
    try:
        from app.tasks.heartbeat import sweep_servers

        await asyncio.to_thread(sweep_servers)
    finally:
        await dispose_engine()

    swept = await org_db.get(Server, server_id)
    assert swept is not None
    org_db.expire_all()
    swept = await org_db.get(Server, server_id)
    assert swept.status == ServerStatus.OFFLINE

    alerts = (
        (await org_db.execute(select(Alert).where(Alert.resource_id == str(server_id))))
        .scalars()
        .all()
    )
    assert len(alerts) == 1
    assert alerts[0].org_id == uuid.UUID(owner["active_organization_id"])
    assert alerts[0].event_type == "SERVER_OFFLINE"


async def test_heartbeat_adopts_container_inserted_concurrently(owner, org_db, monkeypatch):
    """The sweep and a heartbeat can both see a brand-new container in the same
    instant; the loser of the unique insert must adopt the winner's row instead
    of failing the whole heartbeat with a uq_containers_host_cid violation."""
    from app.core.db import get_sessionmaker
    from app.models import Container, Server
    from app.schemas.agent import AgentContainerIn
    from app.services.server_service import ensure_docker_host, upsert_containers

    server = Server(name="srv-race", hostname="race.test")
    org_db.add(server)
    await org_db.commit()
    host = await ensure_docker_host(org_db, server=server)
    await org_db.commit()

    # Injection point: the upsert's FIRST flush. By then it has already
    # SELECTed the host's rows (and seen no such container), so committing the
    # same (docker_host_id, container_id) from a concurrent session right here
    # reproduces the production race: the winner's row is committed between the
    # heartbeat's SELECT and its INSERT.
    real_flush = org_db.flush
    fired = False
    org_id = uuid.UUID(owner["active_organization_id"])

    async def racing_flush(*args, **kwargs):
        nonlocal fired
        if not fired:
            fired = True
            # A second connection — the sweep — winning the same unique insert.
            async with get_sessionmaker()() as other:
                with org_scope(org_id):
                    await apply_scope_to_session(other)
                    other.add(
                        Container(
                            docker_host_id=host.id,
                            container_id="abc123def456",
                            name="racer",
                            status="RUNNING",
                            observed_at=datetime.now(UTC),
                        )
                    )
                    await other.commit()
        return await real_flush(*args, **kwargs)

    monkeypatch.setattr(org_db, "flush", racing_flush)

    entry = AgentContainerIn(
        container_id="abc123def456",
        name="web",
        status="RUNNING",
        image_ref="nginx:1.27",
        restart_count=0,
    )
    await upsert_containers(org_db, server=server, entries=[entry])
    await org_db.commit()

    rows = (
        (await org_db.execute(select(Container).where(Container.container_id == "abc123def456")))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].name == "web"
