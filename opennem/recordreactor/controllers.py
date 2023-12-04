""" OpenNEM Milestone Reactor

Generates records for the OpenNEM Milestone Reactor project.

"""
from pathlib import Path

QUERIES_DIRECTORY = Path(__file__).parent / "queries"


def read_sql_file(filename: str) -> str:
    """Reads a SQL file from the queries directory."""
    if not filename.endswith(".sql"):
        filename += ".sql"

    with open(QUERIES_DIRECTORY / filename) as f:
        return f.read()
