import logging
from datetime import datetime

from sqlalchemy import TextClause, text

from opennem.queries.utils import list_to_case
from opennem.schema.time import TimeInterval

logger = logging.getLogger(__name__)


def get_weather_observation_query(
    interval: TimeInterval, date_start: datetime, date_end: datetime, station_codes: list[str]
) -> TextClause:
    """
    Get weather observations for a list of stations and a date range.
    """

    __query = """
    select
        time_bucket_gapfill('{interval}', fs.observation_time) as interval,
        fs.station_id as station_id,
        coalesce(avg(fs.temp_air), NULL) as temp_air,
        coalesce(min(fs.temp_min), min(fs.temp_air)) as temp_min,
        coalesce(max(fs.temp_max), max(fs.temp_air)) as temp_max
    from bom_observation fs
    where
        fs.station_id in ({station_codes}) and
        fs.observation_time <= '{date_end}' and
        fs.observation_time >= '{date_start}'
    group by 1, 2
    order by 1 desc;
    """

    query = __query.format(
        station_codes=list_to_case(station_codes),
        date_start=date_start,
        date_end=date_end,
        interval=interval.interval_sql,
    )

    return text(query)
