"""
Get a monthly history of capacities for units grouped by network region and fueltech

This module provides functionality to retrieve historical capacity data for energy units,
aggregated by month, network region, and fuel technology type. A unit is considered "live"
in a given month if that month falls within the unit's data_first_seen and data_last_seen range.
"""

import logging
from datetime import date, timedelta
from typing import Any

import polars as pl
from sqlalchemy import text

from opennem.api.schema import APIV4ResponseSchema
from opennem.db import get_read_session
from opennem.exporter.storage_bucket import cloudflare_uploader
from opennem.schema.network import NetworkNEM

logger = logging.getLogger(__name__)


async def get_capacity_history(
    start_date: date,
    end_date: date,
) -> pl.DataFrame:
    """
    Get monthly capacity history grouped by network region and fueltech.

    Generates a complete time series with one record for every month in the date range.
    A unit is considered live in a month if that month overlaps with the unit's
    data_first_seen to data_last_seen period.

    Args:
        start_date: Start date for the capacity history query
        end_date: End date for the capacity history query

    Returns:
        DataFrame with columns: month_start, network_id, network_region, fueltech_id, total_capacity
    """

    query = text("""
        WITH monthly_buckets AS (
            -- Generate complete series of monthly buckets from start_date to end_date
            SELECT date_trunc('month', generate_series) AS month_start
            FROM generate_series(
                date_trunc('month', CAST(:start_date AS timestamp)),
                date_trunc('month', CAST(:end_date AS timestamp)),
                '1 month'::interval
            ) AS generate_series
        )
        SELECT
            mb.month_start,
            f.network_id,
            f.network_region,
            u.fueltech_id,
            SUM(u.capacity_registered) AS total_capacity
        FROM monthly_buckets mb
        CROSS JOIN units u
        INNER JOIN facilities f ON u.station_id = f.id
        WHERE
            u.fueltech_id IS NOT NULL
            AND u.capacity_registered IS NOT NULL
            AND u.data_first_seen IS NOT NULL
            AND f.network_id IN ('NEM', 'WEM')
            AND u.fueltech_id NOT IN ('battery', 'solar_rooftop')
            -- Only include valid regions: WEM network only has WEM region
            AND ((f.network_id = 'WEM' AND f.network_region = 'WEM') OR (f.network_id = 'NEM' AND f.network_region != 'WEM'))
            -- Unit is live if the month overlaps with its active period
            AND mb.month_start >= date_trunc('month', u.data_first_seen)
            AND mb.month_start <= date_trunc('month', COALESCE(u.data_last_seen, NOW()))
        GROUP BY
            mb.month_start,
            f.network_id,
            f.network_region,
            u.fueltech_id
        ORDER BY
            month_start,
            network_id,
            network_region,
            fueltech_id;
    """)

    async with get_read_session() as session:
        result = await session.execute(query, {"start_date": start_date, "end_date": end_date})

        # Convert to Polars DataFrame
        rows = result.fetchall()
        column_names = list(result.keys())

        # Convert rows to native Python types to avoid decimal issues
        converted_rows = []
        for row in rows:
            converted_row = []
            for value in row:
                if hasattr(value, "__float__"):  # Convert decimal to float
                    converted_row.append(float(value))
                else:
                    converted_row.append(value)
            converted_rows.append(converted_row)

        df = pl.DataFrame(converted_rows, schema=column_names, orient="row")

        # Debug: check unique months in the result
        if not df.is_empty():
            unique_months = df.select("month_start").unique().sort("month_start")
            logger.info(f"Retrieved capacity history with {len(df)} records from {start_date} to {end_date}")
            logger.info(f"Found {len(unique_months)} unique months in the result")
            logger.info(f"Date range in result: {unique_months.item(0, 0)} to {unique_months.item(-1, 0)}")
        else:
            logger.warning("No capacity history data retrieved")

        return df


def pad_missing_values(df: pl.DataFrame) -> pl.DataFrame:
    """
    Pad missing values with zeros to ensure all combinations of month/network/region/fueltech exist.

    Args:
        df: Input DataFrame with capacity data

    Returns:
        DataFrame with all combinations filled, missing values as 0
    """
    if df.is_empty():
        return df

    # Get all unique values for each dimension
    all_months = df.select("month_start").unique().sort("month_start")
    all_fueltechs = df.select("fueltech_id").unique()

    # Get valid network/region combinations (don't create invalid cross products)
    valid_network_regions = df.select(["network_id", "network_region"]).unique()

    logger.info(
        f"Padding: {len(all_months)} months, {len(all_fueltechs)} fueltechs, {len(valid_network_regions)}"
        " network/region combinations"
    )

    # Create cartesian product of months, valid network/region combinations, and fueltechs
    combinations = all_months.join(valid_network_regions, how="cross").join(all_fueltechs, how="cross")

    # Left join with original data to fill missing combinations with 0
    padded_df = (
        combinations.join(df, on=["month_start", "network_id", "network_region", "fueltech_id"], how="left")
        .with_columns(pl.col("total_capacity").fill_null(0.0).cast(pl.Float64))
        .sort(["month_start", "network_id", "network_region", "fueltech_id"])
    )

    logger.info(f"After padding: {len(padded_df)} total records")

    return padded_df


