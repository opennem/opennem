"""
Unit Intervals aggregation module.

This module handles the aggregation of unit interval data from PostgreSQL to ClickHouse.
It calculates energy values, emissions, and market values for each unit and stores them in ClickHouse.
"""

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta

import polars as pl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import get_write_session
from opennem.db.clickhouse import (
    create_table_if_not_exists,
    get_clickhouse_client,
    table_exists,
)
from opennem.db.clickhouse_schema import UNIT_INTERVALS_TABLE_SCHEMA
from opennem.db.clickhouse_views import (
    FUELTECH_INTERVALS_DAILY_VIEW,
    FUELTECH_INTERVALS_VIEW,
    RENEWABLE_INTERVALS_DAILY_VIEW,
    RENEWABLE_INTERVALS_VIEW,
    UNIT_INTERVALS_DAILY_VIEW,
    MaterializedView,
)
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.aggregates.unit_intervals")

# List of all materialized views to manage
MATERIALIZED_VIEWS = [
    UNIT_INTERVALS_DAILY_VIEW,
    FUELTECH_INTERVALS_VIEW,
    FUELTECH_INTERVALS_DAILY_VIEW,
    RENEWABLE_INTERVALS_VIEW,
    RENEWABLE_INTERVALS_DAILY_VIEW,
]


async def _get_unit_interval_data(
    session: AsyncSession, start_time: datetime, end_time: datetime, network: NetworkSchema | None = None
) -> list[tuple]:
    """
    Get unit interval data from PostgreSQL for a given time range.

    Args:
        session: Database session
        start_time: Start time for data range
        end_time: End date for data range
        network: Optional network filter

    Returns:
        List of tuples containing unit interval data
    """
    # Strip timezone info
    start_time_naive = start_time.replace(tzinfo=None)
    end_time_naive = end_time.replace(tzinfo=None)

    network_where_clause = ""

    if network:
        network_where_clause = f"AND fs.network_id IN ('{"','".join(network.get_network_codes())}')"

    query = text(f"""
    WITH filled_balancing_summary AS (
        SELECT
            time_bucket_gapfill('5 minutes', bs.interval) as interval,
            bs.network_id,
            bs.network_region,
            locf(
                avg(bs.demand)
            ) AS demand,
            locf(
                avg(bs.demand_total)
            ) as demand_total,
            locf(
                avg(bs.price)
            ) AS price
        FROM balancing_summary bs
        WHERE
            bs.interval >= :start_time
            AND bs.interval <= :end_time
        GROUP BY 1, 2, 3
    ),
    filled_solar_data AS (
        SELECT
            time_bucket_gapfill('5 minutes', fs.interval) as interval,
            fs.network_id,
            f.network_region,
            f.code as facility_code,
            u.code as unit_code,
            u.status_id,
            u.fueltech_id,
            'solar' as fueltech_group_id,
            TRUE as renewable,
            locf(coalesce(round(sum(fs.generated), 4), 0)) as generated,
            locf(coalesce(round(sum(fs.energy) / (12 / (60 / n.interval_size)), 4), 0)) as energy
        FROM
            facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        JOIN network n on fs.network_id = n.code
        WHERE
            fs.is_forecast IS FALSE
            AND u.fueltech_id in ('solar_rooftop')
            AND fs.interval >= :start_time
            AND fs.interval <= :end_time
            {network_where_clause}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, n.interval_size
    ),
    facility_data as (
        SELECT
            time_bucket('5 minutes', fs.interval) as interval,
            fs.network_id,
            f.network_region,
            f.code as facility_code,
            u.code as unit_code,
            u.status_id,
            u.fueltech_id,
            ftg.code as fueltech_group_id,
            ftg.renewable as renewable,
            round(sum(fs.generated), 4) as generated,
            round(sum(fs.energy), 4) as energy
        FROM
            facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        JOIN fueltech ft ON ft.code = u.fueltech_id
        JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
        WHERE
            fs.is_forecast IS FALSE
            AND u.fueltech_id not in ('solar_rooftop', 'imports', 'exports', 'interconnector', 'battery')
            AND fs.interval >= :start_time
            AND fs.interval <= :end_time
            {network_where_clause}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
    ),
    combined_data AS (
        -- Regular facility data
        SELECT
            fd.interval,
            fd.network_id,
            fd.network_region,
            fd.facility_code,
            fd.unit_code,
            fd.status_id,
            fd.fueltech_id,
            fd.fueltech_group_id,
            fd.renewable,
            fd.generated,
            fd.energy,
            u.emissions_factor_co2
        FROM
            facility_data fd
        JOIN units u ON fd.unit_code = u.code

        UNION ALL

        -- Solar data (rooftop and utility)
        SELECT
            sd.interval,
            sd.network_id,
            sd.network_region,
            sd.facility_code,
            sd.unit_code,
            sd.status_id,
            sd.fueltech_id,
            sd.fueltech_group_id,
            sd.renewable,
            sd.generated,
            sd.energy,
            u.emissions_factor_co2
        FROM
            filled_solar_data sd
        JOIN units u ON sd.unit_code = u.code
    )
    SELECT
        cd.interval,
        cd.network_id,
        cd.network_region,
        cd.facility_code,
        cd.unit_code,
        cd.status_id,
        cd.fueltech_id,
        cd.fueltech_group_id,
        cd.renewable,
        cd.generated,
        cd.energy,
        CASE
            WHEN cd.energy > 0 THEN coalesce(round(cd.emissions_factor_co2 * cd.energy, 4), 0)
            ELSE 0
        END as emissions,
        CASE
            WHEN cd.energy > 0 THEN coalesce(round(cd.emissions_factor_co2, 4), 0)
            ELSE 0
        END as emission_factor,
        CASE
            WHEN cd.energy > 0 THEN round(cd.energy * bs.price, 4)
            ELSE 0
        END as market_value
    FROM
        combined_data cd
    LEFT JOIN filled_balancing_summary bs ON
        bs.interval = cd.interval
        AND bs.network_region = cd.network_region
    WHERE
        cd.interval >= :start_time
        AND cd.interval < :end_time
        and cd.network_id not in ('OPENNEM_ROOFTOP_BACKFILL')
    ORDER BY 1,2,3,4,5
    """)

    result = await session.execute(query, {"start_time": start_time_naive, "end_time": end_time_naive})
    return result.fetchall()


