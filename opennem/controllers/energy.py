"""Energy controllers"""

import logging

from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.units import get_unit
from opennem.db import db_connect
from opennem.queries.energy import get_energy_network_fueltech_query
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("openne.controllers.energy")


async def energy_fueltech_daily_v3(
    network: NetworkSchema,
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
) -> OpennemDataSet:
    engine = db_connect()
    units = get_unit("energy_giga")

    query = get_energy_network_fueltech_query(
        time_series=time_series,
        network=network,
        network_region=network_region_code,
    )

    async with engine.begin() as conn:
        logger.debug(query)
        res = await conn.execute(query)

    results = list(res)
    columns = res.keys()
    result_dicts = [dict(zip(columns, row, strict=False)) for row in results]

    results_energy = [
        DataQueryResult(interval=i["interval"], group_by=i["fueltech_code"], result=i["fueltech_energy_gwh"])
        for i in result_dicts
    ]

    results_market_value = [
        DataQueryResult(interval=i["interval"], group_by=i["fueltech_code"], result=i["fueltech_market_value_dollars"])
        for i in result_dicts
    ]

    results_emissions = [
        DataQueryResult(interval=i["interval"], group_by=i["fueltech_code"], result=i["fueltech_emissions"]) for i in result_dicts
    ]

    if not results_energy:
        raise Exception(f"No results from query: {query}")

    stats = stats_factory(
        stats=results_energy,
        units=units,
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        localize=True,
        code=network.code.lower(),
    )

    stats_market_value = stats_factory(
        stats=results_market_value,
        units=get_unit("market_value"),
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        localize=True,
        code=network.code.lower(),
    )

    stats.append_set(stats_market_value)

    stats_emissions = stats_factory(
        stats=results_emissions,
        units=get_unit("emissions"),
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        localize=True,
        code=time_series.network.code.lower(),
    )

    stats.append_set(stats_emissions)

    return stats
