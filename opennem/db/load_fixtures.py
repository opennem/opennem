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
    station_name_cleaner,
)
from opennem.db import db_connect
from opennem.db.models.bom import BomStation
from opennem.db.models.opennem import (
    FacilityStatus,
    FuelTech,
    NemFacility,
    NemParticipant,
    NemStation,
    WemFacility,
    WemParticipant,
    WemStation,
)
from opennem.db.models.wem import metadata

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
        ft = FuelTech(code=fueltech)

        try:
            s.add(ft)
            s.commit()
        except Exception:
            logger.error("Have {}".format(ft.code))


def load_facilitystatus():
    fixture = load_fixture("facility_status.json")

    s = session()

    for status in fixture:
        ft = FacilityStatus(code=status["code"], label=status["label"])

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


def parse_facilities_json():
    facilities = load_fixture("facility_registry.json")

    wa_facilities = [
        {"station_code": k, **v}
        for k, v in facilities.items()
        if v["location"]["state"] == "WA"
    ]

    nem_facilities = [
        {"station_code": k, **v}
        for k, v in facilities.items()
        if v["location"]["state"] != "WA"
    ]

    s = session()

    for facility in wa_facilities:
        station = None

        station_name = station_name_cleaner(facility["display_name"])

        if facility_station_join_by_name(station_name):
            station = (
                s.query(WemStation)
                .filter(WemStation.name_clean == station_name)
                .one_or_none()
            )

        if not station:
            station = (
                s.query(WemStation)
                .filter(WemStation.code == facility["station_code"])
                .one_or_none()
            )

        if not station:

            station = WemStation(
                code=facility["station_code"],
                name=name_normalizer(facility["display_name"]),
                name_clean=station_name_cleaner(facility["display_name"]),
                state=facility["location"]["state"],
                postcode=facility["location"]["postcode"],
                geom="SRID=4326;POINT({} {})".format(
                    facility["location"]["latitude"],
                    facility["location"]["longitude"],
                ),
                created_by="fixture.registry",
            )
            s.add(station)
            s.commit()

            logger.info(
                "WEM Station not found so created with {} ({})".format(
                    station.name, station.code, station.id
                )
            )

        for duid, v in facility["duid_data"].items():
            created = False

            db_facility = (
                s.query(WemFacility)
                .filter(WemFacility.code == duid)
                .one_or_none()
            )

            if not db_facility:
                db_facility = WemFacility(
                    code=duid,
                    capacity_maximum=clean_capacity(
                        v["registered_capacity"]
                        if "registered_capacity" in v
                        else None
                    ),
                    name=name_normalizer(facility["display_name"]),
                    created_by="fixture.registry",
                )
                created = True

            db_facility.fueltech_id = fueltech_map(v["fuel_tech"])
            db_facility.region = facility["region_id"]

            db_facility.station = station
            db_facility.status_id = map_v3_states(facility["status"]["state"])

            logger.info(
                "{} facility {} ({}) to station {} ({})".format(
                    "Created" if created else "Updated",
                    facility["display_name"],
                    duid,
                    station.name,
                    station.id,
                )
            )

            s.add(db_facility)
            s.commit()

    for facility in nem_facilities:
        station = None
        created = False

        station_name = station_name_cleaner(facility["display_name"])

        if facility_station_join_by_name(station_name):
            station = (
                s.query(NemStation)
                .filter(NemStation.name_clean == station_name)
                .one_or_none()
            )

        if not station:
            station = (
                s.query(NemStation)
                .filter(NemStation.code == facility["station_code"])
                .one_or_none()
            )

        if not station:
            station = NemStation(
                code=facility["station_code"],
                name=name_normalizer(facility["display_name"]),
                name_clean=station_name,
                state=facility["location"]["state"],
                postcode=facility["location"]["postcode"],
                created_by="fixture.registry",
            )

            if (
                "latitude" in facility["location"]
                and facility["location"]["latitude"] is not None
            ):
                station.geom = "SRID=4326;POINT({} {})".format(
                    facility["location"]["latitude"],
                    facility["location"]["longitude"],
                )

            s.add(station)
            s.commit()

            logger.info(
                "NEM Station not found so created with {} ({})".format(
                    station.name, station.code, station.id
                )
            )

        for duid, v in facility["duid_data"].items():
            created = False

            db_facility = (
                s.query(NemFacility)
                .filter(NemFacility.code == duid)
                .filter(NemFacility.nameplate_capacity != None)
                .first()
            )

            if not db_facility:
                db_facility = NemFacility(
                    code=duid,
                    nameplate_capacity=clean_capacity(
                        v["registered_capacity"]
                        if "registered_capacity" in v
                        else None
                    ),
                    name=name_normalizer(facility["display_name"]),
                    name_clean=station_name_cleaner(facility["display_name"]),
                    created_by="fixture.registry",
                )
                created = True

            if "fuel_tech" in v:
                db_facility.fueltech_id = fueltech_map(v["fuel_tech"])

            db_facility.region = facility["region_id"]
            db_facility.station = station
            db_facility.status_id = map_v3_states(facility["status"]["state"])

            s.add(db_facility)
            s.commit()

            logger.info(
                "{} facility {} ({}) to station {} ({})".format(
                    "Created" if created else "Updated",
                    facility["display_name"],
                    duid,
                    station.name,
                    station.id,
                )
            )


if __name__ == "__main__":
    load_fueltechs()
    load_facilitystatus()
    load_bom_stations()
    # parse_facilities_json()
