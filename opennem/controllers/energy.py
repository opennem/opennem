"""Energy controllers"""

import logging

from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import OpennemDataSet
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.controllers.schema import ExportResultRow
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.queries.energy import energy_network_fueltech_query
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("openne.controllers.energy")


def energy_fueltech_daily(
    network: NetworkSchema,
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    sub_networks: list[NetworkSchema] | None = None,
) -> OpennemDataSet:
    engine = get_database_engine()
    units = get_unit("energy_giga")

    query = energy_network_fueltech_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=sub_networks,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    results_energy = [ExportResultRow(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None) for i in row]

    results_market_value = [ExportResultRow(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None) for i in row]

    results_emissions = [ExportResultRow(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None) for i in row]

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
    )

    stats.append_set(stats_market_value)

    stats_emissions = stats_factory(
        stats=results_emissions,
        units=get_unit("emissions"),
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        code=time_series.network.code.lower(),
        localize=True,
    )

    stats.append_set(stats_emissions)

    return stats
