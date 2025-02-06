"""
Time interval definitions and helpers for OpenNEM.

This module provides interval definitions and helper functions for generating
time interval queries in both TimescaleDB and ClickHouse databases. The intervals
are used for aggregating time series data at different granularities.
"""

from enum import Enum
from typing import Literal


class Interval(str, Enum):
    """
    Time intervals for aggregating time series data.

    These intervals are used to group time series data into fixed-width periods
    for both API queries and database aggregations.

    Attributes:
        INTERVAL: 5-minute interval (default trading interval)
        HOUR: 1-hour interval
        DAY: Daily interval
        WEEK: 7-day interval
        MONTH: Monthly interval
        QUARTER: Quarterly interval
        SEASON: Seasonal interval (3 months)
        YEAR: Yearly interval
        FINANCIAL_YEAR: Financial year interval (July-June)
    """

    INTERVAL = "5m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "7d"
    MONTH = "1M"
    QUARTER = "3M"
    SEASON = "season"
    YEAR = "1y"
    FINANCIAL_YEAR = "fy"


DatabaseType = Literal["timescaledb", "clickhouse"]


def get_interval_function(interval: Interval, timestamp_column: str, database: DatabaseType = "timescaledb") -> str:
    """
    Get the appropriate time interval function for the specified database.

    Args:
        interval: The time interval to use for aggregation
        timestamp_column: The name of the timestamp column to bucket
        database: The database type to generate the function for

    Returns:
        str: The time interval function as a SQL string

    Raises:
        ValueError: If an invalid interval or database type is provided
    """
    if database == "timescaledb":
        return _get_timescaledb_interval(interval, timestamp_column)
    elif database == "clickhouse":
        return _get_clickhouse_interval(interval, timestamp_column)
    else:
        raise ValueError(f"Unsupported database type: {database}")


def _get_timescaledb_interval(interval: Interval, timestamp_column: str) -> str:
    """
    Generate a TimescaleDB time_bucket function.

    Args:
        interval: The time interval to use for aggregation
        timestamp_column: The name of the timestamp column to bucket

    Returns:
        str: The TimescaleDB time_bucket function as a SQL string

    Raises:
        ValueError: If an invalid interval type is provided
    """
    interval_map = {
        Interval.INTERVAL: "5 minutes",
        Interval.HOUR: "1 hour",
        Interval.DAY: "1 day",
        Interval.WEEK: "7 days",
        Interval.MONTH: "1 month",
        Interval.QUARTER: "3 months",
        Interval.YEAR: "1 year",
    }

    if interval == Interval.SEASON:
        return f"time_bucket_ng('3 months', {timestamp_column}, 'Australia/Sydney', 'SEASON')"
    elif interval == Interval.FINANCIAL_YEAR:
        return f"time_bucket_ng('1 year', {timestamp_column}, 'Australia/Sydney', '07-01')"
    elif interval in interval_map:
        return f"time_bucket('{interval_map[interval]}', {timestamp_column})"
    else:
        raise ValueError(f"Unsupported interval type for TimescaleDB: {interval}")


def _get_clickhouse_interval(interval: Interval, timestamp_column: str) -> str:
    """
    Generate a ClickHouse time interval function.

    Args:
        interval: The time interval to use for aggregation
        timestamp_column: The name of the timestamp column to bucket

    Returns:
        str: The ClickHouse time interval function as a SQL string

    Raises:
        ValueError: If an invalid interval type is provided
    """
    interval_map = {
        Interval.INTERVAL: "toStartOfFiveMinute",
        Interval.HOUR: "toStartOfHour",
        Interval.DAY: "toStartOfDay",
        Interval.WEEK: "toStartOfWeek",
        Interval.MONTH: "toStartOfMonth",
        Interval.QUARTER: "toStartOfQuarter",
        Interval.YEAR: "toStartOfYear",
    }

    if interval == Interval.SEASON:
        # Custom function to handle seasons in Australia
        return f"""
            toStartOfQuarter(
                if(
                    month({timestamp_column}) >= 12 or month({timestamp_column}) <= 2,
                    toDateTime(concat(toString(year({timestamp_column})), '-12-01')),
                    if(
                        month({timestamp_column}) >= 3 and month({timestamp_column}) <= 5,
                        toDateTime(concat(toString(year({timestamp_column})), '-03-01')),
                        if(
                            month({timestamp_column}) >= 6 and month({timestamp_column}) <= 8,
                            toDateTime(concat(toString(year({timestamp_column})), '-06-01')),
                            toDateTime(concat(toString(year({timestamp_column})), '-09-01'))
                        )
                    )
                )
            )
        """
    elif interval == Interval.FINANCIAL_YEAR:
        return f"""
            toStartOfYear(
                if(
                    month({timestamp_column}) >= 7,
                    dateAdd(year, 1, {timestamp_column}),
                    {timestamp_column}
                )
            )
        """
    elif interval in interval_map:
        return f"{interval_map[interval]}({timestamp_column})"
    else:
        raise ValueError(f"Unsupported interval type for ClickHouse: {interval}")
