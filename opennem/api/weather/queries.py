from typing import List

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
    period: TimePeriod,
    network: NetworkSchema = NetworkNEM,
    timezone: str = "UTC",
):

    timezone = network.get_timezone(postgres_format=True)

    if not timezone:
        timezone = "UTC"

    __query = """
    SET SESSION TIME ZONE '{timezone}';

    select
        time_bucket_gapfill('{trunc}', observation_time) as observation_time,
        fs.station_id,
        interpolate(avg(fs.temp_air)) as generated
    from bom_observation fs
    where
        fs.station_id in ({station_codes})
        and fs.observation_time <= now()
        and fs.observation_time > now() - '{period}'::interval
    group by 1, 2
    order by 1 desc, 2 desc
    """

    query = __query.format(
        station_codes=station_id_case(station_codes),
        trunc=interval.interval_sql,
        period=period.period_sql,
        timezone=timezone,
    )

    return query
