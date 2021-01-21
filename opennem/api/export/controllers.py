import logging
from typing import List, Optional

from opennem.api.export.queries import (
    country_stats_query,
    energy_network_fueltech_query,
    interconnector_power_flow,
    power_network_fueltech_query,
    price_network_query,
)
from opennem.api.stats.controllers import get_scada_range, stats_factory
from opennem.api.stats.schema import (
    DataQueryResult,
    OpennemDataSet,
    RegionFlowResult,
    ScadaDateRange,
)
from opennem.api.time import human_to_interval, human_to_period
from opennem.api.weather.queries import observation_query, observation_query_all
from opennem.core.flows import net_flows
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.stats import StatTypes
from opennem.schema.time import TimePeriod

logger = logging.getLogger(__name__)


def weather_daily(
    network_code: str,
    station_code: str,
    year: Optional[int] = None,
    unit_name: str = "temperature_mean",
    period_human: str = None,
    include_min_max: bool = True,
    date_range: Optional[ScadaDateRange] = None,
) -> Optional[OpennemDataSet]:
    station_codes = []

    if station_code:
        station_codes = [station_code]

    engine = get_database_engine()
    interval = human_to_interval("1d")
    network = network_from_network_code(network_code)
    units = get_unit(unit_name)

    if not date_range:
        date_range = get_scada_range(network=network)

    if not date_range:
        raise Exception("Require a scada range")

    if year:
        query = observation_query(
            station_codes=station_codes,
            interval=interval,
            network=network,
            scada_range=date_range,
            year=year,
        )
    elif period_human:
        interval = human_to_interval("30m")
        period = human_to_period(period_human)

        query = observation_query(
            station_codes=station_codes,
            interval=interval,
            network=network,
            scada_range=date_range,
            period=period,
        )
    else:
        interval = human_to_interval("1M")

        query = observation_query_all(
            station_codes=station_codes,
            scada_range=date_range,
            network=network,
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
        network=network,
        interval=interval,
        code="bom",
        group_field="temperature",
    )

    if not stats:
        return None

    if include_min_max:
        stats_min = stats_factory(
            stats=temp_min,
            units=get_unit("temperature_min"),
            network=network,
            interval=interval,
            code="bom",
            group_field="temperature",
        )

        stats_max = stats_factory(
            stats=temp_max,
            units=get_unit("temperature_max"),
            network=network,
            interval=interval,
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
    network: NetworkSchema,
    network_region_code: str,
    date_range: ScadaDateRange,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    query = interconnector_power_flow(
        network_region=network_region_code, date_range=date_range, network=network
    )

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
        network=network,
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
        network=network,
        period=human_to_period("7d"),
        interval=human_to_interval("5m"),
        units=get_unit("power"),
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    return result


def power_week(
    network_code: str = "WEM",
    network_region_code: str = None,
    period: Optional[TimePeriod] = None,
    date_range: Optional[ScadaDateRange] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()

    network = network_from_network_code(network_code)
    interval = human_to_interval("{}m".format(network.interval_size))
    units = get_unit("power")
    network_region = None

    query = power_network_fueltech_query(
        network=network,
        networks_query=networks_query,
        period=period,
        date_range=date_range,
        interval=interval,
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
        network=network,
        interval=interval,
        period=period,
        units=units,
        region=network_region,
        fueltech_group=True,
    )

    if not result:
        raise Exception("No results")

    # price

    query = price_network_query(
        network=network,
        networks_query=networks_query,
        period=period,
        date_range=date_range,
        interval=interval,
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
        code=network_region_code or network.code.lower(),
        units=get_unit("price_energy_mega"),
        network=network,
        interval=interval,
        region=network_region_code,
        period=period,
    )

    result.append_set(stats_market_value)

    return result


def energy_fueltech_daily(
    network: NetworkSchema,
    year: Optional[int] = None,
    network_region_code: Optional[str] = None,
    interval_size: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
    date_range: Optional[ScadaDateRange] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()
    period: TimePeriod = human_to_period("1Y")
    units = get_unit("energy_giga")

    interval = None

    if interval_size:
        interval = human_to_interval(interval_size)

    query = energy_network_fueltech_query(
        year=year,
        interval=interval,
        network=network,
        network_region=network_region_code,
        networks_query=networks_query,
        date_range=date_range,
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
        network=network,
        fueltech_group=True,
        interval=interval,
        region=network_region_code,
        period=period,
        # code=network.code.lower(),
    )

    if not stats:
        return None

    stats_market_value = stats_factory(
        stats=results_market_value,
        units=get_unit("market_value"),
        network=network,
        fueltech_group=True,
        interval=interval,
        region=network_region_code,
        period=period,
        code=network.code.lower(),
    )

    stats.append_set(stats_market_value)

    stats_emissions = stats_factory(
        stats=results_emissions,
        units=get_unit("emissions"),
        network=network,
        fueltech_group=True,
        interval=interval,
        region=network_region_code,
        period=period,
        code=network.code.lower(),
    )

    stats.append_set(stats_emissions)

    return stats


def energy_interconnector_region_daily(
    network: NetworkSchema,
    network_region_code: str,
    year: Optional[int] = None,
    interval_size: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
    date_range: Optional[ScadaDateRange] = None,
) -> Optional[OpennemDataSet]:
    engine = get_database_engine()
    period: TimePeriod = human_to_period("1Y")
    units = get_unit("energy_giga")

    interval = None

    if interval_size:
        interval = human_to_interval(interval_size)

    query = energy_network_fueltech_query(
        interconnector=True,
        year=year,
        interval=interval,
        network=network,
        network_region=network_region_code,
        networks_query=networks_query,
        date_range=date_range,
    )

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    if len(row) < 1:
        raise Exception("No results from query: {}".format(query))

    # stats_grouped = net_flows(network_region_code, stats)
    # stats_grouped = net_flows_energy(network_region_code, stats)

    imports = [
        DataQueryResult(interval=i[0], group_by="imports", result=i[1] if len(i) > 1 else None)
        for i in row
    ]
    exports = [
        DataQueryResult(interval=i[0], group_by="exports", result=i[2] if len(i) > 1 else None)
        for i in row
    ]

    result = stats_factory(
        imports,
        # code=network_region_code or network.code,
        network=network,
        period=period,
        interval=interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
    )

    # Bail early on no interconnector
    # don't error
    if not result:
        return result

    result_exports = stats_factory(
        exports,
        # code=network_region_code or network.code,
        network=network,
        period=period,
        interval=interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
    )

    result.append_set(result_exports)

    return result
