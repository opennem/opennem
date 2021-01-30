from textwrap import dedent
from typing import List, Optional, Union

from opennem.api.stats.schema import ScadaDateRange
from opennem.core.normalizers import normalize_duid
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.time import human_to_timedelta


def station_id_case(station_codes: List[str]) -> str:
    return ",".join(["'{}'".format(i) for i in map(normalize_duid, station_codes)])


def observation_query(
    station_codes: List[str],
    interval: TimeInterval,
    network: NetworkSchema = NetworkNEM,
    period: Optional[TimePeriod] = None,
    scada_range: Optional[ScadaDateRange] = None,
    year: Optional[Union[str, int]] = None,
) -> str:
    if isinstance(year, int):
        year = str(year)

    timezone = network.timezone_database

    if not timezone:
        timezone = "AEST"

    __query = """
    select
        time_bucket_gapfill('{trunc}', observation_time) as observation_time,
        fs.station_id as station_id,
        avg(fs.temp_air) as temp_air,
        min(fs.temp_air) as temp_min,
        max(fs.temp_air) as temp_max
    from bom_observation fs
    where
        fs.station_id in ({station_codes})
        and fs.observation_time <= {date_end}
        and fs.observation_time > {date_start_condition}
    group by 1, 2;
    """
    date_end = ""

    if scada_range:
        date_end = scada_range.get_end_sql()

    date_start_condition = ""

    if period:
        date_start_condition = "{date_end}::timestamp - '{period}'::interval".format(
            date_end=date_end, period=period.period_sql
        )
        date_start_condition = "'{}'".format(scada_range.get_end() - human_to_timedelta("7d"))

    if year:
        date_start_condition = "'{year}-12-31'::date".format(year=int(year) - 1)
        date_end = "'{year}-12-31'::date".format(year=year)

    if not period and not year:
        if not scada_range:
            raise Exception("require a scada range ")

        date_start_condition = "'{}'".format(scada_range.get_start())

    query = dedent(
        __query.format(
            station_codes=station_id_case(station_codes),
            trunc=interval.interval_sql,
            timezone=timezone,
            date_start_condition=date_start_condition,
            date_end=date_end,
        )
    )

    return query


def observation_query_all(
    station_codes: List[str],
    scada_range: ScadaDateRange,
    network: NetworkSchema = NetworkNEM,
) -> str:
    #

    timezone = network.timezone_database

    if not timezone:
        timezone = "UTC"

    __query = """
        select
            date_trunc('month', t.observation_time at time zone '{timezone}') as observation_month,
            t.station_id,
            avg(t.temp_avg),
            min(t.temp_min),
            max(t.temp_max)
        from
            (
                select
                    time_bucket_gapfill('1 day', observation_time) as observation_time,
                    fs.station_id,
                    avg(fs.temp_air) as temp_avg,
                    min(fs.temp_air) as temp_min,
                    max(fs.temp_air) as temp_max
                from bom_observation fs
                where
                    fs.station_id in ({station_codes})
                    and fs.observation_time <= {date_end}
                    and fs.observation_time > {date_start}
                group by 1, 2
            ) as t
        group by 1, 2
        order by 1 desc, 2 desc
    """

    date_end = scada_range.get_end_sql()
    date_start = scada_range.get_start_sql()

    query = __query.format(
        station_codes=station_id_case(station_codes),
        timezone=timezone,
        date_start=date_start,
        date_end=date_end,
    )

    return query
