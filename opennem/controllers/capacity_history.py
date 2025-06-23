"""
Capacity history controller

This module handles the processing and export of capacity history data.
It transforms raw capacity data into API-compatible formats and manages
the export to cloud storage.
"""

import logging
from datetime import date, timedelta
from typing import Any

import polars as pl

from opennem.api.schema import APIV4ResponseSchema
from opennem.exporter.storage_bucket import cloudflare_uploader
from opennem.queries.capacity_history import get_capacity_history, get_rooftop_capacity_history
from opennem.schema.network import NetworkNEM

logger = logging.getLogger(__name__)


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

    Uses unit commencement_date and closure_date to determine operational periods.

    Returns:
        URL of the uploaded file
    """
    try:
        # Get capacity history for the full date range
        end_date = date.today().replace(day=1) - timedelta(days=1)
        start_date = NetworkNEM.data_first_seen.date()

        logger.info(f"Generating capacity history from {start_date} to {end_date}")

        # Get the data from both queries
        df_units = await get_capacity_history(start_date, end_date)
        df_rooftop = await get_rooftop_capacity_history(start_date, end_date)

        # Combine the dataframes
        if df_units.is_empty() and df_rooftop.is_empty():
            logger.warning("No capacity history data found")
            return ""
        elif df_units.is_empty():
            df = df_rooftop
        elif df_rooftop.is_empty():
            df = df_units
        else:
            # Concatenate both dataframes
            df = pl.concat([df_units, df_rooftop], how="vertical")

        logger.info(f"Combined capacity history: {len(df)} total records ({len(df_units)} units, {len(df_rooftop)} rooftop)")

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

    asyncio.run(export_capacity_history_json())
