from sqlalchemy.orm import sessionmaker

from opennem.api.export.queries import (
    market_value_year_query,
    wem_market_value_all_query,
)
from opennem.api.stats.controllers import get_scada_range, stats_factory
from opennem.api.stats.schema import DataQueryResult
from opennem.api.time import human_to_interval
from opennem.api.weather.queries import observation_query
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.db import db_connect, get_database_engine

engine = db_connect()
session = sessionmaker(bind=engine)


PERIOD_MAP = {
    "all": 0,
    # current year
    "year": "date_trunc('year', current_date))",
    # current month
    "month": "date_trunc('month', current_date))",
}


def bom_observation(station_id, region="wa"):
    __query = """
        SELECT
            observation_time,
            round(temp_air, 2) as value
        FROM bom_observation
        WHERE
            station_id = '{station_id}'
            AND observation_time > now() - interval '7 days'
        order by 1 desc
    """

    query = __query.format(station_id=station_id)

    json_object = {
        "id": f"{region}.temperature",
        "history": {
            "data": [],
            "interval": "30m",
            "last": None,
            "start": None,
        },
        "bom.station": station_id,
        "region": region,
        "type": "temperature",
        "units": "degreesC",
    }

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:

            if (
                json_object["history"]["start"] == None
                or row[0] < json_object["history"]["start"]
            ):
                json_object["history"]["start"] = row[0]

            if (
                json_object["history"]["last"] == None
                or row[0] > json_object["history"]["last"]
            ):
                json_object["history"]["last"] = row[0]

            json_object["history"]["data"].append(row[1])

    return json_object


def wem_price(region="wa"):
    __query = """
        with intervals as (
        select generate_series(
            date_trunc('hour', now()) - '7 day'::interval,
            date_trunc('hour', now()),
            '30 minutes'::interval
        ) as interval
        )

        select
            i.interval,
            round(bs.price, 2),
            case when bs.price is null then 0 else bs.price end as price_cast,
            round(bs.generation_total, 2)
        from intervals i
        left join balancing_summary bs on bs.trading_interval = interval
        where bs.network_id='WEM'
        order by i.interval desc
    """

    query = __query.format()

    json_object = {
        "id": f"{region}.price",
        "history": {
            "data": [],
            "interval": "30m",
            "last": None,
            "start": None,
        },
        "region": region,
        "type": "price",
        "units": "AUD/MWh",
    }

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:

            if (
                json_object["history"]["start"] == None
                or row[0] < json_object["history"]["start"]
            ):
                json_object["history"]["start"] = row[0]

            if (
                json_object["history"]["last"] == None
                or row[0] > json_object["history"]["last"]
            ):
                json_object["history"]["last"] = row[0]

            json_object["history"]["data"].append(row[1])

    return json_object


def wem_demand(region="wa"):
    __query = """
        with intervals as (
            select generate_series(
                date_trunc('hour', now()) - '7 day'::interval,
                date_trunc('hour', now()),
                '30 minutes'::interval
            ) as interval
        )

        select
            i.interval,
            round(wbs.price, 2),
            round(wbs.generation_total, 2)
        from intervals i
        left join balancing_summary wbs on wbs.trading_interval = interval
        where wbs.network_id='WEM'
        order by i.interval desc
    """

    query = __query.format()

    json_object = {
        "id": f"{region}.demand",
        "history": {
            "data": [],
            "interval": "30m",
            "last": None,
            "start": None,
        },
        "region": region,
        "type": "demand",
        "units": "MW",
    }

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:

            if (
                json_object["history"]["start"] == None
                or row[0] < json_object["history"]["start"]
            ):
                json_object["history"]["start"] = row[0]

            if (
                json_object["history"]["last"] == None
                or row[0] > json_object["history"]["last"]
            ):
                json_object["history"]["last"] = row[0]

            json_object["history"]["data"].append(row[2])

    return json_object


def wem_power_groups(intervals_per_hour=2):
    __query = """
        with intervals as (
            select generate_series(
                date_trunc('hour', now()) - '7 day'::interval,
                date_trunc('hour', now()),
                '30 minutes'::interval
            ) as interval
        )
        select
            i.interval,
            f.fueltech_id as fueltech,
            round(sum(fs.generated) * {intervals_per_hour}, 2) as val
        from intervals i
        left join facility_scada fs on i.interval = fs.trading_interval
        left join facility f on f.code = fs.facility_code
        where
            fs.network_id='WEM'
            and f.fueltech_id is not null
        group by 1, 2
        order by 2 asc, 1 desc
        """

    query = __query.format(intervals_per_hour=intervals_per_hour)

    json_envelope = []
    json_obj = None

    with engine.connect() as c:
        rows = c.execute(query)

        current_tech = None

        for row in rows:

            if current_tech != row[1]:

                if json_obj is not None:
                    json_envelope.append(json_obj)

                current_tech = row[1]

                json_obj = {
                    "id": f"wem.fuel_tech.{current_tech}.power",
                    "fuel_tech": current_tech,
                    "region": "wa",
                    "network": "wem",
                    "type": "power",
                    "units": "MWh",
                    "history": {
                        "interval": "30m",
                        "start": None,
                        "last": None,
                        "data": [],
                    },
                }

            if (
                json_obj["history"]["start"] == None
                or row[0] < json_obj["history"]["start"]
            ):
                json_obj["history"]["start"] = row[0]

            if (
                json_obj["history"]["last"] == None
                or row[0] > json_obj["history"]["last"]
            ):
                json_obj["history"]["last"] = row[0]

            value = row[2]

            json_obj["history"]["data"].append(value)

    json_envelope.append(json_obj)

    return json_envelope


def wem_energy_year(year="2020"):
    """
        WEM energy year

    """
    __query = """
        select
            date_trunc('day', fs.trading_interval) AS trading_day,
            round(max(fs.eoi_quantity), 2) as energy_output,
            f.fueltech_id
        from facility_scada fs
        left join facility f on fs.facility_code = f.code
        where
            f.fueltech_id is not null
            and f.network_id = 'WEM'
            and extract('year' from fs.trading_interval) = {year}
        group by 1, f.fueltech_id
        order by 1 desc, 2 asc
        """

    query = __query.format(year=year)

    json_envelope = {}

    with engine.connect() as c:
        rows = c.execute(query)

        current_tech = None

        for row in rows:

            current_tech = row[2]

            if current_tech not in json_envelope.keys():
                json_envelope[current_tech] = {
                    "id": f"wem.fuel_tech.{current_tech}.energy",
                    "fuel_tech": current_tech,
                    "region": "wa",
                    "type": "energy",
                    "units": "MWh",
                    "history": {
                        "interval": "1d",
                        "start": None,
                        "last": None,
                        "data": [],
                    },
                }

            if (
                json_envelope[current_tech]["history"]["start"] == None
                or row[0] < json_envelope[current_tech]["history"]["start"]
            ):
                json_envelope[current_tech]["history"]["start"] = row[0]

            if (
                json_envelope[current_tech]["history"]["last"] == None
                or row[0] > json_envelope[current_tech]["history"]["last"]
            ):
                json_envelope[current_tech]["history"]["last"] = row[0]

            json_envelope[current_tech]["history"]["data"].append(row[1])

    return [json_envelope[i] for i in json_envelope.keys()]


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


def market_value_year(year: int, network_code: str = "WEM"):
    network = network_from_network_code(network_code)
    engine = get_database_engine()

    query = market_value_year_query(network_code="WEM", year=year,)
    units = get_unit("market_value")
    interval = human_to_interval("1d")

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

