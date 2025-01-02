"""
ClickHouse database utility functions.
"""

from opennem.schema.time import TimeInterval


def get_clickhouse_interval(interval: TimeInterval | str) -> str:
    """
    Get the ClickHouse time bucket function for a given interval.

    Args:
        interval: TimeInterval object or interval string (e.g. '5m', '1h')

    Returns:
        str: ClickHouse time bucket function name
    """
    # Convert TimeInterval to string if needed
    interval_str = interval.interval_human if isinstance(interval, TimeInterval) else interval

    interval_map = {
        "5m": "toStartOfFiveMinute",
        "15m": "toStartOfFifteenMinutes",
        "30m": "toStartOfInterval(30 minute)",
        "1h": "toStartOfHour",
        "1d": "toStartOfDay",
        "1M": "toStartOfMonth",
    }

    return interval_map.get(interval_str, "toStartOfFiveMinute")
