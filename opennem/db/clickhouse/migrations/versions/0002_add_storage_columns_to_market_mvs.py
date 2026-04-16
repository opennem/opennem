"""
Add generation_renewable_with_storage columns to market_summary MVs.

MV storage doesn't support ALTER ADD COLUMN — must drop + recreate.
Fixes BACKEND-550: source 32 cols vs target 30 cols mismatch.
"""

from clickhouse_driver import Client

REQUIRES_BACKFILL: list[str] = ["market_summary_daily_mv", "market_summary_monthly_mv"]

# Old 30-column schemas for down() — frozen at pre-0002 state
_OLD_DAILY_SCHEMA = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS market_summary_daily_mv
    ENGINE = ReplacingMergeTree(version)
    ORDER BY (date, network_id, network_region)
    AS SELECT
        toDate(interval) as date,
        network_id,
        network_region,
        sum(price) as price_sum,
        countIf(price IS NOT NULL) as price_count,
        sum(demand) as demand_sum,
        sum(demand_total) as demand_total_sum,
        sum(demand_gross) as demand_gross_sum,
        sum(generation_renewable) as generation_renewable_sum,
        sum(demand_energy) as demand_energy_daily,
        sum(demand_total_energy) as demand_total_energy_daily,
        sum(demand_gross_energy) as demand_gross_energy_daily,
        sum(generation_renewable_energy) as generation_renewable_energy_daily,
        sum(demand_market_value) as demand_market_value_daily,
        sum(demand_total_market_value) as demand_total_market_value_daily,
        sum(demand_gross_market_value) as demand_gross_market_value_daily,
        sum(curtailment_solar_total) as curtailment_solar_total_daily,
        sum(curtailment_wind_total) as curtailment_wind_total_daily,
        sum(curtailment_total) as curtailment_total_daily,
        sum(curtailment_energy_solar_total) as curtailment_energy_solar_total_daily,
        sum(curtailment_energy_wind_total) as curtailment_energy_wind_total_daily,
        sum(curtailment_energy_total) as curtailment_energy_total_daily,
        sum(energy_imports) as energy_imports_daily,
        sum(energy_exports) as energy_exports_daily,
        sum(emissions_imports) as emissions_imports_daily,
        sum(emissions_exports) as emissions_exports_daily,
        sum(market_value_imports) as market_value_imports_daily,
        sum(market_value_exports) as market_value_exports_daily,
        count() as interval_count,
        toUInt64(count(distinct interval)) * 1000000000 + max(version) as version
    FROM market_summary
    GROUP BY
        date,
        network_id,
        network_region
"""

_OLD_MONTHLY_SCHEMA = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS market_summary_monthly_mv
    ENGINE = ReplacingMergeTree(version)
    ORDER BY (month, network_id, network_region)
    AS SELECT
        toStartOfMonth(interval) as month,
        network_id,
        network_region,
        sum(price) as price_sum,
        countIf(price IS NOT NULL) as price_count,
        sum(demand) as demand_sum,
        sum(demand_total) as demand_total_sum,
        sum(demand_gross) as demand_gross_sum,
        sum(generation_renewable) as generation_renewable_sum,
        sum(demand_energy) as demand_energy_monthly,
        sum(demand_total_energy) as demand_total_energy_monthly,
        sum(demand_gross_energy) as demand_gross_energy_monthly,
        sum(generation_renewable_energy) as generation_renewable_energy_monthly,
        sum(demand_market_value) as demand_market_value_monthly,
        sum(demand_total_market_value) as demand_total_market_value_monthly,
        sum(demand_gross_market_value) as demand_gross_market_value_monthly,
        sum(curtailment_solar_total) as curtailment_solar_total_monthly,
        sum(curtailment_wind_total) as curtailment_wind_total_monthly,
        sum(curtailment_total) as curtailment_total_monthly,
        sum(curtailment_energy_solar_total) as curtailment_energy_solar_total_monthly,
        sum(curtailment_energy_wind_total) as curtailment_energy_wind_total_monthly,
        sum(curtailment_energy_total) as curtailment_energy_total_monthly,
        sum(energy_imports) as energy_imports_monthly,
        sum(energy_exports) as energy_exports_monthly,
        sum(emissions_imports) as emissions_imports_monthly,
        sum(emissions_exports) as emissions_exports_monthly,
        sum(market_value_imports) as market_value_imports_monthly,
        sum(market_value_exports) as market_value_exports_monthly,
        count() as interval_count,
        toUInt64(count(distinct interval)) * 1000000000 + max(version) as version
    FROM market_summary
    GROUP BY
        month,
        network_id,
        network_region
"""


def up(client: Client) -> None:
    from opennem.db.clickhouse.views import (
        MARKET_SUMMARY_DAILY_VIEW,
        MARKET_SUMMARY_MONTHLY_VIEW,
    )

    # Drop + recreate with new schema (32 cols including storage columns)
    client.execute("DROP TABLE IF EXISTS market_summary_daily_mv")
    client.execute(MARKET_SUMMARY_DAILY_VIEW.schema)

    client.execute("DROP TABLE IF EXISTS market_summary_monthly_mv")
    client.execute(MARKET_SUMMARY_MONTHLY_VIEW.schema)


def down(client: Client) -> None:
    # Revert to old 30-column schemas
    client.execute("DROP TABLE IF EXISTS market_summary_daily_mv")
    client.execute(_OLD_DAILY_SCHEMA)

    client.execute("DROP TABLE IF EXISTS market_summary_monthly_mv")
    client.execute(_OLD_MONTHLY_SCHEMA)
