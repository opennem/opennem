from typing import List

from opennem.core.normalizers import normalize_duid
from opennem.schema.time import TimeInterval, TimePeriod


def station_id_case(station_codes: List[str]) -> str:
    return ",".join(
        ["'{}'".format(i) for i in map(normalize_duid, station_codes)]
    )


def observation_query(
    station_codes: List[str],
    interval: TimeInterval,
    period: TimePeriod,
    timezone: str = "AEST",
):
    __query = """with intervals as (
        select generate_series(
            date_trunc('{trunc}', now() AT TIME ZONE '{timezone}') - '{period}'::interval,
            date_trunc('{trunc}', now() AT TIME ZONE '{timezone}'),
            '{interval}'::interval
        )::timestamp as interval
    )

    select
        i.interval,
        fs.generated,
        fs.station_id
    from intervals i
    left outer join
        (select
            date_trunc('{trunc}', fs.observation_time AT TIME ZONE '{timezone}')::timestamp  {interval_remainder} as interval,
            fs.station_id,
            coalesce(avg(fs.temp_air), 0) as generated
            from bom_observation fs
            where
                fs.station_id in ({station_codes})
                and fs.observation_time > now() AT TIME ZONE '{timezone}' - '{period}'::interval
            group by 1, 2
        ) as fs on fs.interval = i.interval
    order by 1 desc, 2 desc"""

    query = __query.format(
        station_codes=station_id_case(station_codes),
        trunc=interval.trunc,
        interval=interval.interval_human,
        interval_remainder=interval.get_sql_join(
            field="observation_time", timezone=timezone
        ),
        period=period.period_sql,
        timezone=timezone,
    )

    return query
