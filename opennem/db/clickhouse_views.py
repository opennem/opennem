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
    schema: str
    backfill_query: str


UNIT_INTERVALS_DAILY_VIEW = MaterializedView(
    name="unit_intervals_daily_mv",
    schema="""
        CREATE MATERIALIZED VIEW unit_intervals_daily_mv
        ENGINE = SummingMergeTree()
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
            avg(generated) as generated_avg,
            max(generated) as generated_max,
            min(generated) as generated_min,
            sum(energy) as energy_sum,
            sum(emissions) as emissions_sum,
            avg(emission_factor) as emission_factor_avg,
            sum(market_value) as market_value_sum,
            count() as count
        FROM unit_intervals
        WHERE interval >= %(start)s AND interval < %(end)s
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

UNIT_INTERVALS_MONTHLY_VIEW = MaterializedView(
    name="unit_intervals_monthly_mv",
    schema="""
        CREATE MATERIALIZED VIEW unit_intervals_monthly_mv
        ENGINE = SummingMergeTree()
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
            fueltech_group_id
    """,
    backfill_query="""
        INSERT INTO unit_intervals_monthly_mv
        SELECT
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
        WHERE interval >= %(start)s AND interval < %(end)s
        GROUP BY
            month,
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
    schema="""
        CREATE MATERIALIZED VIEW fueltech_intervals_mv
        ENGINE = SummingMergeTree()
        ORDER BY (interval, network_id, network_region, fueltech_group_id)
        AS SELECT
            interval,
            network_id,
            network_region,
            fueltech_group_id,
            any(renewable) as renewable,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count
        FROM unit_intervals
        GROUP BY
            interval,
            network_id,
            network_region,
            fueltech_group_id
    """,
    backfill_query="""
        INSERT INTO fueltech_intervals_mv
        SELECT
            interval,
            network_id,
            network_region,
            fueltech_group_id,
            any(renewable) as renewable,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count
        FROM unit_intervals
        WHERE interval >= %(start)s AND interval < %(end)s
        GROUP BY
            interval,
            network_id,
            network_region,
            fueltech_group_id
    """,
)

FUELTECH_INTERVALS_DAILY_VIEW = MaterializedView(
    name="fueltech_intervals_daily_mv",
    schema="""
        CREATE MATERIALIZED VIEW fueltech_intervals_daily_mv
        ENGINE = SummingMergeTree()
        ORDER BY (date, network_id, network_region, fueltech_group_id)
        AS SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            fueltech_group_id,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count
        FROM unit_intervals
        GROUP BY date, network_id, network_region, fueltech_group_id
    """,
    backfill_query="""
        INSERT INTO fueltech_intervals_daily_mv
        SELECT
            toDate(interval) as date,
            network_id,
            network_region,
            fueltech_group_id,
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as unit_count
        FROM unit_intervals
        WHERE interval >= %(start)s AND interval < %(end)s
        GROUP BY date, network_id, network_region, fueltech_group_id
    """,
)
