"""
ClickHouse database connection and utilities module.

This module provides a global ClickHouse client and common utilities for working with ClickHouse.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from clickhouse_driver import Client

from opennem import settings

logger = logging.getLogger("opennem.db.clickhouse")


def get_clickhouse_client(timeout: int = 10) -> Client:
    """
    Get a ClickHouse client instance using settings from environment.

    Returns:
        Client: A configured ClickHouse client instance
    """
    return Client(
        host=settings.clickhouse_url.host,
        port=settings.clickhouse_url.port,
        user=settings.clickhouse_url.username,
        password=settings.clickhouse_url.password,
        settings={"connect_timeout": timeout},
    )


@asynccontextmanager
async def get_clickhouse_context() -> AsyncGenerator[Client, None]:
    """
    Async context manager for ClickHouse client connections.

    Yields:
        Client: ClickHouse client for executing queries

    Raises:
        Exception: If connection fails
    """
    client = get_clickhouse_client()
    try:
        yield client
    finally:
        client.disconnect()


async def get_clickhouse_dependency() -> AsyncGenerator[Client, None]:
    """
    FastAPI dependency for injecting ClickHouse client into route handlers.

    Yields:
        Client: ClickHouse client for executing queries
    """
    async with get_clickhouse_context() as client:
        yield client


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
