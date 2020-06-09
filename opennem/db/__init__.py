import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from opennem.settings import get_database_host, get_mysql_host

DeclarativeBase = declarative_base()

logger = logging.getLogger(__name__)


def db_connect(db_name=None, debug=False):
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    db_conn_str = get_database_host(db_name)

    logger.info("Connecting with {}".format(db_conn_str))

    try:
        e = create_engine(db_conn_str, echo=debug)
        return e
    except Exception as e:
        logger.error("Could not connect to database: {}".format(e))
        return
