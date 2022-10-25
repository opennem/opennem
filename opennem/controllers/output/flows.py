import logging
import re

from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet, RegionFlowEmissionsResult
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.flows import net_flows_emissions
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.queries.flows import energy_network_flow_query, energy_network_interconnector_emissions_query
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.controllers.flows")


def energy_interconnector_region_daily(
    time_series: OpennemExportSeries,
    network_region_code: str,
) -> OpennemDataSet | None:
    """Old version of interconnector region daily"""
    engine = get_database_engine()
    units = get_unit("energy_giga")

    query = energy_network_flow_query(
        time_series=time_series,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        return None

    imports = [DataQueryResult(interval=i[0], group_by="imports", result=i[1]) for i in row]

    exports = [DataQueryResult(interval=i[0], group_by="exports", result=i[2]) for i in row]

    imports_mv = [DataQueryResult(interval=i[0], group_by="imports", result=i[3]) for i in row]

    exports_mv = [DataQueryResult(interval=i[0], group_by="exports", result=i[4]) for i in row]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
    )

    # Bail early on no interconnector
    # don't error
    if not result:
        logger.warn("No interconnector energy result")
        return result

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    result_imports_mv = stats_factory(
        imports_mv,
        units=get_unit("market_value"),
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        code=time_series.network.code.lower(),
        localize=False,
    )
    result.append_set(result_imports_mv)

    result_export_mv = stats_factory(
        exports_mv,
        units=get_unit("market_value"),
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        code=time_series.network.code.lower(),
        localize=False,
    )
    result.append_set(result_export_mv)

    return result


def energy_interconnector_emissions_region_daily(
    time_series: OpennemExportSeries,
    network_region_code: str,
    networks_query: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:
    engine = get_database_engine()
    units = get_unit("emissions")

    query = energy_network_interconnector_emissions_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        return None

    stats = [
        RegionFlowEmissionsResult(
            interval=i[0],
            flow_from=i[1],
            flow_to=i[2],
            energy=i[3],
            flow_from_emissions=i[4],
            flow_to_emissions=i[5],
        )
        for i in row
    ]

    stats_grouped = net_flows_emissions(network_region_code, stats, time_series.interval)

    imports = stats_grouped["imports"]
    exports = stats_grouped["exports"]

    # imports = [DataQueryResult(interval=i[0], group_by="imports", result=i[5]) for i in row]

    # exports = [DataQueryResult(interval=i[0], group_by="exports", result=i[4]) for i in row]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    # Bail early on no interconnector
    # don't error
    if not result:
        return result

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_exports)

    return result
