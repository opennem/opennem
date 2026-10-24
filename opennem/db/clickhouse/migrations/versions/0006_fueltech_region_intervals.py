"""
Add fueltech_region_intervals, an additive per (interval, network, region, fueltech) table (#763).

Holds the same sums unit_intervals would give for generated / energy / emissions / market_value,
~150 rows per 5 minute interval against ~1200 in unit_intervals, so cold tracker windows read far
fewer rows. Written from the same python rows (same version) that write unit_intervals, NOT by a
materialized view, so a partial re-insert cannot replace a full row with a partial sum (#755).

ReplacingMergeTree(version), same semantics as unit_intervals. Range rebuild:
`opennem.aggregates.fueltech_region_intervals.rebuild_range`. Empty on creation: backfill it with
`bin/backfill_agg_table.py` before enabling CLICKHOUSE_AGG_TABLE_ROUTING.
"""

from clickhouse_driver import Client

REQUIRES_BACKFILL: list[str] = []

FUELTECH_REGION_INTERVALS_SCHEMA = """
CREATE TABLE IF NOT EXISTS fueltech_region_intervals (
    interval DateTime64(3),
    network_id String,
    network_region String,
    fueltech_id String,
    fueltech_group_id String,
    generated Nullable(Float64),
    energy Nullable(Float64),
    emissions Nullable(Float64),
    market_value Nullable(Float64),
    unit_count UInt32,
    version UInt64
) ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(interval)
ORDER BY (interval, network_id, network_region, fueltech_id, fueltech_group_id)
"""


def up(client: Client) -> None:
    client.execute(FUELTECH_REGION_INTERVALS_SCHEMA)


def down(client: Client) -> None:
    client.execute("DROP TABLE IF EXISTS fueltech_region_intervals")