def _prepare_unit_interval_data(records: Sequence[tuple]) -> list[tuple]:
    """
    Prepare unit interval data for ClickHouse by converting to the correct format.

    Args:
        records: Raw records from PostgreSQL

    Returns:
        List of tuples ready for ClickHouse insertion
    """
    if not records:
        return []

    # Convert records to polars DataFrame
    df = pl.DataFrame(
        records,
        schema={
            "interval": pl.Datetime,
            "network_id": pl.String,
            "network_region": pl.String,
            "facility_code": pl.String,
            "unit_code": pl.String,
            "status_id": pl.String,
            "fueltech_id": pl.String,
            "fueltech_group_id": pl.String,
            "renewable": pl.Boolean,
            "generated": pl.Float64,
            "energy": pl.Float64,
            "emissions": pl.Float64,
            "emission_factor": pl.Float64,
            "market_value": pl.Float64,
        },
    )

    # Round numeric values to 4 decimal places
    numeric_cols = ["generated", "energy", "emissions", "emission_factor", "market_value"]
    df = df.with_columns([pl.col(col).round(4) for col in numeric_cols])

    # Add version column based on current timestamp
    df = df.with_columns(pl.lit(int(datetime.now().timestamp())).alias("version"))

    # if network_region is SNOWY1 then set it to NSW1
    df = df.with_columns(
        pl.when(pl.col("network_region") == "SNOWY1")
        .then(pl.lit("NSW1"))
        .otherwise(pl.col("network_region"))
        .alias("network_region")
    )

    # filter out solar and renewable records before 26 October 2015
    # df = df.filter(
    #     (pl.col("fueltech_group_id") != "solar") | (pl.col("interval") >= datetime.fromisoformat("2015-10-26T00:00:00"))
    # )

    # # filter out wind records before we had non-scheduled generation data on 2009-07-01
    # df = df.filter(
    #     (pl.col("fueltech_group_id") != "wind") | (pl.col("interval") >= datetime.fromisoformat("2009-07-01T00:00:00"))
    # )

    # Ensure columns are in the exact order matching the table schema
    result_df = df.select(
        [
            "interval",
            "network_id",
            "network_region",
            "facility_code",
            "unit_code",
            "status_id",
            "fueltech_id",
            "fueltech_group_id",
            "renewable",
            "generated",
            "energy",
            "emissions",
            "emission_factor",
            "market_value",
            "version",
        ]
    )

    # Convert back to list of tuples for ClickHouse insertion
    return result_df.rows()


def _ensure_clickhouse_schema() -> None:
    """
    Ensure ClickHouse schema exists by creating tables and views if needed.
    """
    client = get_clickhouse_client()
    if not table_exists(client, "unit_intervals"):
        create_table_if_not_exists(client, "unit_intervals", UNIT_INTERVALS_TABLE_SCHEMA)
        logger.info("Created unit_intervals")

    for view in MATERIALIZED_VIEWS:
        if not table_exists(client, view.name):
            client.execute(view.schema)
            logger.info(f"Created {view.name}")


