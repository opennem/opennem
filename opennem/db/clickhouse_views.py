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
            sum(generated) as generated,
            sum(energy) as energy,
            sum(emissions) as emissions,
            sum(market_value) as market_value,
            count() as count
        FROM (
            SELECT *
            FROM unit_intervals
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
            count() as count
        FROM (
            SELECT *
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
    timestamp_column="date",
    schema="""
        CREATE MATERIALIZED VIEW unit_intervals_monthly_mv
        ENGINE = SummingMergeTree()
        ORDER BY (date, network_id, network_region, facility_code, unit_code, fueltech_id, fueltech_group_id)
        AS SELECT
            toStartOfMonth(interval) as date,
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
            count() as count
        FROM (
            SELECT *
            FROM unit_intervals
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
        INSERT INTO unit_intervals_monthly_mv
        SELECT
            toStartOfMonth(interval) as date,
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
            count() as count
        FROM (
            SELECT *
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
        ENGINE = SummingMergeTree()
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
            count() as unit_count
        FROM (
            SELECT *
            FROM unit_intervals
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
            count() as unit_count
        FROM (
            SELECT *
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
        ENGINE = SummingMergeTree()
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
            count(distinct interval) as interval_count
        FROM (
            SELECT *
            FROM unit_intervals
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
            count(distinct interval) as interval_count
        FROM (
            SELECT *
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
        ENGINE = SummingMergeTree()
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
            count() as unit_count
        FROM (
            SELECT *
            FROM unit_intervals
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
            count() as unit_count
        FROM (
            SELECT *
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
        GROUP BY interval, network_id, network_region, renewable
    """,
)

RENEWABLE_INTERVALS_DAILY_VIEW = MaterializedView(
    name="renewable_intervals_daily_mv",
    timestamp_column="date",
    schema="""
        CREATE MATERIALIZED VIEW renewable_intervals_daily_mv
        ENGINE = SummingMergeTree()
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
            count(distinct interval) as interval_count
        FROM (
            SELECT *
            FROM unit_intervals
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
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
            count(distinct interval) as interval_count
        FROM (
            SELECT *
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            ORDER BY interval, network_id, network_region, facility_code, unit_code, version DESC
        )
        GROUP BY date, network_id, network_region, renewable
    """,
)

CLICKHOUSE_MATERIALIZED_VIEWS = {
    "unit_intervals_daily_mv": UNIT_INTERVALS_DAILY_VIEW,
    "unit_intervals_monthly_mv": UNIT_INTERVALS_MONTHLY_VIEW,
    "fueltech_intervals_mv": FUELTECH_INTERVALS_VIEW,
    "fueltech_intervals_daily_mv": FUELTECH_INTERVALS_DAILY_VIEW,
    "renewable_intervals_mv": RENEWABLE_INTERVALS_VIEW,
    "renewable_intervals_daily_mv": RENEWABLE_INTERVALS_DAILY_VIEW,
}
