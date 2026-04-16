"""
Fix market_summary_daily_mv source_timestamp_column.

Code-only change — adds source_timestamp_column="interval" to MARKET_SUMMARY_DAILY_VIEW
so backfill without explicit date range queries the correct column from market_summary.
No ClickHouse DDL needed.
"""

from clickhouse_driver import Client

REQUIRES_BACKFILL: list[str] = []


def up(client: Client) -> None:
    # Code-only fix applied alongside this migration file.
    pass


def down(client: Client) -> None:
    # Code-only — nothing to reverse in CH.
    pass
