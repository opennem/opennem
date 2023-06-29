""" OpenNEM Price Queries """
from datetime import datetime
from textwrap import dedent

from sqlalchemy import text as sql
from sqlalchemy.sql.expression import TextClause

from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.utils.dates import num_intervals_between_datetimes

from .exceptions import TooManyIntervals


def get_network_region_price_query(
    date_min: datetime,
    date_max: datetime,
    network: NetworkSchema,
    interval: TimeInterval | None = None,
    network_region_code: str | None = None,
    forecast: bool = False,
) -> TextClause:
    """Gets a price query"""

    __query = """
        select
            time_bucket_gapfill('{trunc}', bs.trading_interval) as trading_interval,
            bs.network_id,
            bs.network_region,
            coalesce(avg(bs.price), avg(bs.price_dispatch)) as price
        from balancing_summary bs
        where
            bs.trading_interval >= '{date_min}'
            and bs.trading_interval <= '{date_max}'
            and bs.network_id = '{network_id}'
            {forecast_clause}
            {network_regions_query}
        group by 1, 2, 3;
    """

    # regions clause
    network_regions_query = ""

    if network_region_code:
        network_regions_query = f"and bs.network_region = '{network_region_code.upper()}'"

    # forecast clause
    forecast_clause = ""

    if forecast:
        forecast_clause = "and bs.forecast = true"

    # if not interval provided get the default from the network
    if not interval:
        interval = network.get_interval()

    num_intervals = num_intervals_between_datetimes(interval.get_timedelta(), date_min, date_max)

    if num_intervals > 1000:
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
