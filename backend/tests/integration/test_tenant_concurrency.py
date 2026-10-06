"""Tenant context under concurrency and connection pooling (Phase 1 hardening).

The isolation suite proves a request cannot *ask* for another tenant's data.
This suite proves something narrower and harder: that the organization bound to a
unit of work cannot *leak through the connection pool* into the next one.

Why a pool is the interesting surface
-------------------------------------
``app.current_org`` is connection state, and connections are reused. The tenant
scope itself lives in ``ContextVar``s, so it is already task-local; the risk is
the PostgreSQL GUC that RLS reads, which is written onto whatever pooled
connection the session happens to draw. Three properties make that safe, and each
one is exercised here:

* the GUC is set **transaction-local** (``is_local => true``), so PostgreSQL
  discards it when the transaction ends and a connection handed back to the pool
  carries no organization at all — this closes the window in which a session-level
  setting survived checkin (the pool's reset is a plain ``rollback``);
* it is re-issued on **every** ``after_begin``, so a fresh transaction on a
  recycled connection is re-armed from the *current* task's scope, including after
  a commit ends one transaction and the next statement opens another;
* the ``ContextVar`` scope is copied per task, so concurrent requests and worker
  jobs that interleave on the same handful of connections never read each other's
  organization.

The tests deliberately use a dedicated engine pinned to a **single** connection
(``pool_size=1, max_overflow=0``) so "reuse" is not left to chance, plus a
two-connection engine to force many tasks to interleave over few connections.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
import sqlalchemy as sa
from app.core.config import get_settings
from app.core.tenancy import (
    SCOPE_UNSET,
    TenancyScopeError,
    apply_scope_to_session,
    current_org,
    current_scope,
    org_scope,
    system_write_scope,
)
from app.models import Server
from app.models.tenancy import SYSTEM_ORG_SENTINEL
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .helpers import API, server_payload

pytestmark = pytest.mark.integration


# --- helpers -----------------------------------------------------------------


def _maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def pooled_engine() -> AsyncIterator[Callable[..., AsyncEngine]]:
    """Factory for throwaway engines that are always disposed."""
    created: list[AsyncEngine] = []

    def make(pool_size: int = 1, max_overflow: int = 0) -> AsyncEngine:
        settings = get_settings()
        assert settings.database_url is not None
        engine = create_async_engine(
            settings.database_url, pool_size=pool_size, max_overflow=max_overflow
        )
        created.append(engine)
        return engine

    yield make
    for engine in created:
        await engine.dispose()


async def _create_server(client, headers, name: str) -> str:
    response = await client.post(f"{API}/nodes", headers=headers, json=server_payload(name))
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _guc(session: AsyncSession) -> str:
    """The organization the connection is currently presenting, or ``""``."""
    return await session.scalar(sa.text("SELECT current_setting('app.current_org', true)")) or ""


async def _visible_server_ids(session: AsyncSession) -> set[str]:
    rows = (await session.execute(select(Server.id))).scalars().all()
    return {str(row) for row in rows}


async def _raw_guc(engine: AsyncEngine) -> str:
    """Read the GUC on a bare pooled connection, bypassing every ORM listener."""
    async with engine.connect() as conn:
        return await conn.scalar(sa.text("SELECT current_setting('app.current_org', true)")) or ""


@pytest_asyncio.fixture
async def two_orgs(client, owner, second_org) -> dict:
    """A and B, each with servers, plus the ids this test created."""
    a = owner["active_organization_id"]
    b = second_org["id"]
    a_ids = {await _create_server(client, owner["headers"], f"conc-a-{i}") for i in range(3)}
    b_ids = {await _create_server(client, second_org["headers"], f"conc-b-{i}") for i in range(2)}
    return {"a": uuid.UUID(a), "b": uuid.UUID(b), "a_ids": a_ids, "b_ids": b_ids}


# --- reuse across sequential transactions ------------------------------------


async def test_a_reused_pooled_connection_carries_no_tenant_between_transactions(
    two_orgs, pooled_engine
) -> None:
    """The same physical connection serves A, then B, and never confuses them.

    ``pool_size=1`` makes reuse deterministic: the second session *must* draw the
    connection the first one returned.
    """
    engine = pooled_engine(pool_size=1)
    maker = _maker(engine)

    async with maker() as session:
        with org_scope(two_orgs["a"]):
            await apply_scope_to_session(session)
            assert await _guc(session) == str(two_orgs["a"])
            assert await _visible_server_ids(session) == two_orgs["a_ids"]
        await session.commit()

    # Returned to the pool: transaction-local means no organization survives it.
    assert await _raw_guc(engine) == ""

    async with maker() as session:
        with org_scope(two_orgs["b"]):
            await apply_scope_to_session(session)
            assert await _guc(session) == str(two_orgs["b"])
            assert await _visible_server_ids(session) == two_orgs["b_ids"]
        await session.commit()

    assert await _raw_guc(engine) == ""


async def test_a_failed_transaction_does_not_leak_its_scope(two_orgs, pooled_engine) -> None:
    """An exception + rollback must leave neither GUC nor ContextVar behind."""
    engine = pooled_engine(pool_size=1)
    maker = _maker(engine)

    async with maker() as session:
        with org_scope(two_orgs["a"]):
            await apply_scope_to_session(session)
            assert await _guc(session) == str(two_orgs["a"])
            with pytest.raises(sa.exc.DBAPIError):
                await session.execute(sa.text("SELECT 1 / 0"))
        await session.rollback()

    # The scope is a context manager: exiting on the exception restores it.
    assert current_scope() == SCOPE_UNSET
    assert current_org() is None
    assert await _raw_guc(engine) == ""

    # The connection is reused by B with a clean slate.
    async with maker() as session:
        with org_scope(two_orgs["b"]):
            await apply_scope_to_session(session)
            assert await _guc(session) == str(two_orgs["b"])
            assert await _visible_server_ids(session) == two_orgs["b_ids"]
        await session.commit()


async def test_scope_contextvars_are_restored_after_a_raising_block(two_orgs) -> None:
    """A scope that exits via an exception must not strand the next unit of work."""
    with pytest.raises(ValueError):
        with org_scope(two_orgs["a"]):
            raise ValueError("boom")

    assert current_scope() == SCOPE_UNSET
    assert current_org() is None


# --- concurrency --------------------------------------------------------------


async def test_concurrent_orgs_sharing_a_pool_never_observe_each_others_context(
    two_orgs, pooled_engine
) -> None:
    """Many tasks, two tenants, two connections: each read sees only its own org.

    Each iteration commits, so the next statement opens a *new* transaction on the
    (reused) connection and has to be re-armed by ``after_begin`` — exactly the
    hand-off a real request makes when the pool is under pressure.
    """
    engine = pooled_engine(pool_size=2, max_overflow=0)

    async def hammer(org: uuid.UUID, expected: set[str]) -> None:
        maker = _maker(engine)
        async with maker() as session:
            with org_scope(org):
                for _ in range(4):
                    await asyncio.sleep(0)  # force interleaving between tasks
                    assert await _guc(session) == str(org)
                    assert await _visible_server_ids(session) == expected
                    await session.commit()

    await asyncio.gather(
        *[hammer(two_orgs["a"], two_orgs["a_ids"]) for _ in range(6)],
        *[hammer(two_orgs["b"], two_orgs["b_ids"]) for _ in range(6)],
    )


async def test_websocket_entity_checks_stay_inside_their_socket_org(
    two_orgs, pooled_engine
) -> None:
    """The hub's subscribe-time existence check under concurrent orgs.

    ``_entity_exists`` is what stops a foreign id from ever becoming a
    subscription on the per-entity channels. Run concurrently on a tiny pool, a
    foreign id must resolve to a plain miss — never to the other tenant's row.
    """
    from app.ws.hub import _entity_exists

    engine = pooled_engine(pool_size=2, max_overflow=0)
    a_server = uuid.UUID(next(iter(two_orgs["a_ids"])))
    b_server = uuid.UUID(next(iter(two_orgs["b_ids"])))

    async def check(org: uuid.UUID, target: uuid.UUID, expected: bool) -> None:
        maker = _maker(engine)
        async with maker() as session:
            assert await _entity_exists(session, Server, target, org_id=org) is expected

    await asyncio.gather(
        check(two_orgs["a"], a_server, True),
        check(two_orgs["b"], b_server, True),
        # A foreign id is indistinguishable from one that never existed.
        check(two_orgs["a"], b_server, False),
        check(two_orgs["b"], a_server, False),
        check(two_orgs["a"], a_server, True),
        check(two_orgs["b"], b_server, True),
    )


# --- deliberate session reuse across scopes ----------------------------------


async def test_a_session_reused_across_scopes_is_rearmed_by_apply_scope_to_session(
    two_orgs, pooled_engine
) -> None:
    """Switching scope on an already-open transaction requires the explicit push.

    ``after_begin`` only fires at a transaction boundary, so a long-lived session
    that changes tenant mid-transaction must call ``apply_scope_to_session`` — this
    is the helper the sweeps rely on, and the test pins that it actually moves the
    GUC (not just the ``ContextVar``).
    """
    engine = pooled_engine(pool_size=1)
    maker = _maker(engine)

    async with maker() as session:
        with org_scope(two_orgs["a"]):
            await apply_scope_to_session(session)
            assert await _visible_server_ids(session) == two_orgs["a_ids"]
        with org_scope(two_orgs["b"]):
            await apply_scope_to_session(session)
            assert await _guc(session) == str(two_orgs["b"])
            assert await _visible_server_ids(session) == two_orgs["b_ids"]
        await session.commit()


async def test_system_write_scope_restores_the_tenant_on_the_same_connection(
    two_orgs, pooled_engine
) -> None:
    """A pre-org write inside a tenant transaction must not strand system scope.

    ``system_write_scope`` briefly moves the GUC to the system sentinel; the
    surrounding tenant work has to continue under its own organization afterwards.
    """
    engine = pooled_engine(pool_size=1)
    maker = _maker(engine)

    async with maker() as session:
        with org_scope(two_orgs["a"]):
            await apply_scope_to_session(session)
            async with system_write_scope(session, "test.pre_org_event"):
                assert await _guc(session) == SYSTEM_ORG_SENTINEL
            assert await _guc(session) == str(two_orgs["a"])
            assert await _visible_server_ids(session) == two_orgs["a_ids"]
        await session.commit()


async def test_an_unscoped_read_after_scoped_work_is_refused_not_empty(
    two_orgs, pooled_engine
) -> None:
    """Leaving the scope must fail loud, never quietly return every tenant's rows."""
    engine = pooled_engine(pool_size=1)
    maker = _maker(engine)

    async with maker() as session:
        with org_scope(two_orgs["a"]):
            await apply_scope_to_session(session)
            assert await _visible_server_ids(session) == two_orgs["a_ids"]
        await session.commit()

        with pytest.raises(TenancyScopeError):
            await session.execute(select(Server.id))


# --- worker (Celery) scoping --------------------------------------------------


async def test_a_worker_sweep_resolves_the_owner_then_reenters_its_org(
    two_orgs,
) -> None:
    """The exact worker pattern: claim cross-tenant, then scope per row.

    The sweep session *may* see every tenant (it has to, to find work). Once a row
    is resolved to its organization, the work session must see only that tenant —
    and the sweep must have returned rows from both organizations to be meaningful.
    """
    from app.tasks._util import org_for, org_session, sweep_session

    async with sweep_session("test.sweep_servers") as db:
        rows = (await db.execute(select(Server.id, Server.org_id))).all()

    owner_of = {str(server_id): org_id for server_id, org_id in rows}
    assert {str(org) for org in owner_of.values()} >= {str(two_orgs["a"]), str(two_orgs["b"])}

    for server_id, org_id in rows:
        assert await org_for(Server, server_id) == org_id
        async with org_session(org_id) as scoped:
            assert await _guc(scoped) == str(org_id)
            visible = await _visible_server_ids(scoped)
            assert str(server_id) in visible
            # Every visible row belongs to this organization, nothing else.
            assert visible <= {sid for sid, org in owner_of.items() if org == org_id}
