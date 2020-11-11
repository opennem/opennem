from typing import List, Optional

from opennem.api.export.queries import (
    energy_network_fueltech_query,
    power_network_fueltech_query,
    price_network_query,
)
from opennem.api.stats.controllers import get_scada_range, stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval, human_to_period
from opennem.api.weather.queries import (
    observation_query,
    observation_query_all,
)
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimePeriod


def weather_daily(
    network_code: str,
    station_code: str,
    year: Optional[int] = None,
    unit_name: str = "temperature_mean",
    period_human: str = None,
    include_min_max: bool = True,
):
    station_codes = []

    if station_code:
        station_codes = [station_code]

    engine = get_database_engine()
    interval = human_to_interval("1d")
    network = network_from_network_code(network_code)
    units = get_unit(unit_name)
    scada_range = get_scada_range(network=network)

    if year:
        query = observation_query(
            station_codes=station_codes,
            interval=interval,
            network=network,
            scada_range=scada_range,
            year=year,
        )
    elif period_human:
        interval = human_to_interval("{}m".format(network.interval_size))
        period = human_to_period("7d")

        query = observation_query(
            station_codes=station_codes,
            interval=interval,
            network=network,
            scada_range=scada_range,
            period=period,
        )
    else:
        interval = human_to_interval("1M")

        query = observation_query_all(
            station_codes=station_codes,
            scada_range=scada_range,
            network=network,
        )

    with engine.connect() as c:
        row = list(c.execute(query))

    temp_avg = [
        DataQueryResult(
            interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None
        )
        for i in row
    ]

    temp_min = [
        DataQueryResult(
            interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None
        )
        for i in row
    ]

    temp_max = [
        DataQueryResult(
            interval=i[0], group_by=i[1], result=i[4] if len(i) > 1 else None
        )
        for i in row
    ]

    if len(temp_avg) < 1:
        raise Exception("No results from query: {}".format(query))

    stats = stats_factory(
        stats=temp_avg,
        units=units,
        network=network,
        interval=interval,
        code="bom",
        group_field="temperature",
    )

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


def power_week(
    network_code: str = "WEM",
    network_region_code: str = None,
    networks: Optional[List[NetworkSchema]] = None,
) -> OpennemDataSet:
    engine = get_database_engine()

    network = network_from_network_code(network_code)
    interval = human_to_interval("{}m".format(network.interval_size))
    period = human_to_period("7d")
    units = get_unit("power")
    network_region = None

    query = power_network_fueltech_query(
        network=network,
        networks=networks,
        period=period,
        interval=interval,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        row = list(c.execute(query))

    stats = [
        DataQueryResult(
            interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None
        )
        for i in row
    ]

    if len(stats) < 1:
        raise Exception("No results from query: {}".format(query))

    result = stats_factory(
        stats,
        code=network_region_code or network.code,
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
        networks=networks,
        period=period,
        interval=interval,
        network_region=network_region_code,
    )

    with engine.connect() as c:
        row = list(c.execute(query))

    stats_price = [
        DataQueryResult(
            interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None
        )
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
    interval_size: str = "1d",
    networks: Optional[List[NetworkSchema]] = None,
) -> OpennemDataSet:
    engine = get_database_engine()
    period: TimePeriod = human_to_period("1Y")
    interval = human_to_interval(interval_size)
    units = get_unit("energy_giga")

    query = energy_network_fueltech_query(
        year=year,
        network=network,
        network_region=network_region_code,
        networks=networks,
    )

    with engine.connect() as c:
        row = list(c.execute(query))

    results_energy = [
        DataQueryResult(
            interval=i[0], group_by=i[1], result=i[2] if len(i) > 1 else None
        )
        for i in row
    ]

    results_market_value = [
        DataQueryResult(
            interval=i[0], group_by=i[1], result=i[3] if len(i) > 1 else None
        )
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
        region=network.code.lower(),
        period=period,
        code=network.code.lower(),
    )

    stats_market_value = stats_factory(
        stats=results_market_value,
        units=get_unit("market_value"),
        network=network,
        fueltech_group=True,
        interval=interval,
        region=network.code.lower(),
        period=period,
        code=network.code.lower(),
    )

    stats.append_set(stats_market_value)

    return stats

