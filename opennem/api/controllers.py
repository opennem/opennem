import decimal
import json
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import FuelTech
from opennem.db.models.wem import WemFacility, metadata

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
            temp_air as value
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
            wbs.price,
            case when wbs.price is null then 0 else wbs.price end as price_cast,
            wbs.generation_total
        from intervals i
        left join wem_balancing_summary wbs on wbs.trading_interval = interval
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
            wbs.price,
            wbs.generation_total
        from intervals i
        left join wem_balancing_summary wbs on wbs.trading_interval = interval
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
            coalesce(wf.fueltech_id, 'Unknown') as fueltech,
            sum(wfs.generated) * {intervals_per_hour} as val
        from intervals i
        left join wem_facility_scada wfs on i.interval = wfs.trading_interval
        left join wem_facility wf on wf.code = wfs.facility_id
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
            date_trunc('day', wfs.trading_interval) AS trading_day,
            max(wfs.eoi_quantity) as energy_output,
            wf.fueltech_id
        from wem_facility_scada wfs
        left join wem_facility wf on wfs.facility_id = wf.code
        where
            wf.fueltech_id is not null
            and extract('year' from wfs.trading_interval) = {year}
        group by 1, wf.fueltech_id
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


def wem_market_value_year(year="2020"):
    """
        WEM market value year

    """
    __query = """
        select
            date_trunc('day', wfs.trading_interval) AS trading_day,
            sum(wfs.eoi_quantity * wbs.price) as energy_interval,
            wf.fueltech_id
        from wem_facility_scada wfs
        left join wem_facility wf on wfs.facility_id = wf.code
        join wem_balancing_summary wbs on wfs.trading_interval = wbs.trading_interval
        where
            wf.fueltech_id is not null
            and extract('year' from wfs.trading_interval) = {year}
        group by 1, wf.fueltech_id
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
                    "id": f"wem.fuel_tech.{current_tech}.market_value",
                    "fuel_tech": current_tech,
                    "region": "wa",
                    "type": "market_value",
                    "units": "AUD",
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


def wem_energy_all():
    """
        WEM energy year

    """
    __query = """
        select
            date_trunc('month', wfs.trading_interval) AS trading_day,
            max(wfs.eoi_quantity) as energy_output,
            wf.fueltech_id
        from wem_facility_scada wfs
        left join wem_facility wf on wfs.facility_id = wf.code
        where
            wf.fueltech_id is not null
        group by 1, wf.fueltech_id
        order by 1 desc, 2 asc
        """

    query = __query.format()

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
                        "interval": "1M",
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


def wem_market_value_all():
    """
        WEM market value all

    """
    __query = """
        select
            date_trunc('month', wfs.trading_interval) AS trading_day,
            sum(wfs.eoi_quantity * wbs.price) as energy_interval,
            wf.fueltech_id
        from wem_facility_scada wfs
        left join wem_facility wf on wfs.facility_id = wf.code
        join wem_balancing_summary wbs on wfs.trading_interval = wbs.trading_interval
        where
            wf.fueltech_id is not null
        group by 1, wf.fueltech_id
        order by 1 desc, 2 asc
        """

    query = __query.format()

    json_envelope = {}

    with engine.connect() as c:
        rows = c.execute(query)

        current_tech = None

        for row in rows:

            current_tech = row[2]

            if current_tech not in json_envelope.keys():
                json_envelope[current_tech] = {
                    "id": f"wem.fuel_tech.{current_tech}.market_value",
                    "fuel_tech": current_tech,
                    "region": "wa",
                    "type": "market_value",
                    "units": "AUD",
                    "history": {
                        "interval": "1M",
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
