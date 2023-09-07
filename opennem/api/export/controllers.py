import logging
import re

from opennem import settings
from opennem.api.exceptions import OpennemBaseHttpException, OpenNEMInvalidNetworkRegion
from opennem.api.export.queries import (
    country_stats_query,
    demand_network_region_query,
    energy_network_fueltech_query,
    interconnector_flow_network_regions_query,
    interconnector_power_flow,
    network_demand_query,
    power_and_emissions_network_fueltech_query,
    power_network_fueltech_query,
    power_network_interconnector_emissions_query,
    power_network_rooftop_query,
    price_network_query,
    weather_observation_query,
)
from opennem.api.facility.capacities import get_facility_capacities
from opennem.api.stats.controllers import get_latest_interval_live, stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.queries.flows import get_network_flows_emissions_market_value_query
from opennem.schema.network import NetworkAEMORooftop, NetworkNEM, NetworkSchema
from opennem.schema.stats import StatTypes

_valid_region = re.compile(r"^\w{1,4}\d?$")


logger = logging.getLogger(__name__)


class NoResults(OpennemBaseHttpException):
    detail = "No results"


def weather_daily(
    time_series: OpennemExportSeries,
    station_code: str,
    unit_name: str = "temperature_mean",
    include_min_max: bool = True,
    network_region: str | None = None,
    network: NetworkSchema | None = None,
) -> OpennemDataSet | None:
    engine = get_database_engine()
    units = get_unit(unit_name)

    query = weather_observation_query(
        time_series=time_series,
        station_codes=[station_code],
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    localize = bool(network)
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
        localize=localize,
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
            localize=localize,
        )

        stats_max = stats_factory(
            stats=temp_max,
            units=get_unit("temperature_max"),
            network=time_series.network,
            interval=time_series.interval,
            region=network_region,
            code="bom",
            group_field="temperature",
            localize=localize,
        )

        stats.append_set(stats_min)
        stats.append_set(stats_max)

    return stats


def gov_stats_cpi() -> OpennemDataSet | None:
    engine = get_database_engine()

    query = country_stats_query(StatTypes.CPI)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    stats = [DataQueryResult(interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None) for i in row]

    if len(stats) < 1:
        logger.error("No results for gov_stats_cpi returing blank set")
        return None

    result = stats_factory(
        stats,
        code="au.cpi",
        network=NetworkNEM,
        interval=human_to_interval("1Q"),
        units=get_unit("cpi"),
        group_field="gov",
    )

    return result


