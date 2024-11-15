import logging

from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.units import get_unit
from opennem.db import db_connect
from opennem.queries.demand import network_demand_query
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.controllers.demand")


async def demand_week_v3(
    time_series: OpennemExportSeries,
    network_region_code: str | None,
    networks_query: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:
    engine = db_connect()

    query = network_demand_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    async with engine.begin() as conn:
        logger.debug(query)
        result = await conn.execute(query)
        row = result.fetchall()

    if not row:
        logger.error(f"No results from network_demand_query with {time_series}")
        return None

    demand = [DataQueryResult(interval=i[0], result=i[2], group_by="demand" if len(i) > 1 else None) for i in row]

    result = stats_factory(
        demand,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("demand"),
        region=network_region_code,
    )

    if not result:
        logger.error(f"No results from network_demand_query with {time_series}")
        return None

    return result
