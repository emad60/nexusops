"""Integration fixtures: migrated test database, per-test clean slate, API client.

Layout:
* session-scoped: ensure ``nexusops_test`` exists, apply Alembic migrations.
* autouse, function-scoped: TRUNCATE every table, reseed the RBAC registry,
  flush the dedicated Redis index, then dispose app singletons so no pooled
  connection outlives its event loop.

Credentials come from tests/conftest.py (parsed from the repo .env); they are
never printed or asserted on.
"""

from __future__ import annotations

import httpx
import pytest
import pytest_asyncio
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import (
    _ADMIN_DB,
    _PG_PASSWORD,
    _PG_PORT,
    _PG_USER,
    BACKEND_DIR,
    TEST_OWNER_DATABASE_URL,
    TEST_PG_HOST,
)

SYNC_OWNER_URL = TEST_OWNER_DATABASE_URL.replace("+psycopg", "")


def _ensure_database() -> None:
    """Create nexusops_test when absent (idempotent across runs)."""
    import psycopg

    dsn = f"postgresql://{_PG_USER}:{_PG_PASSWORD}@{TEST_PG_HOST}:{_PG_PORT}/{_ADMIN_DB}"
    with psycopg.connect(dsn, autocommit=True) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", ("nexusops_test",)
        ).fetchone()
        if not exists:
            conn.execute("CREATE DATABASE nexusops_test")


def _run_migrations() -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def _migrated_database() -> None:
    _ensure_database()
    _run_migrations()


async def _truncate_all() -> None:
    """Wipe every table as the **owner**.

    TRUNCATE is not subject to row-level security but does require table
    ownership (or an explicit TRUNCATE grant the application role deliberately
    does not have), so the fixture opens its own owner-role engine rather than
    reusing the application session.
    """
    owner_engine = create_async_engine(
        SYNC_OWNER_URL.replace("postgresql://", "postgresql+psycopg://")
    )
    try:
        async with owner_engine.begin() as conn:
            rows = await conn.execute(
                sa.text(
                    "SELECT quote_ident(tablename) FROM pg_tables "
                    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
                )
            )
            names = [row[0] for row in rows]
            if names:
                await conn.execute(
                    sa.text(f"TRUNCATE TABLE {', '.join(names)} RESTART IDENTITY CASCADE")
                )
    finally:
        await owner_engine.dispose()


async def _seed_rbac_registry() -> None:
    """Insert permissions + system roles exactly like scripts/seed.py does."""
    from app.core.db import get_sessionmaker
    from app.core.permissions import PERMISSIONS, ROLE_MATRIX, WILDCARD
    from app.models import Permission, Role

    maker = get_sessionmaker()
    async with maker() as db:
        perms: dict[str, Permission] = {}
        for spec in PERMISSIONS:
            perm = Permission(
                codename=spec.codename, group=spec.group, description=spec.description
            )
            perms[spec.codename] = perm
            db.add(perm)
        await db.flush()
        for role_name, codenames in ROLE_MATRIX.items():
            role = Role(name=role_name, description=f"{role_name} (system)", is_system=True)
            if codenames != [WILDCARD]:
                role.permissions = [perms[c] for c in codenames]
            db.add(role)
        await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def _clean_slate() -> None:
    await _truncate_all()
    await _seed_rbac_registry()

    from app.core.logging import get_logger
    from app.core.redis_client import get_redis

    log = get_logger(__name__)
    try:
        await get_redis().flushdb()
    except Exception:
        log.debug("test_redis_flush_skipped")

    yield

    # Pooled connections are loop-bound; drop them before the next test's loop.
    from app.core.db import dispose_engine
    from app.core.redis_client import close_redis

    await close_redis()
    await dispose_engine()


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    from app.main import app

    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 54321))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest_asyncio.fixture
async def db():
    """A session with **no** tenant scope.

    Deliberately unscoped: it is how a test asserts that reaching
    organization-owned data without entering a scope fails loudly instead of
    quietly returning every tenant's rows. Use :func:`org_db` to read or write
    tenant data.
    """
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        yield session


