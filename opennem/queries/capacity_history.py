"""
Get a monthly history of capacities for units grouped by network region and fueltech

This module provides functionality to retrieve historical capacity data for energy units,
aggregated by month, network region, and fuel technology type. A unit is considered "live"
in a given month if that month falls within the unit's commencement_date and closure_date range.
"""

import logging
from datetime import date

import polars as pl
from sqlalchemy import text

from opennem.db import get_read_session

logger = logging.getLogger(__name__)


async def get_capacity_history(
    start_date: date,
    end_date: date,
) -> pl.DataFrame:
    """
    Get monthly capacity history grouped by network region and fueltech.

    Generates a complete time series with one record for every month in the date range.
    A unit is considered live in a month if that month overlaps with the unit's
    commencement_date to closure_date period.

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
            AND u.commencement_date IS NOT NULL
            AND f.network_id IN ('NEM', 'WEM')
            AND u.fueltech_id NOT IN ('battery', 'solar_rooftop')
            -- Only include valid regions: WEM network only has WEM region
            AND ((f.network_id = 'WEM' AND f.network_region = 'WEM') OR (f.network_id = 'NEM' AND f.network_region != 'WEM'))
            -- Unit is live if the month overlaps with its operational period
            AND mb.month_start >= date_trunc('month', u.commencement_date)
            AND mb.month_start <= date_trunc('month', COALESCE(u.closure_date, NOW()))
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


async def get_rooftop_capacity_history(
    start_date: date,
    end_date: date,
) -> pl.DataFrame:
    """
    Get monthly rooftop solar capacity history from unit_history table.

    Retrieves capacity history for APVI rooftop units and maps them to NEM/WEM networks.
    ROOFTOP_APVI_WA is mapped to WEM, all others to NEM with their respective regions.

    Args:
        start_date: Start date for the capacity history query
        end_date: End date for the capacity history query

    Returns:
        DataFrame with columns: month_start, network_id, network_region, fueltech_id, total_capacity
    """

    query = text("""
        WITH monthly_rooftop AS (
            SELECT
                date_trunc('month', uh.changed_at) AS month_start,
                u.code AS unit_code,
                -- Map APVI network to NEM/WEM
                CASE
                    WHEN u.code = 'ROOFTOP_APVI_WA' THEN 'WEM'
                    ELSE 'NEM'
                END AS network_id,
                -- Map regions
                CASE
                    WHEN u.code = 'ROOFTOP_APVI_NSW' THEN 'NSW1'
                    WHEN u.code = 'ROOFTOP_APVI_VIC' THEN 'VIC1'
                    WHEN u.code = 'ROOFTOP_APVI_QLD' THEN 'QLD1'
                    WHEN u.code = 'ROOFTOP_APVI_SA' THEN 'SA1'
                    WHEN u.code = 'ROOFTOP_APVI_TAS' THEN 'TAS1'
                    WHEN u.code = 'ROOFTOP_APVI_WA' THEN 'WEM'
                    ELSE NULL
                END AS network_region,
                'solar_rooftop' AS fueltech_id,
                -- Get the latest capacity for each month
                MAX(uh.capacity_registered) AS total_capacity
            FROM unit_history uh
            INNER JOIN units u ON uh.unit_id = u.id
            WHERE
                u.code LIKE 'ROOFTOP_APVI_%'
                AND u.code != 'ROOFTOP_APVI_NT'  -- Exclude NT
                AND uh.capacity_registered IS NOT NULL
                AND uh.changed_at >= date_trunc('month', CAST(:start_date AS timestamp))
                AND uh.changed_at <= date_trunc('month', CAST(:end_date AS timestamp)) + interval '1 month' - interval '1 second'
            GROUP BY
                date_trunc('month', uh.changed_at),
                u.code
        )
        SELECT
            month_start,
            network_id,
            network_region,
            fueltech_id,
            SUM(total_capacity) AS total_capacity
        FROM monthly_rooftop
        WHERE network_region IS NOT NULL
        GROUP BY
            month_start,
            network_id,
            network_region,
            fueltech_id
        ORDER BY
            month_start,
            network_id,
            network_region;
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

        # Debug logging
        if not df.is_empty():
            unique_regions = df.select(["network_id", "network_region"]).unique().sort(["network_id", "network_region"])
            logger.info(f"Retrieved rooftop capacity history with {len(df)} records")
            logger.info(f"Rooftop regions found: {unique_regions.to_dicts()}")
        else:
            logger.warning("No rooftop capacity history data retrieved")

        return df