def _refresh_clickhouse_schema() -> None:
    """
    Refresh ClickHouse schema by dropping and recreating tables and views.
    """
    print("This will drop and recreate all unit_intervals tables and views. Are you sure you want to continue? (y/n)")
    if input().lower() != "y":
        logger.info("User cancelled")
        return

    client = get_clickhouse_client()

    # Drop views first (in reverse order of creation to handle dependencies)
    for view in reversed(MATERIALIZED_VIEWS):
        client.execute(f"DROP TABLE IF EXISTS {view.name}")
        logger.info(f"Dropped {view.name}")

    client.execute("DROP TABLE IF EXISTS unit_intervals")
    logger.info("Dropped unit_intervals")

    _ensure_clickhouse_schema()


async def process_unit_intervals_backlog(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    chunk_size: timedelta = timedelta(days=7),
    network: NetworkSchema | None = None,
) -> None:
    """
    Process historical unit interval data in chunks.

    Args:
        session: Database session
        start_date: Start date for processing
        end_date: End date for processing
        chunk_size: Size of each processing chunk
    """
    current_start = start_date
    client = get_clickhouse_client()
    _ensure_clickhouse_schema()

    logger.info(f"Processing unit intervals from {current_start} to {end_date} for network {network.code}")

    while current_start <= end_date:
        # For the last chunk, ensure we include the full end date
        chunk_end = min(current_start + chunk_size, end_date + timedelta(minutes=5))

        # Get and process data for this chunk
        records = await _get_unit_interval_data(session, current_start, chunk_end, network)
        if records:
            prepared_data = _prepare_unit_interval_data(records)

            # Batch insert into ClickHouse
            client.execute(
                """
                INSERT INTO unit_intervals
                (
                    interval, network_id, network_region, facility_code, unit_code,
                    status_id, fueltech_id, fueltech_group_id, renewable,
                    generated, energy, emissions, emission_factor, market_value,
                    version
                )
                VALUES
                """,
                prepared_data,
            )

            logger.info(f"Processed {len(prepared_data)} records from {current_start} to {chunk_end}")
        else:
            logger.warning(f"No records found for {current_start} to {chunk_end}")

        current_start = chunk_end