class ScopedSession:
    """A session that enters its tenancy scope around each operation.

    A fixture cannot hold a scope open across the test: the scope is a ContextVar
    in the *test's* context, and ``httpx``'s ASGI transport runs the application
    in that same context — so the next request the test made would start out
    inside someone else's scope, and the guard would (correctly) refuse to switch
    it. Entering per call reproduces what a real request does: one scope, one
    unit of work.
    """

    def __init__(self, session, *, org_id=None, system_reason: str | None = None) -> None:
        self._session = session
        self._org_id = org_id
        self._system_reason = system_reason

    def _scope(self):
        from app.core.tenancy import org_scope, system_scope

        if self._system_reason is not None:
            return system_scope(self._system_reason)
        return org_scope(self._org_id)

    async def _apply(self) -> None:
        from app.core.tenancy import apply_scope_to_session

        await apply_scope_to_session(self._session)

    def add(self, *args, **kwargs):
        return self._session.add(*args, **kwargs)

    def expunge_all(self):
        return self._session.expunge_all()

    def __contains__(self, instance) -> bool:
        # ``obj in db`` is how services test whether a row is still attached.
        return instance in self._session

    def expire_all(self):
        return self._session.expire_all()

    async def execute(self, *args, **kwargs):
        with self._scope():
            await self._apply()
            return await self._session.execute(*args, **kwargs)

    async def scalar(self, *args, **kwargs):
        with self._scope():
            await self._apply()
            return await self._session.scalar(*args, **kwargs)

    async def get(self, *args, **kwargs):
        with self._scope():
            await self._apply()
            return await self._session.get(*args, **kwargs)

    async def refresh(self, *args, **kwargs):
        with self._scope():
            await self._apply()
            return await self._session.refresh(*args, **kwargs)

    async def flush(self, *args, **kwargs):
        with self._scope():
            await self._apply()
            return await self._session.flush(*args, **kwargs)

    async def commit(self):
        with self._scope():
            await self._apply()
            return await self._session.commit()

    async def rollback(self):
        return await self._session.rollback()

    def __getattr__(self, name: str):
        # Anything not wrapped above (``sync_session``, ``info``, …) is a plain
        # pass-through: only the statement-issuing calls need a scope.
        return getattr(self._session, name)


@pytest_asyncio.fixture
async def org_db(owner):
    """A session scoped to the owner's organization.

    Tenant data is only reachable from within a scope — by design, in three
    independent layers — so verification queries in a test have to enter one
    exactly like a request does.
    """
    import uuid as _uuid

    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        yield ScopedSession(session, org_id=_uuid.UUID(owner["active_organization_id"]))


@pytest_asyncio.fixture
async def system_db():
    """A session scoped to the system scope — how a maintenance sweep runs.

    Sweeps are cross-tenant by definition (claim a due row, then resolve its
    organization), so they iterate under ``system_scope``; tests that call those
    functions directly need the same scope the worker would have.
    """
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        yield ScopedSession(session, system_reason="integration test: sweep")


@pytest_asyncio.fixture
async def second_org(client: httpx.AsyncClient, owner: dict):
    """A second organization the owner also belongs to.

    Both tenants are owned by the same user on purpose: it removes every
    *authentication* difference from a cross-tenant test, so what remains is
    purely the tenancy boundary. Requests are made with the same bearer token
    and only ``X-Org-Id`` changes.

    Returns the new organization's id plus headers scoped to it.
    """
    from .helpers import API, assert_error_code, bearer

    response = await client.post(
        f"{API}/organizations",
        json={"name": "Second Tenant", "description": "cross-tenant test org"},
        headers=owner["headers"],
    )
    assert response.status_code == 201, response.text
    org_id = response.json()["organization"]["id"]
    return {
        "id": org_id,
        "headers": bearer(owner["access_token"], org_id),
        "owner_headers": owner["headers"],
        "_assert_error_code": assert_error_code,
    }


@pytest_asyncio.fixture
async def owner(client: httpx.AsyncClient):
    """Bootstrap owner credentials for this test (fresh DB => first user).

    ``headers`` carry both the bearer token and the bootstrap organization, so
    any org-scoped call made with them is a complete, valid request.
    """
    from .helpers import login_headers, register_and_login

    credentials, login = await register_and_login(client)
    return {
        "credentials": credentials,
        "headers": login_headers(login),
        **login,
    }
