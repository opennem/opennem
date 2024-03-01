"""
OpenNEM Mileston Reactor.

Define record queries.

"""

import logging
from pathlib import Path

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.recordreactor.query")

QUERIES_DIRECTORY = Path(__file__).parent / "queries"


def read_sql_file(filename: str) -> str:
    """Reads a SQL file from the queries directory."""
    if not filename.endswith(".sql"):
        filename += ".sql"

    with open(QUERIES_DIRECTORY / filename) as f:
        return f.read()


def run_query(query: str) -> None:
    """Runs a query and logs the result."""
    engine = get_database_engine()

    logger.info(f"Running query: {query}")

    with engine.begin() as c:
        result = c.execute(query)

        logger.info(f"Query result: {result}")


if __name__ == "__main__":
    print(read_sql_file("facility.sql"))
