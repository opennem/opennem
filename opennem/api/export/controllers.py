import logging
import re
from typing import List, Optional

from opennem.api.exceptions import OpennemBaseHttpException, OpenNEMInvalidNetworkRegion
from opennem.api.export.queries import (
    country_stats_query,
    demand_network_region_query,
    energy_network_fueltech_query,
    energy_network_interconnector_emissions_query,
    interconnector_flow_network_regions_query,
    interconnector_power_flow,
    network_demand_query,
    power_network_fueltech_query,
    power_network_rooftop_query,
    price_network_query,
    weather_observation_query,
)
from opennem.api.facility.capacities import get_facility_capacities
from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.schema.dates import TimeSeries
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.stats import StatTypes
from opennem.schema.time import TimePeriod

_valid_region = re.compile(r"^\w{1,4}\d?$")


logger = logging.getLogger(__name__)


class NoResults(OpennemBaseHttpException):
    detail = "No results"


def weather_daily(
    time_series: TimeSeries,
    station_code: str,
    unit_name: str = "temperature_mean",
    include_min_max: bool = True,
    network_region: Optional[str] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()
    units = get_unit(unit_name)

    query = weather_observation_query(
        time_series=time_series,
        station_codes=[station_code],
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    temp_avg = [DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None) for i in row]

    temp_min = [DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None) for i in row]

    temp_max = [DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None) for i in row]

    if len(temp_avg) < 1:
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
        localize=False,
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
            localize=False,
        )

        stats_max = stats_factory(
            stats=temp_max,
            units=get_unit("temperature_max"),
            network=time_series.network,
            interval=time_series.interval,
            region=network_region,
            code="bom",
            group_field="temperature",
            localize=False,
        )

        stats.append_set(stats_min)
        stats.append_set(stats_max)

    return stats


def gov_stats_cpi() -> Optional[OpennemDataSet]:
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
        period=human_to_period("all"),
        units=get_unit("cpi"),
        group_field="gov",
    )

    return result


