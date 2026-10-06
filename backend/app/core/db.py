"""Async SQLAlchemy engine and session management."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        from app.core.config import get_settings

        settings = get_settings()
        # _assemble_database_url guarantees a URL; assert narrows str | None.
        assert settings.database_url is not None
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            echo=settings.db_echo,
            # Statement errors must never repr bound parameters (password
            # hashes, secret ciphertext, token hashes) into logs. The 500
            # handler logs only the exception class; this keeps the traceback
            # parameter-free as well.
            hide_parameters=True,
            # psycopg3 uses the libpq option name connect_timeout.
            connect_args={"connect_timeout": 10},
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        # The tenant guard must exist before the first session is handed out.
        from app.core.tenancy import install_tenancy_guards

        install_tenancy_guards()
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False, autoflush=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an async session."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def sync_database_url() -> str:
    """Runtime DSN (application role, RLS enforced) for Celery/script sync paths."""
    from app.core.config import get_settings

    url = get_settings().database_url
    assert url is not None
    return url


def sync_migration_url() -> str:
    """Owner-role DSN for Alembic and the container entrypoint.

    Migrations legitimately bypass RLS (they create the tables and run the
    backfill), and the owner role is the one role that does so by construction —
    it is never used to serve traffic.
    """
    from app.core.config import get_settings

    url = get_settings().migration_database_url
    assert url is not None
    return url


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
