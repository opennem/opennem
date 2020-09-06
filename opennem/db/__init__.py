import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from opennem.settings import get_database_host

DeclarativeBase = declarative_base()

logger = logging.getLogger(__name__)


def db_connect(db_name=None, debug=False):
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    db_conn_str = get_database_host()

    connect_args = {}

    if db_conn_str.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    try:
        e = create_engine(
            db_conn_str,
            echo=debug,
            pool_size=10,
            pool_timeout=60,
            connect_args=connect_args,
        )
        return e
    except Exception as e:
        logger.error("Could not connect to database: {}".format(e))
        return


engine = db_connect()
session = sessionmaker(bind=engine, autocommit=False, autoflush=False,)


def get_database_session():
    try:
        s = session()
        return s
    finally:
        s.close()