def power_flows_region_week(
    time_series: OpennemExportSeries,
    network_region_code: str,
) -> OpennemDataSet | None:
    """Gets the power flows for the most recent week for a region. Used in export_power for the JSON export sets

    from old flows
    """
    engine = get_database_engine()
    unit_power = get_unit("power")

    query = interconnector_power_flow(
        time_series=time_series,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        rows = list(c.execute(query))

    if not rows:
        logger.error(f"No results from interconnector_power_flow query for {time_series.interval}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[2], group_by="imports" if len(i) > 1 else None) for i in rows]
    exports = [DataQueryResult(interval=i[0], result=i[3], group_by="exports" if len(i) > 1 else None) for i in rows]

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

    return result


def network_flows_for_region(
    time_series: OpennemExportSeries,
    network_region_code: str,
    include_emissions: bool = False,
    include_emission_factors: bool = False,
) -> OpennemDataSet | None:
    "Network flows with optional emissions for a region. Up to last_complete_day"

    engine = get_database_engine()
    unit_power = get_unit("power")

    query = power_network_interconnector_emissions_query(
        time_series=time_series,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        rows = list(c.execute(query))

    if not rows:
        logger.error(f"No results from interconnector_power_flow query for {time_series.interval}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[1], group_by="imports" if len(i) > 1 else None) for i in rows]
    exports = [DataQueryResult(interval=i[0], result=i[2], group_by="exports" if len(i) > 1 else None) for i in rows]

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

    if include_emissions:
        unit_emissions = get_unit("emissions")

        import_emissions = [DataQueryResult(interval=i[0], group_by="imports", result=i[3]) for i in rows]
        export_emissions = [DataQueryResult(interval=i[0], group_by="exports", result=i[4]) for i in rows]

        result_import_emissions = stats_factory(
            import_emissions,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_import_emissions)

        result_export_emissions = stats_factory(
            export_emissions,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_export_emissions)

    if include_emission_factors:
        unit_emissions_factor = get_unit("emissions_factor")

        # import factors
        import_emissions_factors = [DataQueryResult(interval=i[0], group_by="imports", result=i[7]) for i in rows]
        result_import_emissions_factors = stats_factory(
            import_emissions_factors,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions_factor,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_import_emissions_factors)

        # export factors
        export_emissions_factors = [DataQueryResult(interval=i[0], group_by="exports", result=i[8]) for i in rows]
        result_export_emissions = stats_factory(
            export_emissions_factors,
            network=time_series.network,
            interval=time_series.interval,
            units=unit_emissions_factor,
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_export_emissions)

    return result


def power_flows_network_week(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
) -> OpennemDataSet | None:
    engine = get_database_engine()

    query = interconnector_flow_network_regions_query(time_series=time_series, network_region=network_region_code)

    logging.info(query)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        logger.warning(f"No results from interconnector_flow_network_regions_query with {time_series}")
        return None

    imports = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("regional_trade"),
        fueltech_group=True,
        group_field="power",
        include_group_code=True,
    )

    if not result:
        logger.error(f"No results from interconnector_flow_network_regions_query with {time_series}")
        return None

    return result


def demand_week(
    time_series: OpennemExportSeries,
    network_region_code: str | None,
    networks_query: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:
    engine = get_database_engine()

    query = network_demand_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

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


def power_week(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
    include_capacities: bool = False,
) -> OpennemDataSet | None:  # sourcery skip: use-fstring-for-formatting
    engine = get_database_engine()

    if network_region_code and not re.match(_valid_region, network_region_code):
        raise OpenNEMInvalidNetworkRegion()

    query = power_network_fueltech_query(
        time_series=time_series,
        networks_query=networks_query,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    stats = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    if not stats:
        logger.error(f"No results from power week query with {time_series}")
        return None

    result = stats_factory(
        stats,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
        include_code=True,
    )

    if not result:
        logger.error(f"No results from power week status factory with {time_series}")
        return None

    if include_capacities and network_region_code:
        region_fueltech_capacities = get_facility_capacities(time_series.network, network_region_code)

        for ft in result.data:
            if ft.fuel_tech in region_fueltech_capacities:
                ft.x_capacity_at_present = region_fueltech_capacities[ft.fuel_tech]

    # emissions
    if settings.show_emissions_in_power_outputs:
        emissions = [DataQueryResult(interval=i[0], result=i[3], group_by=i[1] if len(i) > 1 else None) for i in row]

        stats_emissions = stats_factory(
            emissions,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions"),
            region=network_region_code,
            fueltech_group=True,
            include_code=True,
        )

        result.append_set(stats_emissions)

    # emission factors
    if settings.show_emission_factors_in_power_outputs:
        emission_factors = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]
        stats_emission_factors = stats_factory(
            emission_factors,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            include_code=True,
        )

        result.append_set(stats_emission_factors)

    # price
    # adjust the interval size
    time_series_price = time_series.copy()

    query = price_network_query(
        time_series=time_series_price,
        networks_query=networks_query,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    stats_price = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    stats_market_value = stats_factory(
        stats=stats_price,
        code=network_region_code or time_series.network.code.lower(),
        units=get_unit("price_energy_mega"),
        network=time_series.network,
        interval=time_series.interval,
        region=network_region_code,
        include_code=True,
    )

    result.append_set(stats_market_value)

    # rooftop solar

    time_series_rooftop = time_series.copy()

    if time_series.network == NetworkNEM:
        time_series_rooftop.end = get_latest_interval_live(network=NetworkAEMORooftop)

    time_series_rooftop.interval = human_to_interval("30m")

    logger.debug(time_series_rooftop)

    query = power_network_rooftop_query(
        time_series=time_series_rooftop,
        networks_query=networks_query,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    rooftop_power = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    rooftop = stats_factory(
        rooftop_power,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=human_to_interval("30m"),
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
        cast_nulls=False,
        include_code=True,
    )

    # rooftop forecast
    rooftop_forecast = None

    if rooftop and rooftop.data:
        time_series_rooftop_forecast = time_series_rooftop.copy()
        time_series_rooftop_forecast.forecast = True

        logger.debug(time_series_rooftop_forecast)

        query = power_network_rooftop_query(
            time_series=time_series_rooftop_forecast, networks_query=networks_query, network_region=network_region_code
        )

        with engine.connect() as c:
            logger.debug(query)
            row = list(c.execute(query))

        rooftop_forecast_power = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

        rooftop_forecast = stats_factory(
            rooftop_forecast_power,
            network=time_series.network,
            interval=human_to_interval("30m"),
            units=get_unit("power"),
            region=network_region_code,
            fueltech_group=True,
            cast_nulls=False,
        )

    if rooftop and rooftop_forecast:
        if hasattr(rooftop, "data") and len(rooftop.data) > 0 and rooftop_forecast.data and len(rooftop_forecast.data) > 0:
            rooftop.data[0].forecast = rooftop_forecast.data[0].history
    else:
        logger.warning("No rooftop or rooftop forecast")

    result.append_set(rooftop)

    return result


def price_for_network_interval(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:
    """Returns price per interval for a network or network region"""
    engine = get_database_engine()

    query = price_network_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    price_data = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]

    price_set = stats_factory(
        stats=price_data,
        code=network_region_code or time_series.network.code.lower(),
        units=get_unit("price"),
        network=time_series.network,
        interval=time_series.interval,
        region=network_region_code,
    )

    return price_set


def power_and_emissions_for_network_interval(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    include_emission_factors: bool = False,
) -> OpennemDataSet | None:
    engine = get_database_engine()

    if network_region_code and not re.match(_valid_region, network_region_code):
        raise OpenNEMInvalidNetworkRegion()

    query = power_and_emissions_network_fueltech_query(
        time_series=time_series,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    power_stats = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row]
    emission_stats = [DataQueryResult(interval=i[0], result=i[3], group_by=i[1] if len(i) > 1 else None) for i in row]

    if not power_stats:
        logger.error(f"No results from emissions_for_network_interval query with {time_series}")
        return None

    power_result = stats_factory(
        power_stats,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
    )

    if not power_result:
        raise Exception(
            f"No power results for {time_series.network.code} in region {network_region_code} and date \
                range {time_series.get_range().start} => {time_series.get_range().end}"
        )

    emissions_result = stats_factory(
        emission_stats,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("emissions"),
        region=network_region_code,
        fueltech_group=True,
    )

    if emissions_result:
        power_result.append_set(emissions_result)

    if include_emission_factors:
        emission_factor_unit = get_unit("emissions_factor")

        emission_factor_results = [
            DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row
        ]

        emission_factor_set = stats_factory(
            emission_factor_results,
            network=time_series.network,
            interval=time_series.interval,
            units=emission_factor_unit,
            region=network_region_code,
            fueltech_group=True,
        )
        power_result.append_set(emission_factor_set)

    return power_result


def demand_network_region_daily(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:  # sourcery skip: raise-specific-error
    """Gets demand market_value and energy for a network -> network_region"""
    engine = get_database_engine()

    query = demand_network_region_query(time_series=time_series, network_region=network_region_code, networks=networks)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    results_energy = [DataQueryResult(interval=i[0], group_by=i[2], result=i[3] if len(i) > 1 else None) for i in row]

    results_market_value = [DataQueryResult(interval=i[0], group_by=i[2], result=i[4] if len(i) > 1 else None) for i in row]

    if not results_energy:
        logger.error(f"No results from query: {query}")
        return None

    # demand based values for VWP
    stats = stats_factory(
        stats=results_energy,
        units=get_unit("demand.energy_giga"),
        network=time_series.network,
        fueltech_group=False,
        interval=time_series.interval,
        region=network_region_code,
    )

    if not stats:
        raise Exception(f"Not stats for demand_network_region_daily: {network_region_code}")

    if stats_market_value := stats_factory(
        stats=results_market_value,
        units=get_unit("demand.market_value"),
        network=time_series.network,
        fueltech_group=False,
        interval=time_series.interval,
        code=time_series.network.code.lower(),
        region=network_region_code,
    ):
        stats.append_set(stats_market_value)

    return stats


def energy_fueltech_daily(
    time_series: OpennemExportSeries,
    network_region_code: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> OpennemDataSet | None:
    engine = get_database_engine()
    units = get_unit("energy_giga")

    query = energy_network_fueltech_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    results_energy = [DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None) for i in row]

    results_market_value = [DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None) for i in row]

    results_emissions = [DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None) for i in row]

    if not results_energy:
        logger.error(f"No results from query: {query}")
        return None

    stats = stats_factory(
        stats=results_energy,
        units=units,
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        localize=True,
        code=time_series.network.code.lower(),
    )

    if not stats:
        return None

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


def energy_interconnector_flows_and_emissions_v2(
    time_series: OpennemExportSeries, network_region_code: str, include_emission_factor: bool = True
) -> OpennemDataSet | None:
    engine = get_database_engine()
    unit_energy = get_unit("energy_giga")
    unit_emissions = get_unit("emissions")

    query = get_network_flows_emissions_market_value_query(time_series=time_series, network_region_code=network_region_code)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if not row:
        logger.error(
            f"No results from energy_interconnector_flows_and_emissions for {time_series.network} "
            "{network_region_code} and {time_series.start} => {time_series.end}"
        )
        return None

    imports = [DataQueryResult(interval=i[0], group_by="imports", result=i[3]) for i in row]
    exports = [DataQueryResult(interval=i[0], group_by="exports", result=i[4]) for i in row]

    import_emissions = [DataQueryResult(interval=i[0], group_by="imports", result=i[5]) for i in row]
    export_emissions = [DataQueryResult(interval=i[0], group_by="exports", result=i[6]) for i in row]

    import_mv = [DataQueryResult(interval=i[0], group_by="imports", result=i[7]) for i in row]
    export_mv = [DataQueryResult(interval=i[0], group_by="exports", result=i[8]) for i in row]

    result = stats_factory(
        imports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_energy,
        region=network_region_code,
        fueltech_group=True,
    )

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_energy,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    result_import_emissions = stats_factory(
        import_emissions,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_emissions,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_import_emissions)

    result_export_emissions = stats_factory(
        export_emissions,
        network=time_series.network,
        interval=time_series.interval,
        units=unit_emissions,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_export_emissions)

    # market value for flows

    result_import_mv = stats_factory(
        import_mv,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("market_value"),
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_import_mv)

    result_export_mv = stats_factory(
        export_mv,
        network=time_series.network,
        interval=time_series.interval,
        units=get_unit("market_value"),
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_export_mv)

    if include_emission_factor:
        import_emission_factor = [DataQueryResult(interval=i[0], group_by="imports", result=i[9]) for i in row]
        export_emission_factor = [DataQueryResult(interval=i[0], group_by="exports", result=i[10]) for i in row]

        result_import_emission_factor = stats_factory(
            import_emission_factor,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_import_emission_factor)

        result_export_emission_factor = stats_factory(
            export_emission_factor,
            network=time_series.network,
            interval=time_series.interval,
            units=get_unit("emissions_factor"),
            region=network_region_code,
            fueltech_group=True,
            localize=False,
        )

        result.append_set(result_export_emission_factor)

    return result
