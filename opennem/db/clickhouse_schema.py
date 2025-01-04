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
    market_value Nullable(Float64)
) ENGINE = ReplacingMergeTree()
PRIMARY KEY (interval, network_id, network_region, facility_code, unit_code)
ORDER BY (interval, network_id, network_region, facility_code, unit_code)
PARTITION BY toYYYYMM(interval)
SETTINGS index_granularity = 8192"""

# Unit Intervals Daily Materialized View
UNIT_INTERVALS_DAILY_MV = """
CREATE MATERIALIZED VIEW IF NOT EXISTS unit_intervals_daily_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, network_id, network_region, facility_code, unit_code, fueltech_id, fueltech_group_id)
AS SELECT
    toDate(interval) as date,
    network_id,
    network_region,
    facility_code,
    unit_code,
    fueltech_id,
    fueltech_group_id,
    any(renewable) as renewable,
    any(status_id) as status_id,
    avg(generated) as generated_avg,
    max(generated) as generated_max,
    min(generated) as generated_min,
    sum(energy) as energy_sum,
    sum(emissions) as emissions_sum,
    avg(emission_factor) as emission_factor_avg,
    sum(market_value) as market_value_sum,
    count() as count
FROM unit_intervals
GROUP BY
    date,
    network_id,
    network_region,
    facility_code,
    unit_code,
    fueltech_id,
    fueltech_group_id"""

# Unit Intervals Monthly Materialized View
UNIT_INTERVALS_MONTHLY_MV = """
CREATE MATERIALIZED VIEW IF NOT EXISTS unit_intervals_monthly_mv
ENGINE = SummingMergeTree()
PARTITION BY toYear(month)
ORDER BY (month, network_id, network_region, facility_code, unit_code, fueltech_id, fueltech_group_id)
AS SELECT
    toStartOfMonth(interval) as month,
    network_id,
    network_region,
    facility_code,
    unit_code,
    fueltech_id,
    fueltech_group_id,
    any(renewable) as renewable,
    any(status_id) as status_id,
    avg(generated) as generated_avg,
    max(generated) as generated_max,
    min(generated) as generated_min,
    sum(energy) as energy_sum,
    sum(emissions) as emissions_sum,
    avg(emission_factor) as emission_factor_avg,
    sum(market_value) as market_value_sum,
    count() as count
FROM unit_intervals
GROUP BY
    month,
    network_id,
    network_region,
    facility_code,
    unit_code,
    fueltech_id,
    fueltech_group_id"""
