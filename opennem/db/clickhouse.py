"""
ClickHouse database connection and utilities module.

This module provides a global ClickHouse client and common utilities for working with ClickHouse.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from clickhouse_driver.client import Client
from clickhouse_driver.dbapi.connection import Connection

from opennem import settings

logger = logging.getLogger("opennem.db.clickhouse")


def get_clickhouse_client() -> Client:
    """
    Get a ClickHouse client instance using settings from environment.

    Returns:
        Client: A configured ClickHouse client instance
    """
    return Client.from_url(settings.clickhouse_url)


def get_clickhouse_connection() -> Connection:
    """
    Get a ClickHouse DBAPI connection using settings from environment.

    Returns:
        Connection: A configured ClickHouse connection
    """
    return Connection.from_url(settings.clickhouse_url)


@asynccontextmanager
async def get_clickhouse_session() -> AsyncGenerator[Client, None]:
    """
    Get a ClickHouse client session as an async context manager.

    Yields:
        Client: A configured ClickHouse client instance
    """
    client = get_clickhouse_client()
    try:
        yield client
    finally:
        client.disconnect()


def create_table_if_not_exists(client: Client, table_name: str, schema: str) -> None:
    """
    Create a ClickHouse table if it doesn't exist.

    Args:
        client (Client): ClickHouse client
        table_name (str): Name of the table to create
        schema (str): CREATE TABLE schema definition
    """
    client.execute(schema)


def drop_table_if_exists(client: Client, table_name: str) -> None:
    """
    Drop a ClickHouse table if it exists.

    Args:
        client (Client): ClickHouse client
        table_name (str): Name of the table to drop
    """
    client.execute(f"DROP TABLE IF EXISTS {table_name}")


def table_exists(client: Client, table_name: str) -> bool:
    """
    Check if a ClickHouse table exists.

    Args:
        client (Client): ClickHouse client
        table_name (str): Name of the table to check

    Returns:
        bool: True if table exists, False otherwise
    """
    result = client.execute(
        "SELECT name FROM system.tables WHERE database = currentDatabase() AND name = %(table)s", {"table": table_name}
    )
    return len(result) > 0
