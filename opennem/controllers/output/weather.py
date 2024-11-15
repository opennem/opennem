import logging

from opennem.api.export.controllers import NoResults
from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.units import get_unit
from opennem.db import db_connect
from opennem.queries.weather import get_weather_observation_query

logger = logging.getLogger("opennem.controllers.output.weather")


async def run_weather_daily_v3(
    time_series: OpennemExportSeries,
    station_code: str,
    unit_name: str = "temperature_mean",
    include_min_max: bool = True,
    network_region: str | None = None,
) -> OpennemDataSet | None:
    engine = db_connect()
    units = get_unit(unit_name)

    query = get_weather_observation_query(
        interval=time_series.interval,
        date_start=time_series.start,
        date_end=time_series.end,
        station_codes=[station_code],
    )

    async with engine.begin() as conn:
        result = await conn.execute(query)
        row = result.fetchall()

    temp_avg = [DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None) for i in row]

    temp_min = [DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None) for i in row]

    temp_max = [DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None) for i in row]

    if not temp_avg:
        logger.info(f"No weather results for {station_code}")
        raise NoResults()

    stats = stats_factory(
        stats=temp_avg,
        units=units,
        network=time_series.network,
        interval=time_series.interval,
        region=network_region,
        code="bom",
        group_field="temperature",
    )

    if not stats:
        raise NoResults()

    if include_min_max:
        stats_min = stats_factory(
            stats=temp_min,
            units=get_unit("temperature_min"),
            network=time_series.network,
            interval=time_series.interval,
            region=network_region,
            code="bom",
            group_field="temperature",
        )

        stats_max = stats_factory(
            stats=temp_max,
            units=get_unit("temperature_max"),
            network=time_series.network,
            interval=time_series.interval,
            region=network_region,
            code="bom",
            group_field="temperature",
        )

        stats.append_set(stats_min)
        stats.append_set(stats_max)

    return stats
