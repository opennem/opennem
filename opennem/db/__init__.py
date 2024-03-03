"""OpenNEM Database Module


Provides database engine connections and sessions across the entire
project


"""

import logging
from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from opennem import settings
from opennem.exporter.encoders import opennem_deserialize, opennem_serialize

DeclarativeBase = declarative_base()

logger = logging.getLogger("opennem.db")


def db_connect(db_conn_str: str | None = None, debug: bool = False, timeout: int = 10) -> Engine:
    """
    Performs database connection using database settings from settings.py.

    Returns sqlalchemy engine instance

    :param db_conn_str: Database connection string
    :param debug: Debug mode will render queries and info to terminal
    :param timeout: Database connection timeout
    """
    if not db_conn_str:
        db_conn_str = str(settings.db_url)

    connect_args = {}

    if db_conn_str.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    if settings.db_debug:
        debug = True

    keepalive_kwargs = {
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 5,
        "keepalives_count": 5,
    }

    if settings.db_debug:
        debug = True
        logger.info("Database debug mode enabled")

    try:
        return create_engine(
            db_conn_str,
            json_serializer=opennem_serialize,
            json_deserializer=opennem_deserialize,
            query_cache_size=1200,
            echo=debug,
            pool_size=30,
            max_overflow=20,
            pool_recycle=100,
            pool_timeout=timeout,
            pool_pre_ping=True,
            pool_use_lifo=True,
            connect_args={
                **connect_args,
                **keepalive_kwargs,
            },
        )
    except Exception as exc:
        logger.error("Could not connect to database: %s", exc)
        raise exc


def db_connect_async(db_conn_str: str | None = None, debug: bool = False, timeout: int = 10) -> AsyncEngine:
    """
    Returns async sqlalchemy engine instance

    :param db_conn_str: Database connection string
    :param debug: Debug mode will render queries and info to terminal
    :param timeout: Database connection timeout
    """
    if not db_conn_str:
        db_conn_str = str(settings.db_url)

    connect_args = {}

    if not db_conn_str.startswith("postgresql"):
        raise Exception("Only postgresql supported")

    if settings.db_debug:
        debug = True

    keepalive_kwargs = {
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 5,
        "keepalives_count": 5,
    }

    if settings.db_debug:
        debug = True
        logger.info("Database debug mode enabled")

    try:
        return create_async_engine(
            db_conn_str,
            json_serializer=opennem_serialize,
            json_deserializer=opennem_deserialize,
            query_cache_size=1200,
            echo=debug,
            pool_size=30,
            max_overflow=20,
            pool_recycle=100,
            pool_timeout=timeout,
            pool_pre_ping=True,
            pool_use_lifo=True,
            connect_args={
                **connect_args,
                **keepalive_kwargs,
            },
        )
    except Exception as exc:
        logger.error("Could not connect to database: %s", exc)
        raise exc


engine = db_connect()


def get_database_engine() -> Engine:
    """
    Gets a database engine connection

    @NOTE deprecate this eventually
    """
    global engine

    return engine


SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
async_session = async_sessionmaker(engine, expire_on_commit=False)


def get_scoped_session() -> Session:
    return scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))()


def get_database_session() -> Generator[Session, None, None]:
    """
    Gets a database session

    """
    s = None

    try:
        s = get_scoped_session()
        yield s
    except Exception as e:
        raise e
    finally:
        if s:
            s.close()


async def get_database_session_async() -> AsyncGenerator[Session, None]:
    """
    Gets a database session

    """
    s = None

    try:
        s = async_session
        yield s
    except Exception as e:
        raise e
    finally:
        if s:
            s.close()