def format_capacity_history_response(df: pl.DataFrame) -> dict[str, Any]:
    """
    Format capacity history data into API v4 response schema format.
    Creates separate time series for each network/region/fueltech combination.

    Args:
        df: Polars DataFrame with capacity history data

    Returns:
        Dictionary in APIV4ResponseSchema format with separate series for each fueltech
    """
    if df.is_empty():
        return {"data": []}

    # Create separate time series for each network/region/fueltech combination
    grouped_data = []

    # Get unique network/region/fueltech combinations
    combinations = (
        df.select(["network_id", "network_region", "fueltech_id"]).unique().sort(["network_id", "network_region", "fueltech_id"])
    )

    for row in combinations.iter_rows(named=True):
        network_id = row["network_id"]
        network_region = row["network_region"]
        fueltech_id = row["fueltech_id"]

        # Filter data for this specific combination
        series_data = df.filter(
            (pl.col("network_id") == network_id)
            & (pl.col("network_region") == network_region)
            & (pl.col("fueltech_id") == fueltech_id)
        ).sort("month_start")

        if series_data.is_empty():
            continue

        # Convert to time series format
        intervals = series_data.select("month_start").to_series().to_list()
        capacities = series_data.select("total_capacity").to_series().to_list()

        # Create data points as just a list of capacity values
        data_points = [float(capacity) if capacity is not None else 0.0 for capacity in capacities]

        # Create time series object
        time_series = {
            "id": f"capacity.{network_id.lower()}.{network_region.lower()}.{fueltech_id}",
            "type": "capacity",
            "network": network_id,
            "region": network_region,
            "fueltech": fueltech_id,
            "metric": "capacity",
            "units": "MW",
            "interval": "1M",
            "period": {
                "start": intervals[0].isoformat() if intervals else None,
                "end": intervals[-1].isoformat() if intervals else None,
            },
            "data": data_points,
        }

        grouped_data.append(time_series)

    return {"data": grouped_data}


async def export_capacity_history_json() -> str:
    """
    Export capacity history data as JSON and upload to Cloudflare.

    Returns:
        URL of the uploaded file
    """
    try:
        # Get capacity history for the full date range
        end_date = date.today().replace(day=1) - timedelta(days=1)
        start_date = NetworkNEM.data_first_seen.date()

        logger.info(f"Generating capacity history from {start_date} to {end_date}")

        # Get the data
        df = await get_capacity_history(start_date, end_date)

        if df.is_empty():
            logger.warning("No capacity history data found")
            return ""

        # Pad missing values with zeros
        padded_df = pad_missing_values(df)

        # Format as API response
        response_data = format_capacity_history_response(padded_df)

        # Create APIV4ResponseSchema
        api_response = APIV4ResponseSchema(data=response_data["data"])

        # Convert to JSON
        json_content = api_response.model_dump_json(indent=2)

        # Upload to Cloudflare
        object_name = "v4/stats/capacity_history.json"
        content_type = "application/json"

        await cloudflare_uploader.upload_content(
            content=json_content,
            object_name=object_name,
            content_type=content_type,
        )

        url = f"{cloudflare_uploader.bucket_public_url}{object_name}"
        logger.info(f"Capacity history exported to: {url}")

        return url

    except Exception as e:
        logger.error(f"Error exporting capacity history: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        """
        Example usage of capacity history functions
        """
        try:
            # Export to JSON and upload to Cloudflare
            url = await export_capacity_history_json()
            print(f"Capacity history exported to: {url}")

            # Also show a sample of the data
            end_date = date.today().replace(day=1) - timedelta(days=1)
            start_date = NetworkNEM.data_first_seen.date()

            df = await get_capacity_history(start_date, end_date)

            print(f"\nCapacity history from {start_date} to {end_date}:")
            print(df.head(10))
            print(f"\nTotal records: {len(df)}")

            # Show summary by network and fueltech
            if not df.is_empty():
                summary = (
                    df.group_by(["network_id", "fueltech_id"])
                    .agg(pl.col("total_capacity").sum())
                    .sort(["network_id", "fueltech_id"])
                )
                print("\nCapacity summary by network and fueltech:")
                print(summary)

        except Exception as e:
            logger.error(f"Error running capacity history: {e}")
            print(f"An error occurred: {str(e)}")

    asyncio.run(export_capacity_history_json())
