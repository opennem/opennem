"""
ClickHouse table schemas for OpenNEM.

This module contains the table schemas for ClickHouse tables used in OpenNEM.
"""

# Market Summary table schema
MARKET_SUMMARY_TABLE_SCHEMA = """CREATE TABLE IF NOT EXISTS market_summary (
    interval DateTime64(3),
    network_id String,
    network_region String,
    price Nullable(Float64),
    demand Nullable(Float64),
    demand_total Nullable(Float64),
    demand_energy Nullable(Float64),
    demand_total_energy Nullable(Float64),
    demand_market_value Nullable(Float64),
    demand_total_market_value Nullable(Float64)
) ENGINE = ReplacingMergeTree()
PRIMARY KEY (interval, network_id, network_region)
ORDER BY (interval, network_id, network_region)
PARTITION BY toYYYYMM(interval)
SETTINGS index_granularity = 8192"""
