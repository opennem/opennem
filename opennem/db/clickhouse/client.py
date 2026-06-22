"""
ClickHouse database connection and utilities module.

This module provides thread-local ClickHouse clients and common utilities for working with ClickHouse.
"""

import asyncio
import logging
import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from clickhouse_driver import Client

from opennem import settings

logger = logging.getLogger("opennem.db.clickhouse")

# Thread-local storage — one Client per thread.  asyncio.to_thread dispatches
# queries to a thread pool, so each thread needs its own connection to avoid
# "Simultaneous queries on single connection" errors.
_local = threading.local()


def _serving_query_settings() -> dict[str, int]:
    """
    Per-query ClickHouse limits for the serving path (execute_async).

    Without these a single wide aggregation can grow its GROUP BY hash table until
    the whole server runs out of memory, at which point the server-wide overcommit
    tracker kills an arbitrary query (Code 241). Capping per query makes a runaway
    query fail cleanly on its own and lets large-but-legit GROUP BYs spill to disk.

    A value of 0 in settings disables that individual limit.
    """
    out: dict[str, int] = {}
    if settings.clickhouse_query_max_memory_usage:
        out["max_memory_usage"] = settings.clickhouse_query_max_memory_usage
    if settings.clickhouse_query_max_bytes_before_external_group_by:
        out["max_bytes_before_external_group_by"] = settings.clickhouse_query_max_bytes_before_external_group_by
    if settings.clickhouse_query_max_execution_time:
        out["max_execution_time"] = settings.clickhouse_query_max_execution_time
    return out


def _make_client(timeout: int = 10) -> Client:
    return Client(
        host=settings.clickhouse_url.host,
        port=settings.clickhouse_url.port,
        user=settings.clickhouse_url.username,
        password=settings.clickhouse_url.password,
        database=settings.clickhouse_url.path.lstrip("/") if settings.clickhouse_url.path else "",
        settings={"connect_timeout": timeout},
    )


def get_clickhouse_client(timeout: int = 10) -> Client:
    """
    Get (or create) a thread-local ClickHouse client instance.
    Connections are reused within the same thread, avoiding TCP
    handshake overhead while remaining thread-safe.
    """
    client = getattr(_local, "client", None)
    if client is None:
        client = _make_client(timeout)
        _local.client = client
    return client


async def execute_async(client: Client, query: str, params: dict | None = None, **kwargs: Any) -> Any:
    """
    Run a blocking clickhouse-driver execute() in a thread so the
    asyncio event loop is not blocked.  Each thread in the pool gets
    its own Client via thread-local storage.

    Conservative per-query resource limits (see ``_serving_query_settings``) are applied
    by default so one expensive serving query cannot OOM the shared server. Callers can
    override individual limits by passing ``settings={...}`` (caller keys win per-key).
    """
    merged_settings = {**_serving_query_settings(), **(kwargs.pop("settings", None) or {})}

    def _run() -> Any:
        tl_client = get_clickhouse_client()
        return tl_client.execute(query, params, settings=merged_settings, **kwargs)

    return await asyncio.to_thread(_run)


@asynccontextmanager
async def get_clickhouse_context() -> AsyncGenerator[Client, None]:
    """
    Async context manager for ClickHouse client connections.
    Yields a thread-local client.
    """
    yield get_clickhouse_client()


async def get_clickhouse_dependency() -> AsyncGenerator[Client, None]:
    """
    FastAPI dependency for injecting ClickHouse client into route handlers.
    """
    async with get_clickhouse_context() as client:
        yield client


def create_table_if_not_exists(client: Client, table_name: str, schema: str) -> None:
    """Create a ClickHouse table if it doesn't exist."""
    client.execute(schema)


def drop_table_if_exists(client: Client, table_name: str) -> None:
    """Drop a ClickHouse table if it exists."""
    client.execute(f"DROP TABLE IF EXISTS {table_name}")


def table_exists(client: Client, table_name: str) -> bool:
    """Check if a ClickHouse table exists."""
    result = client.execute(
        "SELECT name FROM system.tables WHERE database = currentDatabase() AND name = %(table)s", {"table": table_name}
    )
    return len(result) > 0