async def run_unit_intervals_aggregate_to_now() -> int:
    """
    Run the unit intervals aggregation from the last processed interval to now.

    Returns:
        int: Number of records processed
    """
    client = get_clickhouse_client()

    # get the max interval from unit_intervals using FINAL modifier
    result = client.execute("SELECT MAX(interval) FROM unit_intervals FINAL")
    max_interval = result[0][0]

    date_from = max_interval + timedelta(minutes=5)
    date_to = get_last_completed_interval_for_network(network=NetworkNEM)

    if date_from > date_to:
        logger.info("No new data to process")
        return 0

    if date_from - date_to > timedelta(days=1):
        logger.info("Date range is greater than 1 day, skipping")
        return 0

    # run unit intervals from max_interval to now
    async with get_write_session() as session:
        records = await _get_unit_interval_data(session, date_from, date_to)
        prepared_data = _prepare_unit_interval_data(records)

    client.execute(
        """
        INSERT INTO unit_intervals
        (
            interval, network_id, network_region, facility_code, unit_code,
            status_id, fueltech_id, fueltech_group_id, renewable,
            generated, energy, emissions, emission_factor, market_value,
            version
        )
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {date_from} to {date_to}")

    return len(prepared_data)


async def run_unit_intervals_aggregate_for_last_intervals(num_intervals: int) -> int:
    """
    Run the unit intervals aggregation for the last num_intervals.

    Args:
        num_intervals: Number of 5-minute intervals to process

    Returns:
        int: Number of records processed
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = end_date - timedelta(minutes=num_intervals * 5)

    async with get_write_session() as session:
        records = await _get_unit_interval_data(session, start_date, end_date)
        prepared_data = _prepare_unit_interval_data(records)

    client = get_clickhouse_client()

    client.execute(
        """
        INSERT INTO unit_intervals
        (
            interval, network_id, network_region, facility_code, unit_code,
            status_id, fueltech_id, fueltech_group_id, renewable,
            generated, energy, emissions, emission_factor, market_value,
            version
        )
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {start_date} to {end_date}")

    return len(prepared_data)


async def run_unit_intervals_aggregate_for_last_days(days: int) -> int:
    """
    Run the unit intervals aggregation for the last days.
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = end_date - timedelta(days=days)

    async with get_write_session() as session:
        await process_unit_intervals_backlog(session=session, start_date=start_date, end_date=end_date)


async def run_unit_intervals_backlog(start_date: datetime | None = None, network: NetworkSchema | None = None) -> None:
    """
    Run the unit intervals aggregation for the history of the market.
    """
    # Calculate date range
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)

    if not start_date and network:
        start_date = network.data_first_seen.replace(tzinfo=None)

    if not start_date:
        start_date = NetworkNEM.data_first_seen.replace(tzinfo=None)

    # Ensure ClickHouse schema exists
    client = get_clickhouse_client()

    # Process the data
    async with get_write_session() as session:
        await process_unit_intervals_backlog(
            session=session,
            start_date=start_date,
            end_date=end_date,
            chunk_size=timedelta(days=30),
            network=network,
        )

    # Verify the data was inserted
    result = client.execute(
        """
        SELECT
            network_id,
            network_region,
            count(*) as record_count,
            min(interval) as first_interval,
            max(interval) as last_interval
        FROM unit_intervals
        WHERE interval BETWEEN %(start)s AND %(end)s
        GROUP BY network_id, network_region
        """,
        {"start": start_date, "end": end_date},
    )

    # Log the results
    logger.info("Processing complete. Summary of inserted data:")
    for network_id, region, count, first, last in result:
        logger.info(
            f"Network: {network_id}, Region: {region}, Records: {count}, Period: {first.isoformat()} to {last.isoformat()}"
        )


async def _solar_and_wind_fixes() -> None:
    """
    Fix solar and wind records before 2015-10-26 and 2009-07-01 respectively.
    """
    client = get_clickhouse_client(timeout=100)

    client.execute("""
        delete from unit_intervals where fueltech_group_id = 'solar' and interval < '2016-08-01T00:00:00'
    """)

    client.execute(
        """
        DELETE FROM unit_intervals WHERE fueltech_group_id = 'wind' AND interval < '2009-07-01T00:00:00'
        """
    )


def _backfill_materialized_view(client: any, view: MaterializedView, start_date: datetime, end_date: datetime) -> int:
    """
    Backfill a single materialized view for a given date range.

    Args:
        client: ClickHouse client
        view: MaterializedView definition
        start_date: Start date for backfill
        end_date: End date for backfill

    Returns:
        int: Number of records processed
    """

    # if the view backfill query has start and end parameters, use them
    if "%(start)s" in view.backfill_query and "%(end)s" in view.backfill_query:
        # Process month by month
        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            next_month = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            logger.info(f"Processing month {current_date.strftime('%Y-%m')} for {view.name}")

            client.execute(
                view.backfill_query,
                {"start": current_date, "end": next_month},
            )

            current_date = next_month
    else:
        logger.info(f"Processing {view.name}")
        client.execute(view.backfill_query)

    # Return count of records
    result = client.execute(f"SELECT count() FROM {view.name}")
    return result[0][0]


def _get_view_by_name(view_name: str) -> MaterializedView:
    """
    Get a materialized view definition by its name.

    Args:
        view_name: Name of the view to find

    Returns:
        MaterializedView if found, None otherwise
    """
    for view in MATERIALIZED_VIEWS:
        if view.name == view_name:
            return view
    raise ValueError(f"View {view_name} not found")


def backfill_materialized_views(view: MaterializedView | str | None = None, refresh_views: bool = False) -> None:
    """
    Backfill materialized views from the base unit_intervals table.
    This should be run after bulk loading data into unit_intervals if the views are empty.

    Args:
        view: Optional view to backfill. Can be either a MaterializedView instance or a view name.
              If None, all views will be backfilled.

    Raises:
        ValueError: If a view name is provided but not found
    """
    client = get_clickhouse_client()

    # Get date range from base table
    result = client.execute("""
        SELECT
            min(interval) as min_date,
            max(interval) as max_date
        FROM unit_intervals
    """)
    start_date, end_date = result[0]

    # Determine which views to process
    views_to_process = []
    if view is None:
        views_to_process = MATERIALIZED_VIEWS
    elif isinstance(view, MaterializedView):
        views_to_process = [view]
    elif isinstance(view, str):
        found_view = _get_view_by_name(view)
        if found_view is None:
            raise ValueError(f"View {view} not found")
        views_to_process = [found_view]

    # Process each view
    for view in views_to_process:
        # delete and recreate the view if we are refreshing
        if refresh_views:
            logger.info(f"Refreshing {view.name}")
            client.execute(f"DROP TABLE IF EXISTS {view.name}")
            client.execute(view.schema)

        record_count = _backfill_materialized_view(
            client=client,
            view=view,
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"Backfill complete for {view.name}. Records: {record_count}")


if __name__ == "__main__":
    # Run the test
    async def reset_unit_intervals():
        # _refresh_clickhouse_schema()
        # await run_unit_intervals_backlog(start_date=NetworkNEM.data_first_seen.replace(tzinfo=None))
        from opennem.schema.network import NetworkWEM

        await run_unit_intervals_backlog(network=NetworkWEM)
        # await _solar_and_wind_fixes()

        # await optimize_clickhouse_tables()

        # Uncomment to backfill views:
        # backfill_materialized_views(refresh_views=True)

    import asyncio

    asyncio.run(reset_unit_intervals())
