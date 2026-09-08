"""
Add per-metric 5-minute slot bitmaps to the daily materialised views.

`generated_slots` on unit/fueltech/renewable daily views and `<metric>_slots` on
market_summary_daily_mv record which raw intervals carried a non-NULL value, so the
API can compute exact MW averages (raw-equivalent denominators) from the views.

MV storage doesn't support ALTER ADD COLUMN — must drop + recreate, then FULL backfill.
"""

from clickhouse_driver import Client

REQUIRES_BACKFILL: list[str] = [
    "unit_intervals_daily_mv",
    "fueltech_intervals_daily_mv",
    "renewable_intervals_daily_mv",
    "market_summary_daily_mv",
]

_VIEWS = [
    "UNIT_INTERVALS_DAILY_VIEW",
    "FUELTECH_INTERVALS_DAILY_VIEW",
    "RENEWABLE_INTERVALS_DAILY_VIEW",
    "MARKET_SUMMARY_DAILY_VIEW",
]

# Pre-0004 schemas for down() — frozen.
_OLD_SCHEMAS: dict[str, str] = {
    "UNIT_INTERVALS_DAILY_VIEW": """
        CREATE MATERIALIZED VIEW unit_intervals_daily_mv
        ENGINE = ReplacingMergeTree(version)
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
            sum(generated) as generated,
            sum(energy) as energy,
            sum(coalesce(energy_storage, 0)) as energy_storage_sum,
            countIf(energy_storage IS NOT NULL) as energy_storage_count,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as interval_count,
            toUInt64(count(distinct interval)) * 1000000000 + max(version) as version
        FROM unit_intervals
        GROUP BY
            date,
            network_id,
            network_region,
            facility_code,
            unit_code,
            fueltech_id,
            fueltech_group_id
    """,
    "FUELTECH_INTERVALS_DAILY_VIEW": """
        CREATE MATERIALIZED VIEW fueltech_intervals_daily_mv
        ENGINE = ReplacingMergeTree(version)
        ORDER BY (date, network_id, network_region, fueltech_id, fueltech_group_id)
        AS SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(coalesce(energy_storage, 0)) as energy_storage_sum,
            countIf(energy_storage IS NOT NULL) as energy_storage_count,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            count(distinct interval) as interval_count,
            toUInt64(count(distinct interval)) * 1000000000 + max(version) as version
        FROM unit_intervals
        GROUP BY
            date,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id
    """,
    "RENEWABLE_INTERVALS_DAILY_VIEW": """
        CREATE MATERIALIZED VIEW renewable_intervals_daily_mv
        ENGINE = ReplacingMergeTree(version)
        ORDER BY (date, network_id, network_region, renewable)
        AS SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            renewable,
            sum(greatest(generated, 0)) as generated,
            sum(greatest(energy, 0)) as energy,
            sum(coalesce(energy_storage, 0)) as energy_storage_sum,
            countIf(energy_storage IS NOT NULL) as energy_storage_count,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            count(distinct interval) as interval_count,
            toUInt64(count(distinct interval)) * 1000000000 + max(version) as version
        FROM unit_intervals
        WHERE fueltech_id not in ('pumps', 'battery', 'battery_charging', 'battery_discharging')
        GROUP BY date, network_id, network_region, renewable
    """,
    "MARKET_SUMMARY_DAILY_VIEW": """
        CREATE MATERIALIZED VIEW market_summary_daily_mv
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
            sum(generation_renewable_with_storage) as generation_renewable_with_storage_sum,
            sum(demand_energy) as demand_energy_daily,
            sum(demand_total_energy) as demand_total_energy_daily,
            sum(demand_gross_energy) as demand_gross_energy_daily,
            sum(generation_renewable_energy) as generation_renewable_energy_daily,
            sum(generation_renewable_with_storage_energy) as generation_renewable_with_storage_energy_daily,
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
    """,
}


def up(client: Client) -> None:
    from opennem.db.clickhouse import views

    for name in _VIEWS:
        view = getattr(views, name)
        client.execute(f"DROP TABLE IF EXISTS {view.name}")
        client.execute(view.schema)


def down(client: Client) -> None:
    from opennem.db.clickhouse import views

    for name in _VIEWS:
        view = getattr(views, name)
        client.execute(f"DROP TABLE IF EXISTS {view.name}")
        client.execute(_OLD_SCHEMAS[name])
