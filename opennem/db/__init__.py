import logging
from typing import Generator

from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from opennem.exporter.encoders import opennem_deserialize, opennem_serialize
from opennem.settings import settings

DeclarativeBase = declarative_base()

logger = logging.getLogger(__name__)


database = Database(settings.db_url)


# Methods


async def db_connect_async() -> None:
    await database.connect()


async def db_disconnect() -> None:
    await database.disconnect()


def db_connect(
    db_name: str = None, debug: bool = False, timeout: int = 300
) -> Engine:
    """
    Performs database connection using database settings from settings.py.

    Returns sqlalchemy engine instance
    """
    db_conn_str = settings.db_url

    connect_args = {}

    if db_conn_str.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    if settings.db_debug:
        debug = True

    try:
        return create_engine(
            db_conn_str,
            json_serializer=opennem_serialize,
            json_deserializer=opennem_deserialize,
            echo=debug,
            pool_size=10,
            max_overflow=2,
            pool_recycle=300,
            pool_timeout=timeout,
            pool_pre_ping=True,
            pool_use_lifo=True,
            connect_args=connect_args,
        )
    except Exception as exc:
        logger.error("Could not connect to database: %s", exc)
        raise exc


engine = db_connect()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

SessionAutocommit = sessionmaker(bind=engine, autocommit=True, autoflush=True)


def get_database_session() -> Generator[sessionmaker, None, None]:
    """
    Gets a database session

    """
    s = None

    try:
        s = SessionLocal()
        yield s
    except Exception as e:
        raise e
    finally:
        if s:
            s.close()


def get_database_engine() -> Engine:
    """
    Gets a database engine connection

    """
    return engine
