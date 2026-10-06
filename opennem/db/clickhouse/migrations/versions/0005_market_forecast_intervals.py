"""
Add market_forecast_intervals, the store for region-level forecasts (#675).

One row per (network, metric, region, interval) at the source's native resolution, so each
forecast source replaces its own rows without touching another's. A wide row per interval
(as #500 first proposed) would let a rooftop run's version bump blank the PREDISPATCH
columns and the reverse. The latest run per key wins on `version` (run_time in ms).

`interval` is naive network time like every other CH table; `run_time` is a real instant.
"""

from clickhouse_driver import Client

REQUIRES_BACKFILL: list[str] = []

MARKET_FORECAST_INTERVALS_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_forecast_intervals (
    interval DateTime64(3),
    network_id LowCardinality(String),
    network_region LowCardinality(String),
    metric LowCardinality(String),
    source LowCardinality(String),
    value Float64,
    run_time DateTime64(3, 'UTC'),
    horizon_minutes UInt32,
    version UInt64
) ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(interval)
ORDER BY (network_id, metric, network_region, interval)
"""


def up(client: Client) -> None:
    client.execute(MARKET_FORECAST_INTERVALS_SCHEMA)


def down(client: Client) -> None:
    client.execute("DROP TABLE IF EXISTS market_forecast_intervals")
