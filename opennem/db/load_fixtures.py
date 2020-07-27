import csv
import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.facilitystatus import map_v3_states
from opennem.core.normalizers import (
    clean_capacity,
    name_normalizer,
    normalize_duid,
    station_name_cleaner,
)
from opennem.db import db_connect
from opennem.db.models.bom import BomStation
from opennem.db.models.opennem import (
    Facility,
    FacilityStatus,
    FuelTech,
    Network,
    Participant,
    Station,
)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")

engine = db_connect()
session = sessionmaker(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opennem.fixtureloader")
logger.setLevel(logging.INFO)


def fueltech_map(fueltech):
    if fueltech == "brown_coal":
        return "coal_brown"

    if fueltech == "black_coal":
        return "coal_black"

    if fueltech == "solar":
        return "solar_utility"

    if fueltech == "biomass":
        return "bioenergy_biomass"

    return fueltech


def load_fixture(fixture_name):
    fixture_path = os.path.join(FIXTURE_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture


def load_fueltechs():
    fixture = load_fixture("fueltechs.json")

    s = session()

    for fueltech in fixture:
        ft = FuelTech(
            created_by="opennem.fixture",
            code=fueltech["code"],
            label=fueltech["label"],
            renewable=fueltech["renewable"],
        )

        try:
            s.add(ft)
            s.commit()
        except Exception:
            logger.error("Have {}".format(ft.code))


def load_facilitystatus():
    fixture = load_fixture("facility_status.json")

    s = session()

    for status in fixture:
        ft = FacilityStatus(
            created_by="opennem.fixture",
            code=status["code"],
            label=status["label"],
        )

        try:
            s.add(ft)
            s.commit()
        except Exception:
            logger.error("Have {}".format(ft.code))


def load_networks():
    fixture = load_fixture("networks.json")

    s = session()

    for network in fixture:
        ft = Network(
            created_by="opennem.fixture",
            code=network["code"],
            label=network["label"],
            country=network["country"],
        )

        try:
            s.add(ft)
            s.commit()
        except Exception:
            logger.error("Have {}".format(ft.code))


def parse_date(date_str):
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.date()


def parse_fixed_line(line):
    return (
        str(line[:6]),
        str(line[8:11]).strip(),
        str(line[18:59]).strip(),
        parse_date(line[59:67]),
        Decimal(line[75:83]),
        Decimal(line[84:]),
    )


def load_bom_stations():
    s = session()

    with open(os.path.join(FIXTURE_PATH, "stations_db.txt")) as fh:
        lines = fh.readlines()
        for line in lines:
            code, state, name, registered, lat, lng = parse_fixed_line(line)
            station = BomStation(
                code=code,
                state=state,
                name=name,
                registered=registered,
                lat=lat,
                lng=lng,
            )

            try:
                s.add(station)
                s.commit()
            except Exception:
                logger.error("Have {}".format(station.code))


def update_existing_geos():
    station_fixture = load_fixture("facility_registry.json")

    stations = [{"station_code": k, **v} for k, v in station_fixture.items()]

    s = session()

    for station_data in stations:
        station = None

        station_name = station_name_cleaner(station_data["display_name"])
        station_code = normalize_duid(station_data["station_code"])
        station_state = map_v3_states(station_data["status"]["state"])

        station = (
            s.query(Station).filter(Station.code == station_code).one_or_none()
        )

        if not station:
            logger.info("Could not find station {}".format(station_code))
            continue

        if (
            "location" in station_data
            and "latitude" in station_data["location"]
            and station_data["location"]["latitude"]
        ):
            station.geom = (
                "SRID=4326;POINT({} {})".format(
                    station_data["location"]["latitude"],
                    station_data["location"]["longitude"],
                ),
            )
            station.geocode_processed_at = datetime.now()
            station.geocode_by = "opennem"
            station.geocode_approved = True

            station.updated_by = "fixture.registry"

        s.add(station)

        logger.info(
            "Updated station geo location {} ({})".format(
                station.code, station.name,
            )
        )

        facilities = [
            {"code": k, **v} for k, v in stations[0]["duid_data"].items()
        ]

        for facility_data in facilities:
            facility_duid = facility_data["code"]
            facility_fueltech = fueltech_map(facility_data["fuel_tech"])

            facility = (
                s.query(Facility)
                .filter(Facility.code == facility_duid)
                .one_or_none()
            )

            if not facility:
                logger.error(
                    "Could not find existing facility {} for station {}".format(
                        facility_duid, station_code
                    )
                )
                continue

            if not facility.fueltech_id:
                facility.fueltech_id = facility_fueltech

            if facility.fueltech_id != facility_fueltech:
                logger.error(
                    "Fueltech mismatch for {}. Old is {} and new is {}".format(
                        station_code, facility_fueltech, station.fueltech_id
                    )
                )

            s.add(facility)

        s.commit()


if __name__ == "__main__":
    load_fueltechs()
    load_facilitystatus()
    load_networks()
    load_bom_stations()
