"""
    Queries for network data

    @TODO use sqlalchemy text() compiled queries
"""

from datetime import datetime, timedelta
from textwrap import dedent
from typing import List, Optional

from opennem.schema.dates import TimeSeries
from opennem.utils.sql import duid_in_case


def power_facility_query(
    time_series: TimeSeries,
    facility_codes: List[str],
) -> str:

    __query = """
        select
            t.trading_interval at time zone '{timezone}',
            coalesce(avg(t.facility_power), 0),
            t.facility_code
        from (
            select
                time_bucket_gapfill('{trunc}', fs.trading_interval) AS trading_interval,
                coalesce(
                    avg(fs.generated), 0
                ) as facility_power,
                fs.facility_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            where
                fs.trading_interval <= '{date_max}' and
                fs.trading_interval > '{date_min}' and
                fs.facility_code in ({facility_codes_parsed})
            group by 1, 3
        ) as t
        group by 1, 3
        order by 1 desc
    """

    date_range = time_series.get_range()

    query = __query.format(
        facility_codes_parsed=duid_in_case(facility_codes),
        trunc=time_series.interval.interval_sql,
        period=time_series.period.period_sql,
        timezone=time_series.network.timezone_database,
        date_max=date_range.end,
        date_min=date_range.start,
    )

    return query


def energy_facility_query(time_series: TimeSeries, facility_codes: List[str]) -> str:
    """
    Get Energy for a list of facility codes
    """

    __query = """
    select
        date_trunc('{trunc}', t.trading_day at time zone '{timezone}') as trading_day,
        t.facility_code,
        sum(t.energy) as fueltech_energy,
        sum(t.market_value) as fueltech_market_value,
        sum(t.emissions) as fueltech_emissions
    from at_facility_daily t
    where
        t.trading_day <= '{date_max}' and
        t.trading_day >= '{date_min}' and
        t.facility_code in ({facility_codes_parsed})
    group by 1, 2
    order by
        trading_day desc;
    """

    date_range = time_series.get_range()

    query = dedent(
        __query.format(
            facility_codes_parsed=duid_in_case(facility_codes),
            trunc=time_series.interval.trunc,
            date_max=date_range.end,
            date_min=date_range.start,
            timezone=time_series.network.timezone_database,
        )
    )
    return query


def emission_factor_region_query(
    time_series: TimeSeries, network_region_code: Optional[str] = None
) -> str:
    __query = """
        select
            f.trading_interval at time zone '{timezone}' as ti,
            f.network_region,
            avg(f.emissions_per_mw) * 2
        from mv_region_emissions_45d f
        where
            f.network_id='{network_id}' and
            {network_region_query}
            f.trading_interval <= '{date_max}' and
            f.trading_interval >= '{date_min}'
        group by 1, 2
        order by 1 asc;
    """

    network_region_query = ""

    if network_region_code:
        network_region_query = f"f.network_region='{network_region_code}' and"

    date_range = time_series.get_range()

    query = dedent(
        __query.format(
            network_region_query=network_region_query,
            network_id=time_series.network.code,
            trunc=time_series.interval.trunc,
            date_max=date_range.end,
            date_min=date_range.start,
            timezone=time_series.network.timezone_database,
        )
    )
    return query


def network_fueltech_demand_query(time_series: TimeSeries) -> str:
    __query = """
        select
            f.fueltech_id,
            round(sum(fs.eoi_quantity) / 1000, 2) as energy,
            sum(bs.demand_total) as demand
        from facility_scada fs
        left join balancing_summary bs on bs.trading_interval = fs.trading_interval and bs.network_id = fs.network_id
        left join facility f on fs.facility_code = f.code
        join fueltech ft on f.fueltech_id = ft.code
        where
            fs.trading_interval >= '{date_min}'
            and fs.trading_interval < '{date_max}'
            and fs.network_id = '{network_id}'
            and f.dispatch_type = 'GENERATOR'
        group by 1;
    """

    date_range = time_series.get_range()

    date_min: datetime = date_range.end - timedelta(days=1)

    query = dedent(
        __query.format(
            network_id=time_series.network.code,
            trunc=time_series.interval.trunc,
            date_max=date_range.end,
            date_min=date_min,
            timezone=time_series.network.timezone_database,
        )
    )
    return query


def network_region_price_query(time_series: TimeSeries) -> str:
    __query = """
        select
            time_bucket('{trunc}', bs.trading_interval) as trading_interval,
            bs.network_id,
            bs.network_region,
            coalesce(avg(bs.price), avg(bs.price_dispatch)) as price
        from balancing_summary bs
        where
            bs.trading_interval >= '{date_min}'
            and bs.trading_interval < '{date_max}'
            and bs.network_id = '{network_id}'
            {network_regions_query}
        group by 1, 2, 3;
    """

    date_range = time_series.get_range()

    date_min: datetime = date_range.end - timedelta(days=1)

    network_regions_query = ""

    if time_series.network.regions:
        network_regions: str = ",".join([f"'{i.code}'" for i in time_series.network.regions])
        network_regions_query = f"and bs.network_region IN ({network_regions})"

    query = dedent(
        __query.format(
            network_id=time_series.network.code,
            trunc=time_series.interval.interval_human,
            date_max=date_range.end,
            date_min=date_min,
            network_regions_query=network_regions_query,
        )
    )
    return query
