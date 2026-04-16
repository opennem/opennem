"""
ClickHouse database package for OpenNEM.

Re-exports from client module for backwards compatibility.
"""

from opennem.db.clickhouse.client import (
    create_table_if_not_exists,
    drop_table_if_exists,
    execute_async,
    get_clickhouse_client,
    get_clickhouse_context,
    get_clickhouse_dependency,
    table_exists,
)

__all__ = [
    "create_table_if_not_exists",
    "drop_table_if_exists",
    "execute_async",
    "get_clickhouse_client",
    "get_clickhouse_context",
    "get_clickhouse_dependency",
    "table_exists",
]
