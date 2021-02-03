import logging
from typing import List, Optional

from opennem.api.export.queries import (
    country_stats_query,
    energy_network_fueltech_query,
    energy_network_interconnector_emissions_query,
    interconnector_power_flow,
    network_demand_query,
    power_network_fueltech_query,
    power_network_rooftop_query,
    price_network_query,
    weather_observation_query,
)
from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import (
    DataQueryResult,
    OpennemDataSet,
    RegionFlowEmissionsResult,
    RegionFlowResult,
)
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.flows import net_flows, net_flows_emissions
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.schema.dates import TimeSeries
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.stats import StatTypes
from opennem.schema.time import TimePeriod

logger = logging.getLogger(__name__)


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

    temp_avg = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None)
        for i in row
    ]

    temp_min = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None)
        for i in row
    ]

    temp_max = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None)
        for i in row
    ]

    if len(temp_avg) < 1:
        logger.info("No results from query: {}".format(query))
        return None

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
        return None

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


def gov_stats_cpi() -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    query = country_stats_query(StatTypes.CPI)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    stats = [
        DataQueryResult(interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None)
        for i in row
    ]

    if len(stats) < 1:
        raise Exception("No results from query: {}".format(query))

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


def power_flows_week(
    time_series: TimeSeries,
    network_region_code: str,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    query = interconnector_power_flow(time_series=time_series, network_region=network_region_code)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if len(row) < 1:
        raise Exception("No results from query: {}".format(query))

    imports = [
        DataQueryResult(interval=i[0], result=i[2], group_by="imports" if len(i) > 1 else None)
        for i in row
    ]

    exports = [
        DataQueryResult(interval=i[0], result=i[3], group_by="exports" if len(i) > 1 else None)
        for i in row
    ]

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
        raise Exception("No results")

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
        raise Exception("No results from query: {}".format(query))

    demand = [
        DataQueryResult(interval=i[0], result=i[2], group_by="demand" if len(i) > 1 else None)
        for i in row
    ]

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
        raise Exception("No results")

    return result


def power_week(
    time_series: TimeSeries,
    network_region_code: str = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    query = power_network_fueltech_query(
        time_series=time_series,
        networks_query=networks_query,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    stats = [
        DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None)
        for i in row
    ]

    if len(stats) < 1:
        raise Exception("No results from query: {}".format(query))

    result = stats_factory(
        stats,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=time_series.interval,
        period=time_series.period,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        raise Exception("No results")

    # price

    time_series_price = time_series.copy()
    time_series_price.interval = human_to_interval("30m")

    query = price_network_query(
        time_series=time_series_price,
        networks_query=networks_query,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    stats_price = [
        DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None)
        for i in row
    ]

    stats_market_value = stats_factory(
        stats=stats_price,
        code=network_region_code or time_series.network.code.lower(),
        units=get_unit("price_energy_mega"),
        network=time_series.network,
        interval=human_to_interval("30m"),
        region=network_region_code,
        period=time_series.period,
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

    rooftop_power = [
        DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None)
        for i in row
    ]

    rooftop = stats_factory(
        rooftop_power,
        # code=network_region_code or network.code,
        network=time_series.network,
        interval=human_to_interval("30m"),
        period=time_series.period,
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
    )

    # rooftop forecast

    time_series_rooftop_forecast = time_series.copy()
    time_series_rooftop_forecast.interval = human_to_interval("30m")
    time_series_rooftop_forecast.forecast = True

    query = power_network_rooftop_query(
        time_series=time_series_rooftop,
        networks_query=networks_query,
        network_region=network_region_code,
        forecast=True,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    rooftop_forecast_power = [
        DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None)
        for i in row
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
    )

    if rooftop and rooftop_forecast:
        if (
            hasattr(rooftop, "data")
            and len(rooftop.data) > 0
            and rooftop_forecast.data
            and len(rooftop_forecast.data) > 0
        ):
            rooftop.data[0].forecast = rooftop_forecast.data[0].history

    result.append_set(rooftop)

    return result


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

    results_energy = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None)
        for i in row
    ]

    results_market_value = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None)
        for i in row
    ]

    results_emissions = [
        DataQueryResult(interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None)
        for i in row
    ]

    if len(results_energy) < 1:
        raise Exception("No results from query: {}".format(query))

    stats = stats_factory(
        stats=results_energy,
        units=units,
        network=time_series.network,
        fueltech_group=True,
        interval=time_series.interval,
        region=network_region_code,
        period=time_series.period,
        localize=False,
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
        localize=False,
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
        localize=False,
    )

    stats.append_set(stats_emissions)

    return stats


def energy_interconnector_region_daily(
    time_series: TimeSeries,
    network_region_code: str,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()
    period: TimePeriod = human_to_period("1Y")
    units = get_unit("energy_giga")

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

    stats = [
        RegionFlowResult(interval=i[0], flow_from=i[1], flow_to=i[2], generated=i[3]) for i in row
    ]

    stats_grouped = net_flows(network_region_code, stats, interval=time_series.interval)

    imports = stats_grouped["imports"]
    exports = stats_grouped["exports"]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
        period=period,
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
        # code=network_region_code or network.code,
        network=time_series.network,
        period=period,
        interval=time_series.interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_exports)

    return result


def energy_interconnector_emissions_region_daily(
    time_series: TimeSeries,
    network_region_code: str,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()
    period: TimePeriod = human_to_period("1Y")
    units = get_unit("emissions")

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

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=time_series.network,
        period=period,
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
        # code=network_region_code or network.code,
        network=time_series.network,
        period=period,
        interval=time_series.interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
        localize=False,
    )

    result.append_set(result_exports)

    return result
