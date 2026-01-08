"""
Market Summary aggregation module.

This module handles the aggregation of market summary data from PostgreSQL to ClickHouse.
It calculates energy values from power readings and stores them in MWh in ClickHouse for efficient querying.
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
from opennem.db.clickhouse_materialized_views import (
    backfill_materialized_views,
    ensure_materialized_views_exist,
)
from opennem.db.clickhouse_schema import (
    MARKET_SUMMARY_TABLE_SCHEMA,
    optimize_clickhouse_tables,
)
from opennem.db.clickhouse_views import (
    MARKET_SUMMARY_DAILY_VIEW,
    MARKET_SUMMARY_MONTHLY_VIEW,
)
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.aggregates.market_summary")

# List of all materialized views to manage
_MARKET_SUMMARY_MATERIALIZED_VIEWS = [
    MARKET_SUMMARY_DAILY_VIEW,
    MARKET_SUMMARY_MONTHLY_VIEW,
]


async def _get_market_summary_data(
    session: AsyncSession, start_time: datetime, end_time: datetime
) -> list[
    tuple[
        datetime,
        str,
        str,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
    ]
]:
    """
    Get market summary data from PostgreSQL for a given time range.

    Args:
        session: Database session
        start_time: Start time for data range
        end_time: End date for data range

    Returns:
        List of tuples containing
        (interval, network_id, network_region, price, demand, demand_total,
         prev_demand, prev_demand_total, rooftop_solar, prev_rooftop_solar,
         renewable_generation, prev_renewable_generation,
         curtailment_solar_total, curtailment_wind_total, prev_curtailment_solar_total,
         prev_curtailment_wind_total, curtailment_total)
        Note: Only returns complete interval pairs where both current and previous intervals are available
    """
    # Strip timezone info
    start_time_naive = start_time.replace(tzinfo=None)
    end_time_naive = end_time.replace(tzinfo=None)

    query = text("""
    WITH regions AS (
        -- Get all unique network regions for the period
        SELECT DISTINCT network_id, network_region
        FROM balancing_summary
        WHERE interval BETWEEN :start_time_window AND :end_time
        AND is_forecast = false
    ),
    rooftop_data AS (
        -- Get rooftop solar generation aggregated by region with gap filling
        SELECT
            time_bucket_gapfill('5 minutes', fs.interval, :start_time_window, :end_time) as interval,
            f.network_id,
            f.network_region,
            interpolate(avg(fs.generated)) as rooftop_solar
        FROM facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        WHERE fs.interval BETWEEN :start_time_window AND :end_time
            AND u.fueltech_id = 'solar_rooftop'
            AND fs.is_forecast = false
            AND f.network_id IN (SELECT network_id FROM regions)
            AND f.network_region IN (SELECT network_region FROM regions)
        GROUP BY 1, 2, 3
    ),
    renewable_data AS (
        -- Get all renewable generation (excluding rooftop which is handled separately)
        SELECT
            time_bucket_gapfill('5 minutes', fs.interval, :start_time_window, :end_time) as interval,
            f.network_id,
            f.network_region,
            interpolate(sum(CASE
                WHEN u.fueltech_id IN ('bioenergy_biogas', 'bioenergy_biomass', 'hydro',
                                       'solar_utility', 'wind')
                THEN fs.generated
                ELSE 0
            END)) as renewable_generation
        FROM facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        WHERE fs.interval BETWEEN :start_time_window AND :end_time
            AND fs.is_forecast = false
            AND f.network_id IN (SELECT network_id FROM regions)
            AND f.network_region IN (SELECT network_region FROM regions)
        GROUP BY 1, 2, 3
    ),
    gapfilled_data AS (
        -- Generate complete time series with gap filling for each region
        SELECT
            time_bucket_gapfill('5 minutes', interval, :start_time_window, :end_time) as interval,
            network_id,
            network_region,
            avg(CAST(price AS double precision)) as price,
            avg(CAST(demand AS double precision)) as demand,
            avg(CAST(demand_total AS double precision)) as demand_total,
            avg(ROUND((ss_solar_uigf - ss_solar_clearedmw)::numeric, 4)) as curtailment_solar_total,
            avg(ROUND((ss_wind_uigf - ss_wind_clearedmw)::numeric, 4)) as curtailment_wind_total
        FROM balancing_summary
        WHERE interval BETWEEN :start_time_window AND :end_time
            AND is_forecast = false
            AND network_id IN (SELECT network_id FROM regions)
            AND network_region IN (SELECT network_region FROM regions)
        GROUP BY 1, 2, 3
    ),
    combined_data AS (
        SELECT
            COALESCE(gd.interval, rd.interval, rn.interval) as interval,
            COALESCE(gd.network_id, rd.network_id, rn.network_id) as network_id,
            COALESCE(gd.network_region, rd.network_region, rn.network_region) as network_region,
            gd.price,
            gd.demand,
            gd.demand_total,
            COALESCE(rd.rooftop_solar, 0) as rooftop_solar,
            COALESCE(rn.renewable_generation, 0) as renewable_generation,
            gd.curtailment_solar_total,
            gd.curtailment_wind_total
        FROM gapfilled_data gd
        FULL OUTER JOIN rooftop_data rd
            ON gd.interval = rd.interval
            AND gd.network_id = rd.network_id
            AND gd.network_region = rd.network_region
        FULL OUTER JOIN renewable_data rn
            ON gd.interval = rn.interval
            AND gd.network_id = rn.network_id
            AND gd.network_region = rn.network_region
    ),
    ranked_data AS (
        SELECT
            interval,
            network_id,
            network_region,
            price,
            demand,
            demand_total,
            LAG(demand) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_demand,
            LAG(demand_total) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_demand_total,
            rooftop_solar,
            LAG(rooftop_solar) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_rooftop_solar,
            renewable_generation,
            LAG(renewable_generation) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_renewable_generation,
            curtailment_solar_total,
            curtailment_wind_total,
            LAG(curtailment_solar_total) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_curtailment_solar_total,
            LAG(curtailment_wind_total) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_curtailment_wind_total
        FROM combined_data
        ORDER BY interval
    )
    SELECT
        interval,
        network_id,
        network_region,
        price,
        demand,
        demand_total,
        prev_demand,
        prev_demand_total,
        rooftop_solar,
        prev_rooftop_solar,
        renewable_generation,
        prev_renewable_generation,
        curtailment_solar_total,
        curtailment_wind_total,
        prev_curtailment_solar_total,
        prev_curtailment_wind_total,
        COALESCE(curtailment_solar_total, 0) + COALESCE(curtailment_wind_total, 0) as curtailment_total
    FROM ranked_data
    WHERE interval BETWEEN :start_time AND :end_time
    ORDER BY interval, network_id, network_region
    """)

    result = await session.execute(
        query,
        {
            "start_time": start_time_naive,
            "start_time_window": start_time_naive - timedelta(hours=1),
            "end_time": end_time_naive,
        },
    )
    # Type cast to match expected return type
    return [tuple(row) for row in result.fetchall()]  # type: ignore


def _prepare_market_summary_data(
    records: Sequence[
        tuple[
            datetime,
            str,
            str,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
            float | None,
        ]
    ],
) -> list[
    tuple[
        datetime,
        str,
        str,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
    ]
]:
    """
    Prepare market summary data for ClickHouse by calculating energy values.

    Args:
        records: Raw records from PostgreSQL

    Returns:
        List of tuples ready for ClickHouse insertion with energy values in MWh
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
            "price": pl.Float64,
            "demand": pl.Float64,
            "demand_total": pl.Float64,
            "prev_demand": pl.Float64,
            "prev_demand_total": pl.Float64,
            "rooftop_solar": pl.Float64,
            "prev_rooftop_solar": pl.Float64,
            "renewable_generation": pl.Float64,
            "prev_renewable_generation": pl.Float64,
            "curtailment_solar_total": pl.Float64,
            "curtailment_wind_total": pl.Float64,
            "prev_curtailment_solar_total": pl.Float64,
            "prev_curtailment_wind_total": pl.Float64,
            "curtailment_total": pl.Float64,
        },
        orient="row",
    )

    # round all float64 columns to 4 decimal places
    df = df.with_columns([pl.col(col).round(4) for col in df.columns if isinstance(col, pl.Float64)])

    # fill curtailment, rooftop, and renewable records with 0 if they are null
    df = df.with_columns(
        [
            pl.col("rooftop_solar").fill_null(0),
            pl.col("prev_rooftop_solar").fill_null(0),
            pl.col("renewable_generation").fill_null(0),
            pl.col("prev_renewable_generation").fill_null(0),
            pl.col("curtailment_solar_total").fill_null(0),
            pl.col("curtailment_wind_total").fill_null(0),
            pl.col("prev_curtailment_solar_total").fill_null(0),
            pl.col("prev_curtailment_wind_total").fill_null(0),
            pl.col("curtailment_total").fill_null(0),
        ]
    )

    # Calculate demand_gross (demand_total + rooftop_solar)
    df = df.with_columns(
        [
            (pl.col("demand_total") + pl.col("rooftop_solar")).round(4).alias("demand_gross"),
            (pl.col("prev_demand_total") + pl.col("prev_rooftop_solar")).round(4).alias("prev_demand_gross"),
        ]
    )

    # Calculate generation_renewable (renewable_generation + rooftop_solar)
    df = df.with_columns(
        [
            (pl.col("renewable_generation") + pl.col("rooftop_solar")).round(4).alias("generation_renewable"),
            (pl.col("prev_renewable_generation") + pl.col("prev_rooftop_solar")).round(4).alias("prev_generation_renewable"),
        ]
    )

    network_intervals = {
        "NEM": 5,
        "WEM": 30,
    }

    # Create intervals_per_hour mapping
    intervals_map = {network: 60 / interval for network, interval in network_intervals.items()}
    default_intervals = 60 / 5  # Default to 5-minute intervals

    # Calculate energy values using vectorized operations (converting to MWh)
    df = df.with_columns(
        [
            (
                (
                    (pl.col("demand") + pl.col("prev_demand"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                    / 1000  # Convert from kWh to MWh
                ).round(4)
            ).alias("demand_energy"),
            (
                (
                    (pl.col("demand_total") + pl.col("prev_demand_total"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                    / 1000  # Convert from kWh to MWh
                ).round(4)
            ).alias("demand_total_energy"),
            (
                (
                    (pl.col("demand_gross") + pl.col("prev_demand_gross"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                    / 1000  # Convert from kWh to MWh
                ).round(4)
            ).alias("demand_gross_energy"),
            (
                (
                    (pl.col("generation_renewable") + pl.col("prev_generation_renewable"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                    / 1000  # Convert from kWh to MWh
                ).round(4)
            ).alias("generation_renewable_energy"),
            (
                (
                    (pl.col("curtailment_solar_total") + pl.col("prev_curtailment_solar_total"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                    / 1000  # Convert from kWh to MWh
                ).round(4)
            ).alias("curtailment_energy_solar_total"),
            (
                (
                    (pl.col("curtailment_wind_total") + pl.col("prev_curtailment_wind_total"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                    / 1000  # Convert from kWh to MWh
                ).round(4)
            ).alias("curtailment_energy_wind_total"),
        ]
    )

    # Calculate total curtailment energy
    df = df.with_columns(
        [
            (pl.col("curtailment_energy_solar_total") + pl.col("curtailment_energy_wind_total"))
            .round(4)
            .alias("curtailment_energy_total"),
        ]
    )

    # Calculate market values and add version
    df = df.with_columns(
        [
            (pl.col("demand_energy") * pl.col("price")).round(4).alias("demand_market_value"),
            (pl.col("demand_total_energy") * pl.col("price")).round(4).alias("demand_total_market_value"),
            (pl.col("demand_gross_energy") * pl.col("price")).round(4).alias("demand_gross_market_value"),
            pl.lit(int(datetime.now().timestamp())).alias("version"),  # Add version column
        ]
    )

    # Select and order columns for ClickHouse insertion
    result_df = df.select(
        [
            "interval",
            "network_id",
            "network_region",
            "price",
            "demand",
            "demand_total",
            "demand_gross",
            "generation_renewable",
            "demand_energy",
            "demand_total_energy",
            "demand_gross_energy",
            "generation_renewable_energy",
            "demand_market_value",
            "demand_total_market_value",
            "demand_gross_market_value",
            "curtailment_solar_total",
            "curtailment_wind_total",
            "curtailment_total",
            "curtailment_energy_solar_total",
            "curtailment_energy_wind_total",
            "curtailment_energy_total",
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

    if not table_exists(client, "market_summary"):
        create_table_if_not_exists(client, "market_summary", MARKET_SUMMARY_TABLE_SCHEMA)
        logger.info("Created market_summary table")

    # Use the generic function to ensure materialized views exist
    ensure_materialized_views_exist(_MARKET_SUMMARY_MATERIALIZED_VIEWS)


def _refresh_clickhouse_schema() -> None:
    """
    Refresh ClickHouse schema by dropping and recreating tables and views.
    """
    print("This will drop and recreate all market_summary tables and views. Are you sure you want to continue? (y/n)")
    if input().lower() != "y":
        logger.info("User cancelled")
        return

    client = get_clickhouse_client()

    # Drop views first (in reverse order of creation to handle dependencies)
    for view in reversed(_MARKET_SUMMARY_MATERIALIZED_VIEWS):
        client.execute(f"DROP TABLE IF EXISTS {view.name}")
        logger.info(f"Dropped {view.name}")

    client.execute("DROP TABLE IF EXISTS market_summary")
    logger.info("Dropped market_summary table")

    _ensure_clickhouse_schema()


async def process_market_summary_backlog(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    chunk_size: timedelta = timedelta(days=7),
) -> None:
    """
    Process historical market summary data in chunks.

    Args:
        session: Database session
        start_date: Start date for processing
        end_date: End date for processing
        chunk_size: Size of each processing chunk
    """
    current_start = start_date
    client = get_clickhouse_client()
    _ensure_clickhouse_schema()

    while current_start < end_date:
        chunk_end = min(current_start + chunk_size, end_date)

        # Get and process data for this chunk
        records = await _get_market_summary_data(session, current_start, chunk_end)
        if records:
            prepared_data = _prepare_market_summary_data(records)

            # Batch insert into ClickHouse
            client.execute(
                """
                INSERT INTO market_summary
                (
                    interval, network_id, network_region, price, demand, demand_total,
                    demand_gross, generation_renewable, demand_energy, demand_total_energy,
                    demand_gross_energy, generation_renewable_energy, demand_market_value,
                    demand_total_market_value, demand_gross_market_value, curtailment_solar_total,
                    curtailment_wind_total, curtailment_total, curtailment_energy_solar_total,
                    curtailment_energy_wind_total, curtailment_energy_total, version
                )
                VALUES
                """,
                prepared_data,
            )

            logger.info(f"Processed {len(prepared_data)} records from {current_start} to {chunk_end}")

        current_start = chunk_end


async def run_market_summary_aggregate_to_now() -> int:
    """ """
    client = get_clickhouse_client()

    # get the max interval from market_summary using FINAL modifier
    result = client.execute("SELECT MAX(interval) FROM market_summary FINAL")
    result_rows = list(result)  # type: ignore

    if not result_rows or not result_rows[0] or result_rows[0][0] is None:
        logger.info("No market summary max interval found")
        return 0

    max_interval = result_rows[0][0]  # type: ignore

    # Check if table is empty (returns epoch time)
    if max_interval.year < 2000:
        logger.info(
            "Market summary table appears to be empty (max interval is before 2000). Please run reset_market_summary() first."
        )
        return 0

    date_from = max_interval + timedelta(minutes=5)  # type: ignore
    date_to = get_last_completed_interval_for_network(network=NetworkNEM)

    if date_from > date_to:
        logger.info("No new data to process")
        return 0

    # Fix: calculate date range correctly (should be date_to - date_from, not date_from - date_to)
    date_range_days = (date_to - date_from).days
    if date_range_days > 7:
        logger.info(
            f"Date range is {date_range_days} days (greater than 7 days), skipping. Use reset_market_summary() for large gaps."
        )
        return 0

    # run market summary from max_interval to now
    async with get_write_session() as session:
        records = await _get_market_summary_data(session, date_from, date_to)
        prepared_data = _prepare_market_summary_data(records)

    client.execute(
        """
        INSERT INTO market_summary
        (
            interval, network_id, network_region, price, demand, demand_total,
            demand_gross, generation_renewable, demand_energy, demand_total_energy,
            demand_gross_energy, generation_renewable_energy, demand_market_value,
            demand_total_market_value, demand_gross_market_value, curtailment_solar_total,
            curtailment_wind_total, curtailment_total, curtailment_energy_solar_total,
            curtailment_energy_wind_total, curtailment_energy_total, version
        )
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {date_from} to {date_to}")

    return len(prepared_data)


async def run_market_summary_aggregate_for_last_intervals(num_intervals: int) -> int:
    """
    Run the market summary aggregation for the last num_intervals
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = end_date - timedelta(minutes=num_intervals * 5)

    async with get_write_session() as session:
        records = await _get_market_summary_data(session, start_date, end_date)
        prepared_data = _prepare_market_summary_data(records)

    client = get_clickhouse_client()

    client.execute(
        """
        INSERT INTO market_summary
        (
            interval, network_id, network_region, price, demand, demand_total,
            demand_gross, generation_renewable, demand_energy, demand_total_energy,
            demand_gross_energy, generation_renewable_energy, demand_market_value,
            demand_total_market_value, demand_gross_market_value, curtailment_solar_total,
            curtailment_wind_total, curtailment_total, curtailment_energy_solar_total,
            curtailment_energy_wind_total, curtailment_energy_total, version
        )
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {start_date} to {end_date}")

    await optimize_clickhouse_tables(table_names=["market_summary"])

    return len(prepared_data)


async def run_market_summary_aggregate_for_last_days(days: int) -> int:
    """
    Run the market summary aggregation for the last days.
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = end_date - timedelta(days=days)

    async with get_write_session() as session:
        await process_market_summary_backlog(session=session, start_date=start_date, end_date=end_date)

    await optimize_clickhouse_tables(table_names=["market_summary"])

    return 0  # Return 0 to indicate successful completion


async def run_market_summary_backlog() -> None:
    """
    Run the market summary aggregation for the history of the market.
    """

    # Calculate date range for the past week
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    if NetworkNEM.data_first_seen is None:
        logger.error("NetworkNEM.data_first_seen is None, cannot proceed")
        return
    start_date = NetworkNEM.data_first_seen.replace(tzinfo=None)

    # Ensure ClickHouse schema exists
    client = get_clickhouse_client()

    # Process the data
    async with get_write_session() as session:
        await process_market_summary_backlog(
            session=session,
            start_date=start_date,
            end_date=end_date,
            chunk_size=timedelta(days=30),
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
        FROM market_summary
        WHERE interval BETWEEN %(start)s AND %(end)s
        GROUP BY network_id, network_region
        """,
        {"start": start_date, "end": end_date},
    )

    # Log the results
    logger.info("Processing complete. Summary of inserted data:")
    result_rows = list(result)  # type: ignore
    for row in result_rows:  # type: ignore
        if len(row) >= 5:  # type: ignore
            network_id, region, count, first, last = row[:5]  # type: ignore
            logger.info(
                f"Network: {network_id}, Region: {region}, Records: {count}, Period: {first.isoformat()} to {last.isoformat()}"
            )


def backfill_market_summary_views(refresh_views: bool = False) -> None:
    """
    Backfill materialized views for market_summary data.
    This function delegates to the generic backfill_materialized_views function.

    Args:
        refresh_views: If True, drops and recreates views before backfilling.
    """
    # Use the generic function with market_summary specific views
    results = backfill_materialized_views(views=_MARKET_SUMMARY_MATERIALIZED_VIEWS, refresh_views=refresh_views)

    for view_name, count in results.items():
        logger.info(f"Backfilled {view_name}: {count} records")


async def reset_market_summary(start_date: datetime | None = None, skip_schema_refresh: bool = False) -> None:
    """
    Reset and rebuild the entire market summary aggregation including all views.
    This is the main entry point for refreshing all market summary data.

    Args:
        start_date: Optional start date for the backlog. If None, uses NetworkNEM.data_first_seen
        skip_schema_refresh: If True, skips the schema refresh step (useful for incremental updates)
    """
    logger.info("Starting complete market summary reset and rebuild")

    # Step 1: Refresh the schema (drops and recreates tables/views) - unless skipped
    if not skip_schema_refresh:
        _refresh_clickhouse_schema()
    else:
        # Just ensure schema exists
        _ensure_clickhouse_schema()

    # Step 2: Determine date range
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    if not start_date:
        if NetworkNEM.data_first_seen is None:
            logger.error("NetworkNEM.data_first_seen is None, cannot proceed")
            return
        start_date = NetworkNEM.data_first_seen.replace(tzinfo=None)
    else:
        start_date = start_date.replace(tzinfo=None)

    # Step 3: Run the backlog to populate the main table
    logger.info(f"Running market summary backlog from {start_date} to {end_date}...")
    async with get_write_session() as session:
        await process_market_summary_backlog(
            session=session,
            start_date=start_date,
            end_date=end_date,
            chunk_size=timedelta(days=30),
        )

    # Step 4: Optimize the tables
    logger.info("Optimizing ClickHouse tables...")
    await optimize_clickhouse_tables(table_names=["market_summary"])

    # Step 5: Backfill the materialized views (only if schema was refreshed)
    if not skip_schema_refresh:
        logger.info("Backfilling materialized views...")
        backfill_market_summary_views(refresh_views=True)

    logger.info("Market summary reset and rebuild complete!")


if __name__ == "__main__":
    # Run the complete reset
    async def main():
        # Option 1: Full reset from the beginning
        # await reset_market_summary()

        # Option 2: Reset from a specific date (e.g., last month for testing)
        await reset_market_summary(start_date=datetime.fromisoformat("2020-01-01T00:00:00"))

        # Option 3: Incremental update without schema refresh
        # await reset_market_summary(
        #     start_date=datetime.fromisoformat("2025-08-01T00:00:00"),
        #     skip_schema_refresh=True
        # )

    import asyncio

    asyncio.run(run_market_summary_aggregate_to_now())
