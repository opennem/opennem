"""
Baseline schema: 2 base tables (market_summary, unit_intervals) + 7 materialized views.

All DDL uses IF NOT EXISTS / IF EXISTS — safe on existing databases.
On first deploy this is a bookkeeping migration (schema already present).
"""

from clickhouse_driver import Client

REQUIRES_BACKFILL: list[str] = []


def _table_exists(client: Client, name: str) -> bool:
    result = client.execute(
        "SELECT name FROM system.tables WHERE database = currentDatabase() AND name = %(t)s",
        {"t": name},
    )
    return len(result) > 0


def up(client: Client) -> None:
    from opennem.db.clickhouse.schema import (
        MARKET_SUMMARY_TABLE_SCHEMA,
        UNIT_INTERVALS_TABLE_SCHEMA,
    )
    from opennem.db.clickhouse.views import CLICKHOUSE_MATERIALIZED_VIEWS

    # Base tables (schemas include IF NOT EXISTS)
    client.execute(MARKET_SUMMARY_TABLE_SCHEMA)
    client.execute(UNIT_INTERVALS_TABLE_SCHEMA)

    # Materialized views (schemas lack IF NOT EXISTS — check manually)
    for view in CLICKHOUSE_MATERIALIZED_VIEWS.values():
        if not _table_exists(client, view.name):
            client.execute(view.schema)


def down(client: Client) -> None:
    from opennem.db.clickhouse.views import CLICKHOUSE_MATERIALIZED_VIEWS

    # Drop MVs first (reverse order)
    for view in reversed(list(CLICKHOUSE_MATERIALIZED_VIEWS.values())):
        client.execute(f"DROP TABLE IF EXISTS {view.name}")

    # Drop base tables
    client.execute("DROP TABLE IF EXISTS market_summary")
    client.execute("DROP TABLE IF EXISTS unit_intervals")
