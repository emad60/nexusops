"""The docker-host maintenance sweep must actually reach real hosts."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.integration


async def test_collect_recent_logs_is_incremental(db, monkeypatch):
    """Re-collection stores only lines newer than the newest stored row.

    The sweep re-reads the same docker tail every cycle; without the cutoff
    each pass duplicates the tail into the database until the row cap trims it.
    """
    from app.models import Container, DockerHost, LogEntry
    from app.providers.base import LogLine
    from app.services import container_service
    from sqlalchemy import func, select

    host = DockerHost(name="sim-collect", endpoint_url="sim://collect-test")
    db.add(host)
    await db.flush()
    row = Container(
        docker_host_id=host.id,
        container_id="abc123def456",
        name="web",
        status="RUNNING",
        observed_at=datetime.now(UTC),
    )
    db.add(row)
    await db.commit()

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

    stored = await container_service.collect_recent_logs(db, host)
    assert stored == 2

    # Same tail again: nothing new, nothing duplicated.
    stored = await container_service.collect_recent_logs(db, host)
    assert stored == 0

    total = await db.scalar(
        select(func.count()).select_from(LogEntry).where(LogEntry.container_id == row.id)
    )
    assert total == 2

    # A genuinely newer line is picked up on the next pass.
    lines.append(LogLine(ts=base + timedelta(seconds=2), stream="stdout", message="line-3"))
    stored = await container_service.collect_recent_logs(db, host)
    assert stored == 1


async def test_sweep_syncs_real_hosts_without_loop_errors(db):
    """Regression: the sweep called asyncio.run() inside its own running loop,
    so every real-host sync failed with 'cannot be called from a running event
    loop' — masked while the only registered host was agent-backed, because
    provider_for() rejected it earlier in the loop."""
    from app.core.db import dispose_engine
    from app.models import DockerHost

    db.add(DockerHost(name="sim-host", endpoint_url="sim://sweep-test"))
    await db.commit()

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


async def test_heartbeat_adopts_container_inserted_concurrently(db, monkeypatch):
    """The sweep and a heartbeat can both see a brand-new container in the same
    instant; the loser of the unique insert must adopt the winner's row instead
    of failing the whole heartbeat with a uq_containers_host_cid violation."""
    from app.core.db import get_sessionmaker
    from app.models import Container, Server
    from app.schemas.agent import AgentContainerIn
    from app.services.server_service import ensure_docker_host, upsert_containers

    server = Server(name="srv-race", hostname="race.test")
    db.add(server)
    await db.commit()
    host = await ensure_docker_host(db, server=server)
    await db.commit()

    # Injection point: the upsert's FIRST flush. By then it has already
    # SELECTed the host's rows (and seen no such container), so committing the
    # same (docker_host_id, container_id) from a concurrent session right here
    # reproduces the production race: the winner's row is committed between the
    # heartbeat's SELECT and its INSERT.
    real_flush = db.flush
    fired = False

    async def racing_flush(*args, **kwargs):
        nonlocal fired
        if not fired:
            fired = True
            async with get_sessionmaker()() as other:
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

    monkeypatch.setattr(db, "flush", racing_flush)

    entry = AgentContainerIn(
        container_id="abc123def456",
        name="web",
        status="RUNNING",
        image_ref="nginx:1.27",
        restart_count=0,
    )
    await upsert_containers(db, server=server, entries=[entry])
    await db.commit()

    rows = (
        (await db.execute(select(Container).where(Container.container_id == "abc123def456")))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].name == "web"
