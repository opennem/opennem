"""
Market data router for OpenNEM API.

This module handles market-specific metrics like price and demand.
"""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from opennem.api.market.queries import get_market_timeseries_query
from opennem.api.market.schema import MarketMetric, MarketTimeSeries
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db import get_read_session
from opennem.schema.network import NetworkSchema

router = APIRouter()
logger = logging.getLogger(__name__)

_SUPPORTED_METRICS = [
    Metric.PRICE,
    Metric.DEMAND,
    Metric.DEMAND_ENERGY,
]


def _group_rows_by_column(rows: list[dict], column: str) -> dict[str, list[dict]]:
    """Group rows by a column value."""
    groups = {}
    for row in rows:
        key = row[column]
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    return groups


def format_market_timeseries_response(
    rows: list[dict],
    network: NetworkSchema,
    metrics: list[MarketMetric],
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
) -> MarketTimeSeries:
    """Format raw query results into a MarketTimeSeries response."""
    # Group rows by region
    region_groups = _group_rows_by_column(rows, "network_region")

    # Format results for each region and metric
    results = []
    for region, region_rows in region_groups.items():
        for metric in metrics:
            # Convert rows to [timestamp, value] pairs
            data = [[row["interval"], row[metric]] for row in region_rows]

            results.append(
                {
                    "name": f"{region}_{metric}",
                    "date_start": date_start,
                    "date_end": date_end,
                    "labels": {"region": region, "metric": metric},
                    "data": data,
                }
            )

    return MarketTimeSeries(network_code=network.code, interval=interval, start=date_start, end=date_end, results=results)


@router.get("/network/{network_code}")
async def get_network_data(
    network_code: str,
    metrics: Annotated[list[MarketMetric], Query()],
    interval: Interval = Interval.HOUR,
    date_start: datetime | None = None,
    date_end: datetime | None = None,
) -> MarketTimeSeries:
    """
    Get market data for a network.

    Args:
        network: The network to get data for
        metrics: List of metrics to query
        interval: Time interval to aggregate by
        date_start: Start time for the query (network time)
        date_end: End time for the query (network time)

    Returns:
        MarketTimeSeries: Time series data for the requested metrics
    """

    # Get network
    network = get_api_network_from_code(network_code)

    # Validate metrics
    validate_metrics(metrics, _SUPPORTED_METRICS)

    # Get default time range if not specified
    if date_start is None:
        date_start = interval.default_start()
    if date_end is None:
        date_end = interval.default_end()

    # Build and execute query
    query, params = get_market_timeseries_query(
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
    )

    async with get_read_session() as session:
        rows = await session.execute(query, params)
        rows = [dict(row) for row in rows]

    # Format response
    return format_market_timeseries_response(
        rows=rows,
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
    )
