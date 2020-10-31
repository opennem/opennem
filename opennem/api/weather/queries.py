from textwrap import dedent
from typing import List, Optional

from opennem.api.stats.schema import ScadaDateRange
from opennem.core.normalizers import normalize_duid
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod


def station_id_case(station_codes: List[str]) -> str:
    return ",".join(
        ["'{}'".format(i) for i in map(normalize_duid, station_codes)]
    )


def observation_query(
    station_codes: List[str],
    interval: TimeInterval,
    network: NetworkSchema = NetworkNEM,
    timezone: str = "UTC",
    period: Optional[TimePeriod] = None,
    scada_range: Optional[ScadaDateRange] = None,
    year: Optional[str] = None,
):

    timezone = network.get_timezone(postgres_format=True)

    if not timezone:
        timezone = "UTC"

    __query = """
    SET SESSION TIME ZONE '{timezone}';

    select
        time_bucket_gapfill('{trunc}', observation_time) as observation_time,
        fs.station_id,
        interpolate(avg(fs.temp_air)) as temp_avg,
        interpolate(min(fs.temp_air)) as temp_min,
        interpolate(max(fs.temp_air)) as temp_max
    from bom_observation fs
    where
        fs.station_id in ({station_codes})
        and fs.observation_time <= {date_end}
        and fs.observation_time >= {date_start_condition}
    group by 1, 2
    order by 1 desc, 2 desc
    """

    date_end = "now()"

    if scada_range:
        date_end = scada_range.get_end_sql()

    date_start_condition = ""

    if period:
        date_start_condition = "{date_end}::timestamp - '{period}'::interval".format(
            date_end=date_end, period=period.period_sql
        )

    if year:
        date_start_condition = "'{year}-01-01'::date".format(year=year)

    if not period and not year:
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
):

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
                    interpolate(avg(fs.temp_air)) as temp_avg,
                    interpolate(min(fs.temp_air)) as temp_min,
                    interpolate(max(fs.temp_air)) as temp_max
                from bom_observation fs
                where
                    fs.station_id in ({station_codes})
                    and fs.observation_time <= {date_end}
                    and fs.observation_time >= {date_start}
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

