"""OpenNEM Price Queries"""

from datetime import datetime
from textwrap import dedent

from sqlalchemy import text as sql
from sqlalchemy.sql.expression import TextClause

from opennem.db.utils import get_clickhouse_interval
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.utils.dates import num_intervals_between_datetimes

from .exceptions import TooManyIntervals


def get_network_region_price_query(
    network: NetworkSchema,
    date_min: datetime,
    date_max: datetime | None = None,
    interval: TimeInterval | None = None,
    network_region_code: str | None = None,
    forecast: bool = False,
) -> TextClause:
    """Gets a price query"""

    __query = """
        select
            time_bucket_gapfill('{trunc}', bs.interval) as interval,
            bs.network_id,
            bs.network_region,
            avg(bs.price) as price
        from mv_balancing_summary bs
        where
            bs.interval >= '{date_min}'
            and bs.interval <= '{date_max}'
            and bs.network_id = '{network_id}'
            {forecast_clause}
            {network_regions_query}
        group by 1, 2, 3;
    """
    # if only a single interval with date_min set date_max
    if not date_max:
        date_max: datetime = date_min

    # regions clause
    network_regions_query: str = ""

    if network_region_code:
        network_regions_query = f"and bs.network_region = '{network_region_code.upper()}'"

    # forecast clause
    forecast_clause: str = ""

    if forecast:
        forecast_clause = "and bs.forecast = true"

    # if not interval provided get the default from the network
    if not interval:
        interval = network.get_interval()

    num_intervals = num_intervals_between_datetimes(interval.get_timedelta(), date_min, date_max)

    if num_intervals > 2016:  # max 7 days of 5 minute intervals
        raise TooManyIntervals("Too many intervals: {num_intervals}. Try reducing date range or interval size")

    return sql(
        dedent(
            __query.format(
                network_id=network.code,
                trunc=interval.interval_human,
                date_max=date_max,
                date_min=date_min,
                network_regions_query=network_regions_query,
                forecast_clause=forecast_clause,
            )
        )
    )


def get_network_price_demand_query_analytics(
    network: NetworkSchema,
    date_min: datetime,
    date_max: datetime | None = None,
    interval: TimeInterval | None = None,
    network_region_code: str | None = None,
) -> str:
    """
    Get price and demand from ClickHouse market_summary table.

    Args:
        network: Network schema
        date_min: Start date
        date_max: End date (optional)
        interval: Time interval for aggregation (optional)

    Returns:
        str: ClickHouse SQL query
    """
    # If only a single interval with date_min set date_max
    if not date_max:
        date_max = date_min

    # If no interval provided get the default from the network
    if not interval:
        interval = network.get_interval()

    # Validate number of intervals
    num_intervals = num_intervals_between_datetimes(interval.get_timedelta(), date_min, date_max)

    if num_intervals > 9216:  # max 7 days of 5 minute intervals
        raise TooManyIntervals(
            f"Too many intervals: {num_intervals}. Try reducing date range or interval size: {date_min} to {date_max}"
        )

    time_bucket = get_clickhouse_interval(interval)

    # network regions query
    network_regions_query = ""

    if network_region_code:
        network_regions_query = f"and network_region = '{network_region_code.upper()}'"

    # strip timezone from date_min and date_max
    date_min = date_min.replace(tzinfo=None)
    date_max = date_max.replace(tzinfo=None)

    query = f"""
        SELECT
            {time_bucket}(interval) AS interval,
            network_id,
            network_region,
            sum(price) AS price,
            sum(demand) AS demand,
            sum(demand_total) AS demand_total
        FROM market_summary
        WHERE network_id = '{network.code}'
            AND interval >= parseDateTimeBestEffort('{date_min}')
            AND interval <= parseDateTimeBestEffort('{date_max}')
            {network_regions_query}
        GROUP BY
            interval,
            network_id,
            network_region
        ORDER BY interval desc, network_id, network_region
    """

    return query
