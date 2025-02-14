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
    demand_total_market_value Nullable(Float64),
    version UInt64
) ENGINE = ReplacingMergeTree(version)
PRIMARY KEY (interval, network_id, network_region)
ORDER BY (interval, network_id, network_region)
PARTITION BY toYYYYMM(interval)
SETTINGS index_granularity = 8192, allow_experimental_replacing_merge_with_cleanup=1"""

# Unit Intervals table schema
UNIT_INTERVALS_TABLE_SCHEMA = """CREATE TABLE IF NOT EXISTS unit_intervals (
    interval DateTime64(3),
    network_id String,
    network_region String,
    facility_code String,
    unit_code String,
    status_id String,
    fueltech_id String,
    fueltech_group_id String,
    renewable Boolean,
    generated Nullable(Float64),
    energy Nullable(Float64),
    emissions Nullable(Float64),
    emission_factor Nullable(Float64),
    market_value Nullable(Float64),
    version UInt64
) ENGINE = ReplacingMergeTree(version)
PRIMARY KEY (interval, network_id, network_region, facility_code, unit_code)
ORDER BY (interval, network_id, network_region, facility_code, unit_code)
PARTITION BY toYYYYMM(interval)
SETTINGS index_granularity = 8192, allow_experimental_replacing_merge_with_cleanup=1"""
