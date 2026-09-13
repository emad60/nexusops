"""The docker-host maintenance sweep must actually reach real hosts."""

from __future__ import annotations

import asyncio

import pytest

pytestmark = pytest.mark.integration


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
