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

from tests.conftest import (
    _ADMIN_DB,
    _PG_PASSWORD,
    _PG_PORT,
    _PG_USER,
    BACKEND_DIR,
    TEST_DATABASE_URL,
    TEST_PG_HOST,
)

SYNC_URL = TEST_DATABASE_URL.replace("+psycopg", "")


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
    from app.core.db import get_sessionmaker

    maker = get_sessionmaker()
    async with maker() as db:
        rows = await db.execute(
            sa.text(
                "SELECT quote_ident(tablename) FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        )
        names = [row[0] for row in rows]
        if names:
            await db.execute(sa.text(f"TRUNCATE TABLE {', '.join(names)} RESTART IDENTITY CASCADE"))
        await db.commit()


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
    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        yield session


@pytest_asyncio.fixture
async def owner(client: httpx.AsyncClient):
    """Bootstrap owner credentials for this test (fresh DB => first user)."""
    from .helpers import bearer, register_and_login

    credentials, login = await register_and_login(client)
    return {
        "credentials": credentials,
        "headers": bearer(login["access_token"]),
        **login,
    }
