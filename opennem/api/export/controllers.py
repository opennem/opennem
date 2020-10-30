from typing import Optional

from opennem.api.export.queries import (
    energy_network_fueltech_daily_query,
    market_value_daily_query,
    power_network_fueltech_query,
    wem_market_value_all_query,
)
from opennem.api.stats.controllers import get_scada_range, stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval, human_to_period
from opennem.api.weather.queries import observation_query
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import get_database_engine
from opennem.schema.time import TimePeriod


def weather_daily(year: int, network_code: str, station_code: str):
    station_codes = []

    if station_code:
        station_codes = [station_code]

    engine = get_database_engine()
    interval = human_to_interval("1d")
    network = network_from_network_code(network_code)
    units = get_unit("temperature_mean")
    scada_range = get_scada_range(network=network)

    query = observation_query(
        station_codes=station_codes,
        interval=interval,
        network=network,
        scada_range=scada_range,
        year=year,
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

    stats.data += stats_factory(
        stats=temp_min,
        units=get_unit("temprature_min"),
        network=network,
        interval=interval,
        code="bom",
        group_field="temperature",
    ).data

    stats.data += stats_factory(
        stats=temp_max,
        units=get_unit("temprature_max"),
        network=network,
        interval=interval,
        code="bom",
        group_field="temperature",
    ).data

    return stats


def power_week(network_code: str = "WEM"):
    engine = get_database_engine()

    network = network_from_network_code(network_code)
    interval = human_to_interval("{}m".format(network.interval_size))
    period = human_to_period("7d")
    units = get_unit("power")
    network_region = None

    query = power_network_fueltech_query(
        network=network, period=period, interval=interval
    )

    # print(query)

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
        code=network.code,
        network=network,
        interval=interval,
        period=period,
        units=units,
        region=network_region,
        fueltech_group=True,
    )

    return result


def energy_fueltech_daily(
    year: int,
    network_code: str = "WEM",
    network_region_code: Optional[str] = None,
) -> OpennemDataSet:
    network = network_from_network_code(network_code)
    engine = get_database_engine()
    period: TimePeriod = human_to_period("1Y")
    network = network_from_network_code(network_code)
    interval = human_to_interval("1d")
    units = get_unit("energy_giga")

    query = energy_network_fueltech_daily_query(
        year=year,
        interval=interval,
        network=network,
        network_region=network_region_code,
    )

    # print(query)

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

    if stats_market_value:
        stats.data += stats_market_value.data

    return stats


def market_value_year(year: int, network_code: str = "WEM"):
    network = network_from_network_code(network_code)
    engine = get_database_engine()

    units = get_unit("market_value")
    interval = human_to_interval("1d")

    query = market_value_daily_query(network=network, year=year)

    with engine.connect() as c:
        row = list(c.execute(query))

    results = [
        DataQueryResult(
            interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None
        )
        for i in row
    ]

    if len(results) < 1:
        raise Exception("No results from query: {}".format(query))

    stats = stats_factory(
        stats=results,
        units=units,
        network=network,
        fueltech_group=True,
        interval=interval,
        region=network.code.lower(),
        code=network.code.lower(),
    )

    return stats


def market_value_all(network_code: str = "WEM"):
    network = network_from_network_code(network_code)
    engine = get_database_engine()

    query = wem_market_value_all_query(network_code="WEM")
    units = get_unit("market_value")
    interval = human_to_interval("1M")

    with engine.connect() as c:
        row = list(c.execute(query))

    results = [
        DataQueryResult(
            interval=i[0], result=i[1], group_by=i[2] if len(i) > 1 else None
        )
        for i in row
    ]

    if len(results) < 1:
        raise Exception("No results from query: {}".format(query))

    stats = stats_factory(
        stats=results,
        units=units,
        network=network,
        fueltech_group=True,
        interval=interval,
        code=network.code,
    )

    return stats

