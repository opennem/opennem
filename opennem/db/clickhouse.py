"""
ClickHouse database connection and utilities module.

This module provides a singleton ClickHouse client and common utilities for working with ClickHouse.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from clickhouse_driver import Client

from opennem import settings

logger = logging.getLogger("opennem.db.clickhouse")

# Module-level singleton — clickhouse-driver Client auto-reconnects on
# dropped connections.  Safe under Granian's single-threaded-per-worker
# asyncio model (one Client per process).
_client: Client | None = None


def get_clickhouse_client(timeout: int = 10) -> Client:
    """
    Get (or create) the singleton ClickHouse client instance.

    Returns:
        Client: A configured ClickHouse client instance
    """
    global _client
    if _client is None:
        _client = Client(
            host=settings.clickhouse_url.host,
            port=settings.clickhouse_url.port,
            user=settings.clickhouse_url.username,
            password=settings.clickhouse_url.password,
            database=settings.clickhouse_url.path.lstrip("/") if settings.clickhouse_url.path else "",
            settings={"connect_timeout": timeout},
        )
    return _client


async def execute_async(client: Client, query: str, params: dict | None = None, **kwargs: Any) -> Any:
    """
    Run a blocking clickhouse-driver execute() in a thread so the
    asyncio event loop is not blocked.
    """
    return await asyncio.to_thread(client.execute, query, params, **kwargs)


@asynccontextmanager
async def get_clickhouse_context() -> AsyncGenerator[Client, None]:
    """
    Async context manager for ClickHouse client connections.

    Yields the singleton client — no per-request connect/disconnect.
    """
    yield get_clickhouse_client()


async def get_clickhouse_dependency() -> AsyncGenerator[Client, None]:
    """
    FastAPI dependency for injecting ClickHouse client into route handlers.
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