def power_flows_region_week(
    time_series: TimeSeries,
    network_region_code: str,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    query = interconnector_power_flow(time_series=time_series, network_region=network_region_code)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if len(row) < 1:
        logger.error("No results from interconnector_power_flow query for {}".format(time_series))
        return None

    imports = [DataQueryResult(interval=i[0], result=i[2], group_by="imports" if len(i) > 1 else None) for i in row]

    exports = [DataQueryResult(interval=i[0], result=i[3], group_by="exports" if len(i) > 1 else None) for i in row]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
        period=human_to_period("7d"),
        interval=human_to_interval("5m"),
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        logger.error("No results from interconnector_power_flow stats facoty for {}".format(time_series))
        return None

    result_exports = stats_factory(
        exports,
        # code=network_region_code or network.code,
        network=time_series.network,
        period=human_to_period("7d"),
        interval=human_to_interval("5m"),
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    return result


def power_flows_network_week(
    time_series: TimeSeries,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    query = interconnector_flow_network_regions_query(time_series=time_series)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if len(row) < 1:
        logger.error("No results from interconnector_flow_network_regions_query with {}".format(time_series))
        return None

    imports = [DataQueryResult(interval=i[0], result=i[4], group_by=i[1] if len(i) > 1 else None) for i in row]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
        period=time_series.period,
        interval=time_series.interval,
        units=get_unit("regional_trade"),
        # fueltech_group=True,
        group_field="power",
        include_group_code=True,
        include_code=True,
    )

    if not result:
        logger.error("No results from interconnector_flow_network_regions_query with {}".format(time_series))
        return None

    return result


def demand_week(
    time_series: TimeSeries,
    network_region_code: Optional[str],
    networks_query: Optional[List[NetworkSchema]] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    query = network_demand_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if len(row) < 1:
        logger.error("No results from network_demand_query with {}".format(time_series))
        return None

    demand = [DataQueryResult(interval=i[0], result=i[2], group_by="demand" if len(i) > 1 else None) for i in row]

    result = stats_factory(
        demand,
        # code=network_region_code or network.code,
        network=time_series.network,
        period=human_to_period("7d"),
        interval=human_to_interval("5m"),
        units=get_unit("demand"),
        region=network_region_code,
    )

    if not result:
        logger.error("No results from network_demand_query with {}".format(time_series))
        return None

    return result


def power_week(
    time_series: TimeSeries,
    network_region_code: str = None,
    networks_query: Optional[List[NetworkSchema]] = None,
    include_capacities: bool = False,
    include_code: Optional[bool] = True,
) -> Optional[OpennemDataSet]:
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

    if len(stats) < 1:
        logger.error("No results from power week query with {}".format(time_series))
        return None

    result = stats_factory(
        stats,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=time_series.interval,
        period=time_series.period,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
        include_code=include_code,
    )

    if not result:
        logger.error("No results from power week status factory with {}".format(time_series))
        return None

    if include_capacities and network_region_code:
        region_fueltech_capacities = get_facility_capacities(time_series.network, network_region_code)

        for ft in result.data:
            if ft.fuel_tech in region_fueltech_capacities:
                ft.x_capacity_at_present = region_fueltech_capacities[ft.fuel_tech]

    # price

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
        period=time_series.period,
        include_code=include_code,
    )

    result.append_set(stats_market_value)

    # rooftop solar

    time_series_rooftop = time_series.copy()
    time_series_rooftop.interval = human_to_interval("30m")

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
        period=time_series.period,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
        include_code=include_code,
        cast_nulls=False,
    )

    # rooftop forecast
    rooftop_forecast = None

    if rooftop and rooftop.data and len(rooftop.data) > 0:
        time_series_rooftop_forecast = time_series_rooftop.copy()
        time_series_rooftop_forecast.start = rooftop.data[0].history.last
        time_series_rooftop_forecast.forecast = True

        query = power_network_rooftop_query(
            time_series=time_series_rooftop_forecast,
            networks_query=networks_query,
            network_region=network_region_code,
            forecast=True,
        )

        with engine.connect() as c:
            logger.debug(query)
            row = list(c.execute(query))

        rooftop_forecast_power = [
            DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in row
        ]

        rooftop_forecast = stats_factory(
            rooftop_forecast_power,
            # code=network_region_code or network.code,
            network=time_series.network,
            interval=human_to_interval("30m"),
            period=time_series.period,
            units=get_unit("power"),
            region=network_region_code,
            fueltech_group=True,
            include_code=include_code,
            cast_nulls=False,
        )

    if rooftop and rooftop_forecast:
        if (
            hasattr(rooftop, "data")
            and len(rooftop.data) > 0
            and rooftop_forecast.data
            and len(rooftop_forecast.data) > 0
        ):
            rooftop.data[0].forecast = rooftop_forecast.data[0].history
    else:
        logger.error("No rooftop or rooftop forecast")

    result.append_set(rooftop)

    return result


def demand_network_region_daily(
    time_series: TimeSeries,
    network: NetworkSchema,
    network_region_code: str | None = None,
) -> OpennemDataSet | None:
    """Gets demand market_value and energy for a network -> network_region"""
    engine = get_database_engine()

    query = demand_network_region_query(
        time_series=time_series,
        network_region=network_region_code,
        network=network,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    results_energy = [DataQueryResult(interval=i[0], group_by=i[2], result=i[3] if len(i) > 1 else None) for i in row]

    results_market_value = [
        DataQueryResult(interval=i[0], group_by=i[2], result=i[4] if len(i) > 1 else None) for i in row
    ]

    if len(results_energy) < 1:
        logger.error("No results from query: {}".format(query))
        return None

    # demand based values for VWP
    stats = stats_factory(
        stats=results_energy,
        units=get_unit("demand.energy_giga"),
        network=time_series.network,
        fueltech_group=False,
        interval=time_series.interval,
        # region=network_region_code,
        period=time_series.period,
        localize=True,
    )

    if not stats:
        raise Exception(f"Not stats for demand_network_region_daily: {network_region_code}")

    stats_market_value = stats_factory(
        stats=results_market_value,
        units=get_unit("demand.market_value"),
        network=time_series.network,
        fueltech_group=False,
        interval=time_series.interval,
        # region=network_region_code,
        period=time_series.period,
        code=time_series.network.code.lower(),
        localize=True,
    )

    if stats_market_value:
        stats.append_set(stats_market_value)

    return stats


def energy_fueltech_daily(
    time_series: TimeSeries,
    network_region_code: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> Optional[OpennemDataSet]:
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

    results_market_value = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None) for i in row
    ]

    results_emissions = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None) for i in row
    ]

    if len(results_energy) < 1:
        logger.error("No results from query: {}".format(query))
        return None

    stats = stats_factory(
        stats=results_energy,
        units=units,
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        period=time_series.period,
        localize=True,
        # code=network.code.lower(),
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
        period=time_series.period,
        code=time_series.network.code.lower(),
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
        period=time_series.period,
        code=time_series.network.code.lower(),
        localize=True,
    )

    stats.append_set(stats_emissions)

    return stats


def energy_interconnector_flows_and_emissions(
    time_series: TimeSeries,
    network_region_code: str,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()
    period: TimePeriod = human_to_period("1Y")
    unit_energy = get_unit("energy_giga")
    unit_emissions = get_unit("emissions")

    query = energy_network_interconnector_emissions_query(
        time_series=time_series,
        network_region=network_region_code,
        networks_query=networks_query,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if len(row) < 1:
        return None

    imports = [DataQueryResult(interval=i[0], group_by="imports", result=i[1]) for i in row]

    exports = [DataQueryResult(interval=i[0], group_by="exports", result=i[2]) for i in row]

    import_emissions = [DataQueryResult(interval=i[0], group_by="imports", result=i[3]) for i in row]
    export_emissions = [DataQueryResult(interval=i[0], group_by="exports", result=i[4]) for i in row]

    import_mv = [DataQueryResult(interval=i[0], group_by="imports", result=i[5]) for i in row]
    export_mv = [DataQueryResult(interval=i[0], group_by="exports", result=i[6]) for i in row]

    result = stats_factory(
        imports,
        network=time_series.network,
        period=period,
        interval=time_series.interval,
        units=unit_energy,
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        raise Exception("No results from flow controller")

    result_exports = stats_factory(
        exports,
        network=time_series.network,
        period=period,
        interval=time_series.interval,
        units=unit_energy,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    result_import_emissions = stats_factory(
        import_emissions,
        network=time_series.network,
        period=period,
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
        period=period,
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
        period=period,
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
        period=period,
        interval=time_series.interval,
        units=get_unit("market_value"),
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_export_mv)

    return result
