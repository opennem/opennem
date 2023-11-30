""" Runs a query against OpenNEM"""

import logging
import re
from datetime import date, datetime
from textwrap import dedent

from pydantic import BaseModel
from sqlalchemy import text as sql

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.recordreactor.ai.utils")

ValidNumber = float | int | None


class OpennemResultSet(BaseModel):
    column_names: list[str]
    results: list[list[ValidNumber | str | datetime | date]]


def is_read_only_query(sql_query: str) -> bool:
    """
    Checks if the given SQL query string is read-only.
    Returns True if the query is read-only, False otherwise.
    """
    # List of SQL statements that modify data in the database
    modifying_statements = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "GRANT", "TRUNCATE"]

    # Check if the query contains any modifying statements
    for statement in modifying_statements:
        if statement in sql_query.upper():
            return False

    # If no modifying statements are found, the query is read-only
    return True


class InvalidQueryReceived(Exception):
    pass


class NotReadOnlyException(Exception):
    pass


class BadQuery(Exception):
    pass


def clean_message_content(query: str) -> str:
    """
    Cleans message content to extract the SQL query
    """
    # Ignore text after the SQL query terminator `;`
    query = query.split(";")[0]

    # Remove prefix for corrected query assistant message
    split_query = query.split(":")
    if len(split_query) > 1:
        query = split_query[1].strip()

    if "```" in query:
        if query_comp := re.search(r"```(.*?)```", query, re.DOTALL):
            query = query_comp.group(1).strip()
        else:
            raise InvalidQueryReceived("Invalid query.")

    return query


def run_opennem_query(query: str) -> OpennemResultSet | None:
    """Runs a query against OpenNEM"""
    engine = get_database_engine()

    query = clean_message_content(query)

    if not is_read_only_query(query):
        raise NotReadOnlyException("Only read-only queries are allowed.")

    logger.debug(dedent(query))

    with engine.begin() as conn:
        try:
            result = conn.execute(sql(query))
        except Exception as e:
            raise BadQuery(e) from None

        if not result:
            return None

        column_names = list(result.keys())
        results = [list(row) for row in result]
        response_model = OpennemResultSet(column_names=column_names, results=results)

    return response_model
