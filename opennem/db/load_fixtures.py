import csv
import json
import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.core.normalizers import station_name_cleaner
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
            print("Have {}".format(ft.code))


def load_facilitystatus():
    fixture = load_fixture("facility_status.json")

    s = session()

    for status in fixture:
        ft = FacilityStatus(code=status["code"], label=status["label"])

        try:
            s.add(ft)
            s.commit()
        except Exception:
            print("Have {}".format(ft.code))


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
                print("Have {}".format(station.code))


def parse_facilities_json():
    facilities = load_fixture("facility_registry.json")

    wa_facilities = [
        {"name": k, **v}
        for k, v in facilities.items()
        if v["location"]["state"] == "WA"
    ]

    nem_facilities = [
        {"name": k, **v}
        for k, v in facilities.items()
        if v["location"]["state"] != "WA"
    ]

    s = session()

    for facility in wa_facilities:
        station = None

        station = (
            s.query(WemStation)
            .filter(WemStation.code == facility["station_id"])
            .one_or_none()
        )

        if not station:
            print("Station not found: {}".format(facility["station_id"]))
            station = WemStation(
                code=facility["station_id"],
                name=station_name_cleaner(facility["display_name"]),
                state=facility["location"]["state"],
                postcode=facility["location"]["postcode"],
                geom="SRID=4326;POINT({} {})".format(
                    facility["location"]["latitude"],
                    facility["location"]["longitude"],
                ),
            )
            s.add(station)
            s.commit()

        for duid, v in facility["duid_data"].items():

            db_facility = (
                s.query(WemFacility)
                .filter(WemFacility.code == duid)
                .one_or_none()
            )

            if not db_facility:
                print("Could not find facility {} in database".format(duid))
                continue

            db_facility.fueltech_id = fueltech_map(v["fuel_tech"])
            db_facility.station = station
            s.add(db_facility)
            s.commit()

    for facility in nem_facilities:
        station = None

        station = (
            s.query(NemStation)
            .filter(NemStation.code == facility["station_id"])
            .one_or_none()
        )

        if not station:
            first_facility_duid = list(facility["duid_data"].keys()).pop()

            print("Looking up {}".format(first_facility_duid))

            station_first_facility = (
                s.query(NemFacility)
                .filter(NemFacility.code == first_facility_duid)
                .filter(NemFacility.nameplate_capacity != None)
                .first()
            )

            if station_first_facility:
                station = station_first_facility.station

        if not station:
            print("Station not found: {}".format(facility["station_id"]))
            station = NemStation(code=facility["station_id"],)

        station.name_clean = station_name_cleaner(facility["display_name"])
        station.state = facility["location"]["state"]
        station.postcode = facility["location"]["postcode"]

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

        for duid, v in facility["duid_data"].items():

            db_facility = (
                s.query(NemFacility)
                .filter(NemFacility.code == duid)
                .filter(NemFacility.nameplate_capacity != None)
                .first()
            )

            if not db_facility:
                print("Could not find facility {} in database".format(duid))
                continue

            if "fuel_tech" in v:
                db_facility.fueltech_id = fueltech_map(v["fuel_tech"])

            db_facility.station = station
            s.add(db_facility)
            s.commit()


if __name__ == "__main__":
    load_fueltechs()
    load_facilitystatus()
    load_bom_stations()
    # parse_facilities_json()
