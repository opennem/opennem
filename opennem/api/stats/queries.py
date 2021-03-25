"""
    Queries for network data

    @TODO use sqlalchemy text() compiled queries
"""

from textwrap import dedent
from typing import List

from opennem.core.normalizers import normalize_duid
from opennem.schema.dates import TimeSeries


def duid_in_case(facility_codes: List[str]) -> str:
    return ",".join(["'{}'".format(i) for i in map(normalize_duid, facility_codes)])


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
        t.code,
        sum(t.energy) as fueltech_energy,
        sum(t.market_value) as fueltech_market_value,
        sum(t.emissions) as fueltech_emissions
    from mv_network_fueltech_days t
    where
        t.trading_day <= '{date_max}' and
        t.trading_day >= '{date_min}' and
        t.code in ({facility_codes_parsed})
    group by 1, 2
    order by
        trading_day desc;
    """

    date_range = time_series.get_range()

    if time_series.period.period <= 43800:
        __query = """
        select
            date_trunc('{trunc}', t.trading_interval at time zone '{timezone}') as trading_day,
            t.code,
            sum(t.energy) as fueltech_energy,
            sum(t.market_value) as fueltech_market_value,
            sum(t.emissions) as fueltech_emissions
        from mv_facility_45d t
        where
            t.trading_interval <= '{date_max}' and
            t.trading_interval >= '{date_min}' and
            t.code in ({facility_codes_parsed})
        group by 1, 2
        order by
            trading_day desc;
        """

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
