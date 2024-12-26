"""OpenNEM Database Module


Provides database engine connections and sessions across the entire
project


"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import deprecation
from psycopg import AsyncConnection
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from opennem import settings
from opennem.utils.version import get_version

DeclarativeBase = declarative_base()

logger = logging.getLogger("opennem.db")

_engine = None
_engine_sync = None
_engine_no_transaction = None


def db_connect(db_conn_str: str | None = None, debug: bool = False, timeout: int = 30) -> AsyncEngine:
    """
    Performs database connection using database settings from settings.py.

    Returns sqlalchemy engine instance

    :param db_conn_str: Database connection string
    :param debug: Debug mode will render queries and info to terminal
    :param timeout: Database connection timeout
    """
    global _engine

    if _engine:
        return _engine

    if not db_conn_str:
        db_conn_str = str(settings.db_url)

    try:
        _engine = create_async_engine(
            db_conn_str,
            query_cache_size=1200,
            echo=settings.db_debug,
            future=True,
            pool_size=30,
            max_overflow=20,
            pool_recycle=1800,
            pool_timeout=timeout,
            pool_pre_ping=True,
            pool_use_lifo=True,
        )

        return _engine
    except Exception as exc:
        logger.error("Could not connect to database: %s", exc)
        raise exc


def get_no_transaction_engine(db_conn_str: str | None = None) -> AsyncEngine:
    """
    Creates a separate engine specifically for operations that cannot run in transactions.
    Uses NullPool to ensure clean connections and isolation.
    """
    global _engine_no_transaction

    if _engine_no_transaction:
        return _engine_no_transaction

    if not db_conn_str:
        db_conn_str = str(settings.db_url)

    try:
        _engine_no_transaction = create_async_engine(
            db_conn_str,
            isolation_level="AUTOCOMMIT",  # This is crucial for no-transaction operations
            poolclass=NullPool,  # Ensure clean connections
            echo=settings.db_debug,
        )
        return _engine_no_transaction
    except Exception as exc:
        logger.error("Could not create no-transaction engine: %s", exc)
        raise exc


def db_connect_sync() -> Engine:
    global _engine_sync

    if _engine_sync:
        return _engine_sync

    db_connect_uri = str(settings.db_url).replace("+asyncpg", "+psycopg")

    _engine_sync = create_engine(db_connect_uri, echo=settings.db_debug)

    return _engine_sync


engine = db_connect()


@deprecation.deprecated(
    deprecated_in="4.0",
    removed_in="4.1",
    current_version=get_version(dev_tag=False),
    details="Use the db_connect function instead",
)
def get_database_engine() -> AsyncEngine:
    """
    Gets a database engine connection

    @NOTE deprecate this eventually
    """
    engine = db_connect()

    return engine


# keey the old variable here until we can remove it
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
SessionLocalAsync = async_sessionmaker(engine, expire_on_commit=False)

# Create a separate session maker for no-transaction operations
SessionNoTransaction = async_sessionmaker(
    get_no_transaction_engine(),
    expire_on_commit=False,
    class_=AsyncSession,
)


@asynccontextmanager
async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocalAsync() as session:
        try:
            async with session.begin():
                yield session
            # The commit will be done automatically when exiting the 'begin' context
        except Exception:
            await session.rollback()
            raise


async def get_scoped_read_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def get_notransaction_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Gets a session that operates outside of transaction blocks.
    Used for operations that can't run inside transaction blocks like VACUUM or certain TimescaleDB operations.
    """
    async with SessionNoTransaction() as session:
        try:
            yield session
        finally:
            await session.close()


@deprecation.deprecated(
    deprecated_in="4.0",
    removed_in="4.1",
    current_version=get_version(dev_tag=False),
    details="Use get_read_session and get_write_session instead",
)
async def get_scoped_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocalAsync() as session:
        yield session


@deprecation.deprecated(
    deprecated_in="4.0",
    removed_in="4.1",
    current_version=get_version(dev_tag=False),
    details="Use the db_connect function instead",
)
async def get_scoped_connection() -> AsyncGenerator[AsyncConnection, None]:
    async with engine.begin() as connection:
        yield connection
