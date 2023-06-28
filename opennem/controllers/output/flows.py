import logging

from opennem import settings
from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.queries.flows import power_network_flow_query

logger = logging.getLogger("opennem.controllers.flows")


def power_flows_per_interval(
    time_series: OpennemExportSeries,
    network_region_code: str,
    include_emissions_and_factors: bool = True,
) -> OpennemDataSet | None:
    """Gets the power flows for the most recent week for a region from the aggregate table

    Supports down to a resolution of per-interval
    """
    engine = get_database_engine()
    unit_power = get_unit("power")

    query = power_network_flow_query(
        time_series=time_series,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        rows = list(c.execute(query))

    if not rows:
        logger.error(f"No results from interconnector_power_flow query for {time_series.interval}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[3], group_by="imports" if len(i) > 1 else None) for i in rows]
    exports = [DataQueryResult(interval=i[0], result=i[4], group_by="exports" if len(i) > 1 else None) for i in rows]
    emissions_imports = [DataQueryResult(interval=i[0], result=i[5], group_by="imports" if len(i) > 1 else None) for i in rows]
    emissions_exports = [DataQueryResult(interval=i[0], result=i[6], group_by="exports" if len(i) > 1 else None) for i in rows]
    emissions_factor_imports = [
        DataQueryResult(interval=i[0], result=i[9], group_by="imports" if len(i) > 1 else None) for i in rows
    ]
    emissions_factor_exports = [
        DataQueryResult(interval=i[0], result=i[10], group_by="exports" if len(i) > 1 else None) for i in rows
    ]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        logger.error(f"No results from interconnector_power_flow stats facoty for {time_series}")
        return None

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_power,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    if settings.show_emissions_in_power_outputs:
        result_emissions_imports = stats_factory(
            emissions_imports,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions"),
            region=network_region_code,
            fueltech_group=True,
        )
        result.append_set(result_emissions_imports)

        result_emissions_exports = stats_factory(
            emissions_exports,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions"),
            region=network_region_code,
            fueltech_group=True,
        )
        result.append_set(result_emissions_exports)

    if settings.show_emission_factors_in_power_outputs:
        result_emissions_factor_imports = stats_factory(
            emissions_factor_imports,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
        )

        result.append_set(result_emissions_factor_imports)

        result_emissions_factor_exports = stats_factory(
            emissions_factor_exports,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
        )

        result.append_set(result_emissions_factor_exports)

    return result
