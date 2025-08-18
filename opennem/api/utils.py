from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import func

from opennem.api.schema import API_SUPPORTED_NETWORKS
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkSchema


def get_query_count(query, session):
    """Get a count of all records in a query"""
    count_q = query.statement.with_only_columns([func.count()]).order_by(None)
    count = session.execute(count_q).scalar()
    return count


def get_api_network_from_code(network_code: str) -> NetworkSchema:
    """Get a network from a code"""
    if network_code not in API_SUPPORTED_NETWORKS:
        raise HTTPException(status_code=400, detail=f"Network {network_code} not supported")

    return API_SUPPORTED_NETWORKS[network_code]


def get_default_period_for_interval(interval: Interval) -> timedelta:
    """
    Get the default time period for a given interval.

    This function returns a sensible default time period based on the interval size.
    The defaults are chosen to provide a good balance between data density and
    query performance.

    Args:
        interval: The interval to get the default period for

    Returns:
        timedelta: The default time period for the interval

    Examples:
        >>> get_default_period_for_interval(Interval.INTERVAL)  # 5m -> 7 days
        datetime.timedelta(days=7)
        >>> get_default_period_for_interval(Interval.DAY)  # 1d -> 30 days
        datetime.timedelta(days=30)
    """
    # Default periods for each interval type
    default_periods = {
        # 5-minute intervals -> 7 days of data
        Interval.INTERVAL: timedelta(days=7),
        # Hourly intervals -> 14 days of data
        Interval.HOUR: timedelta(days=14),
        # Daily intervals -> 30 days of data
        Interval.DAY: timedelta(days=30),
        # Weekly intervals -> 90 days of data
        Interval.WEEK: timedelta(days=90),
        # Monthly intervals -> 365 days of data
        Interval.MONTH: timedelta(days=365),
        # Quarterly intervals -> 2 years of data
        Interval.QUARTER: timedelta(days=365 * 2),
        # Seasonal intervals -> 2 years of data
        Interval.SEASON: timedelta(days=365 * 2),
        # Yearly intervals -> 5 years of data
        Interval.YEAR: timedelta(days=365 * 5),
        # Financial year intervals -> 5 years of data
        Interval.FINANCIAL_YEAR: timedelta(days=365 * 5),
    }

    # Return the default period or 7 days if not specified
    return default_periods.get(interval, timedelta(days=7))


def validate_metrics(metrics: list[Metric], supported_metrics: list[Metric]) -> None:
    """
    Validate a list of metrics against a list of supported metrics.

    Args:
        metrics: List of metrics to validate
        supported_metrics: List of supported metrics for this endpoint

    Raises:
        HTTPException: If any metric is not supported, with a helpful error message
    """
    unsupported_metrics = [m for m in metrics if m not in supported_metrics]

    if unsupported_metrics:
        supported_names = [m.value for m in supported_metrics]
        unsupported_names = [m.value for m in unsupported_metrics]

        error_detail = {
            "error": f"Unsupported metrics: {', '.join(unsupported_names)}",
            "supported_metrics": supported_names,
            "requested_metrics": [m.value for m in metrics],
            "invalid_metrics": unsupported_names,
            "hint": f"This endpoint supports: {', '.join(supported_names)}",
        }

        raise HTTPException(status_code=400, detail=error_detail)
