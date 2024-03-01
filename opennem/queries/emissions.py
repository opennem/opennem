"""OpenNEM Price Queries"""

from datetime import datetime
from textwrap import dedent

from sqlalchemy import text as sql
from sqlalchemy.sql.expression import TextClause

from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.utils.dates import num_intervals_between_datetimes

from .exceptions import TooManyIntervals


def get_emission_factor_region_query(
    date_min: datetime,
    date_max: datetime,
    interval: TimeInterval,
    network: NetworkSchema,
    network_region_code: str | None = None,
) -> TextClause:
    """Gets emission query"""

    __query = """
        select
            t.trading_interval at time zone '{timezone}',
            t.network_region,
            coalesce(sum(t.power), 0) as generated,
            coalesce(sum(t.emissions), 0) as emissions,
            case when sum(t.power) > 0 then
                sum(t.emissions) / sum(t.power)
            else 0
            end as emissions_factor
        from
        (
            select
                time_bucket_gapfill('{trunc}', fs.trading_interval) as trading_interval,
                f.network_region as network_region,
                coalesce(sum(fs.generated), 0) as power,
                coalesce(sum(fs.generated) * max(f.emissions_factor_co2), 0) as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            where
                fs.is_forecast is False and
                f.interconnector = False and
                f.network_id = '{network_id}' and
                fs.generated > 0 and
                {network_regions_query}
                fs.trading_interval >= '{date_min}' and
                fs.trading_interval <= '{date_max}'
            group by
                1, f.code, 2
        ) as t
        group by 1, 2
        order by 1 asc, 2;
    """

    # regions clause
    network_regions_query = ""

    if network_region_code:
        network_regions_query = f"f.network_region = '{network_region_code.upper()}' and"

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
                timezone=network.timezone_database,
            )
        )
    )
