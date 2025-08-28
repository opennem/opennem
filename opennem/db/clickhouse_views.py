"""
Clickhouse materialized view definitions and utilities.

This module contains the dataclass definitions for materialized views and their
implementations in the OpenNEM system.
"""

from dataclasses import dataclass


@dataclass
class MaterializedView:
    """
    Dataclass representing a Clickhouse materialized view definition.

    Attributes:
        name: The name of the materialized view
        schema: The SQL schema definition for the view
        backfill_query: The SQL query used to populate/backfill the view
    """

    name: str
    timestamp_column: str
    schema: str
    backfill_query: str


UNIT_INTERVALS_DAILY_VIEW = MaterializedView(
    name="unit_intervals_daily_mv",
    timestamp_column="date",
    schema="""
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
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as count,
            max(version) as version
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
    backfill_query="""
        INSERT INTO unit_intervals_daily_mv
        SELECT
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
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as count,
            max(version) as version
        FROM unit_intervals FINAL
        WHERE interval >= %(start)s AND interval <= %(end)s
        GROUP BY
            date,
            network_id,
            network_region,
            facility_code,
            unit_code,
            fueltech_id,
            fueltech_group_id
    """,
)

FUELTECH_INTERVALS_VIEW = MaterializedView(
    name="fueltech_intervals_mv",
    timestamp_column="interval",
    schema="""
        CREATE MATERIALIZED VIEW fueltech_intervals_mv
        ENGINE = ReplacingMergeTree(version)
        ORDER BY (interval, network_id, network_region, fueltech_id, fueltech_group_id)
        AS SELECT
            interval,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            max(version) as version
        FROM unit_intervals
        GROUP BY
            interval,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id
    """,
    backfill_query="""
        INSERT INTO fueltech_intervals_mv
        SELECT
            interval,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            max(version) as version
        FROM unit_intervals FINAL
        WHERE interval >= %(start)s AND interval <= %(end)s
        GROUP BY
            interval,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id
    """,
)

FUELTECH_INTERVALS_DAILY_VIEW = MaterializedView(
    name="fueltech_intervals_daily_mv",
    timestamp_column="date",
    schema="""
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
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            count(distinct interval) as interval_count,
            max(version) as version
        FROM unit_intervals
        GROUP BY
            date,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id
    """,
    backfill_query="""
        INSERT INTO fueltech_intervals_daily_mv
        SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            count(distinct interval) as interval_count,
            max(version) as version
        FROM unit_intervals FINAL
        WHERE interval >= %(start)s AND interval <= %(end)s
        GROUP BY
            date,
            network_id,
            network_region,
            fueltech_id,
            fueltech_group_id
    """,
)

RENEWABLE_INTERVALS_VIEW = MaterializedView(
    name="renewable_intervals_mv",
    timestamp_column="interval",
    schema="""
        CREATE MATERIALIZED VIEW renewable_intervals_mv
        ENGINE = ReplacingMergeTree(version)
        ORDER BY (interval, network_id, network_region, renewable)
        AS SELECT
            interval,
            network_id,
            network_region,
            renewable,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            max(version) as version
        FROM unit_intervals
        WHERE fueltech_id not in ('pumps')
        GROUP BY interval, network_id, network_region, renewable
    """,
    backfill_query="""
        INSERT INTO renewable_intervals_mv
        SELECT
            interval,
            network_id,
            network_region,
            renewable,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            max(version) as version
        FROM unit_intervals FINAL
        WHERE fueltech_id not in ('pumps') and interval >= %(start)s AND interval <= %(end)s
        GROUP BY interval, network_id, network_region, renewable
    """,
)

RENEWABLE_INTERVALS_DAILY_VIEW = MaterializedView(
    name="renewable_intervals_daily_mv",
    timestamp_column="date",
    schema="""
        CREATE MATERIALIZED VIEW renewable_intervals_daily_mv
        ENGINE = ReplacingMergeTree(version)
        ORDER BY (date, network_id, network_region, renewable)
        AS SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            renewable,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            count(distinct interval) as interval_count,
            max(version) as version
        FROM unit_intervals
        WHERE fueltech_id not in ('pumps')
        GROUP BY date, network_id, network_region, renewable
    """,
    backfill_query="""
        INSERT INTO renewable_intervals_daily_mv
        SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            renewable,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count,
            count(distinct interval) as interval_count,
            max(version) as version
        FROM unit_intervals FINAL
        WHERE fueltech_id not in ('pumps') and interval >= %(start)s AND interval <= %(end)s
        GROUP BY date, network_id, network_region, renewable
    """,
)

# Market Summary Materialized Views
MARKET_SUMMARY_DAILY_VIEW = MaterializedView(
    name="market_summary_daily_mv",
    timestamp_column="date",
    schema="""
        CREATE MATERIALIZED VIEW market_summary_daily_mv
        ENGINE = ReplacingMergeTree(version)
        ORDER BY (date, network_id, network_region)
        AS SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            avg(price) as price_avg,
            sum(demand) as demand_sum,
            sum(demand_total) as demand_total_sum,
            sum(demand_energy) as demand_energy_daily,
            sum(demand_total_energy) as demand_total_energy_daily,
            sum(demand_market_value) as demand_market_value_daily,
            sum(demand_total_market_value) as demand_total_market_value_daily,
            sum(curtailment_solar_total) as curtailment_solar_total_daily,
            sum(curtailment_wind_total) as curtailment_wind_total_daily,
            sum(curtailment_total) as curtailment_total_daily,
            sum(curtailment_energy_solar_total) as curtailment_energy_solar_total_daily,
            sum(curtailment_energy_wind_total) as curtailment_energy_wind_total_daily,
            sum(curtailment_energy_total) as curtailment_energy_total_daily,
            count() as interval_count,
            max(version) as version
        FROM market_summary
        GROUP BY
            date,
            network_id,
            network_region
    """,
    backfill_query="""
        INSERT INTO market_summary_daily_mv
        SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            avg(price) as price_avg,
            sum(demand) as demand_sum,
            sum(demand_total) as demand_total_sum,
            sum(demand_energy) as demand_energy_daily,
            sum(demand_total_energy) as demand_total_energy_daily,
            sum(demand_market_value) as demand_market_value_daily,
            sum(demand_total_market_value) as demand_total_market_value_daily,
            sum(curtailment_solar_total) as curtailment_solar_total_daily,
            sum(curtailment_wind_total) as curtailment_wind_total_daily,
            sum(curtailment_total) as curtailment_total_daily,
            sum(curtailment_energy_solar_total) as curtailment_energy_solar_total_daily,
            sum(curtailment_energy_wind_total) as curtailment_energy_wind_total_daily,
            sum(curtailment_energy_total) as curtailment_energy_total_daily,
            count() as interval_count,
            max(version) as version
        FROM market_summary FINAL
        WHERE interval >= %(start)s AND interval <= %(end)s
        GROUP BY
            date,
            network_id,
            network_region
    """,
)

MARKET_SUMMARY_MONTHLY_VIEW = MaterializedView(
    name="market_summary_monthly_mv",
    timestamp_column="month",
    schema="""
        CREATE MATERIALIZED VIEW market_summary_monthly_mv
        ENGINE = ReplacingMergeTree(version)
        ORDER BY (month, network_id, network_region)
        AS SELECT
            toStartOfMonth(interval) as month,
            network_id,
            network_region,
            avg(price) as price_avg,
            sum(demand) as demand_sum,
            sum(demand_total) as demand_total_sum,
            sum(demand_energy) as demand_energy_monthly,
            sum(demand_total_energy) as demand_total_energy_monthly,
            sum(demand_market_value) as demand_market_value_monthly,
            sum(demand_total_market_value) as demand_total_market_value_monthly,
            sum(curtailment_solar_total) as curtailment_solar_total_monthly,
            sum(curtailment_wind_total) as curtailment_wind_total_monthly,
            sum(curtailment_total) as curtailment_total_monthly,
            sum(curtailment_energy_solar_total) as curtailment_energy_solar_total_monthly,
            sum(curtailment_energy_wind_total) as curtailment_energy_wind_total_monthly,
            sum(curtailment_energy_total) as curtailment_energy_total_monthly,
            count() as interval_count,
            max(version) as version
        FROM market_summary
        GROUP BY
            month,
            network_id,
            network_region
    """,
    backfill_query="""
        INSERT INTO market_summary_monthly_mv
        SELECT
            toStartOfMonth(interval) as month,
            network_id,
            network_region,
            avg(price) as price_avg,
            sum(demand) as demand_sum,
            sum(demand_total) as demand_total_sum,
            sum(demand_energy) as demand_energy_monthly,
            sum(demand_total_energy) as demand_total_energy_monthly,
            sum(demand_market_value) as demand_market_value_monthly,
            sum(demand_total_market_value) as demand_total_market_value_monthly,
            sum(curtailment_solar_total) as curtailment_solar_total_monthly,
            sum(curtailment_wind_total) as curtailment_wind_total_monthly,
            sum(curtailment_total) as curtailment_total_monthly,
            sum(curtailment_energy_solar_total) as curtailment_energy_solar_total_monthly,
            sum(curtailment_energy_wind_total) as curtailment_energy_wind_total_monthly,
            sum(curtailment_energy_total) as curtailment_energy_total_monthly,
            count() as interval_count,
            max(version) as version
        FROM market_summary FINAL
        WHERE interval >= %(start)s AND interval <= %(end)s
        GROUP BY
            month,
            network_id,
            network_region
    """,
)

CLICKHOUSE_MATERIALIZED_VIEWS = {
    "unit_intervals_daily_mv": UNIT_INTERVALS_DAILY_VIEW,
    "fueltech_intervals_mv": FUELTECH_INTERVALS_VIEW,
    "fueltech_intervals_daily_mv": FUELTECH_INTERVALS_DAILY_VIEW,
    "renewable_intervals_mv": RENEWABLE_INTERVALS_VIEW,
    "renewable_intervals_daily_mv": RENEWABLE_INTERVALS_DAILY_VIEW,
    "market_summary_daily_mv": MARKET_SUMMARY_DAILY_VIEW,
    "market_summary_monthly_mv": MARKET_SUMMARY_MONTHLY_VIEW,
}
