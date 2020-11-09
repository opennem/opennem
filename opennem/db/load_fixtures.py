"""
    Loads database fixtures that are required.

"""

import logging
from datetime import datetime
from decimal import Decimal

from opennem.core.fueltechs import lookup_fueltech
from opennem.core.loader import load_data
from opennem.core.normalizers import normalize_duid, station_name_cleaner
from opennem.db import SessionLocal
from opennem.db.models.opennem import (
    BomStation,
    Facility,
    FacilityStatus,
    FuelTech,
    Network,
    NetworkRegion,
    Station,
)
from opennem.importer.compat import map_compat_facility_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opennem.fixtureloader")
logger.setLevel(logging.INFO)


def load_fueltechs():
    """
        Load the fueltechs fixture
    """
    fixture = load_data("fueltechs.json", from_fixture=True)

    s = SessionLocal()

    for ft in fixture:
        fueltech = s.query(FuelTech).filter_by(code=ft["code"]).one_or_none()

        if not fueltech:
            fueltech = FuelTech(code=ft["code"],)

        fueltech.label = ft["label"]
        fueltech.renewable = ft["renewable"]

        try:
            s.add(fueltech)
            s.commit()
        except Exception:
            logger.error("Have {}".format(fueltech.code))


def load_facilitystatus():
    """
        Load the facility status fixture
    """
    fixture = load_data("facility_status.json", from_fixture=True)

    s = SessionLocal()

    for status in fixture:
        facility_status = (
            s.query(FacilityStatus)
            .filter_by(code=status["code"])
            .one_or_none()
        )

        if not facility_status:
            facility_status = FacilityStatus(code=status["code"],)

        facility_status.label = status["label"]

        try:
            s.add(facility_status)
            s.commit()
        except Exception:
            logger.error("Have {}".format(facility_status.code))


def load_networks():
    """
        Load the networks fixture
    """
    fixture = load_data("networks.json", from_fixture=True)

    s = SessionLocal()

    for network in fixture:
        network_model = (
            s.query(Network).filter_by(code=network["code"]).one_or_none()
        )

        if not network_model:
            network_model = Network(code=network["code"])

        network_model.label = network["label"]
        network_model.country = network["country"]
        network_model.timezone = network["timezone"]
        network_model.timezone_database = network["timezone_database"]
        network_model.offset = network["offset"]
        network_model.interval_size = network["interval_size"]

        try:
            s.add(network_model)
            s.commit()
        except Exception:
            logger.error("Have {}".format(network_model.code))


def load_network_regions():
    """
        Load the network region fixture
    """
    fixture = load_data("network_regions.json", from_fixture=True)

    s = SessionLocal()

    for network_region in fixture:
        network_region_model = (
            s.query(NetworkRegion)
            .filter_by(code=network_region["code"])
            .one_or_none()
        )

        if not network_region_model:
            network_region_model = NetworkRegion(code=network_region["code"])

        network_region_model.network_id = network_region["network_id"]

        try:
            s.add(network_region_model)
            s.commit()
        except Exception:
            logger.error("Have {}".format(network_region_model.code))


"""
    BOM Fixtures
"""


def parse_date(date_str):
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.date()


def parse_fixed_line(line):
    """
        Parses a fixed-width CSV from the funky BOM format
    """
    return (
        str(line[:6]),
        str(line[8:11]).strip(),
        str(line[18:59]).strip(),
        parse_date(line[59:67]),
        Decimal(line[75:83]),
        Decimal(line[84:]),
    )


def load_bom_stations_csv():
    """
        Imports the BOM fixed-width stations format

        Made redundant with the new JSON
    """
    s = SessionLocal()

    station_csv = load_data("stations_db.txt", from_fixture=True)

    lines = station_csv.split("\n")

    for line in lines:
        code, state, name, registered, lng, lat = parse_fixed_line(line)

        station = s.query(BomStation).filter_by(code=code).one_or_none()

        if not station:
            station = BomStation(
                code=code, state=state, name=name, registered=registered,
            )

        station.geom = "SRID=4326;POINT({} {})".format(lat, lng)

        try:
            s.add(station)
            s.commit()
        except Exception:
            logger.error("Have {}".format(station.code))


def load_bom_stations_json():
    """
        Imports BOM stations into the database from bom_stations.json

        The json is obtained using scripts/bom_stations.py
    """
    session = SessionLocal()

    bom_stations = load_data("bom_stations.json", from_project=True)
    bom_capitals = load_data("bom_capitals.json", from_project=True)

    codes = []

    for bom_station in bom_stations:

        if not "code" in bom_station:
            logger.error("Invalida bom station ..")
            continue

        if bom_station["code"] in codes:
            continue

        codes.append(bom_station["code"])

        station = (
            session.query(BomStation)
            .filter_by(code=bom_station["code"])
            .one_or_none()
        )

        if not station:
            logger.info("New station: %s", bom_station["name"])

            station = BomStation(code=bom_station["code"],)

        station.name = bom_station["name_full"]
        station.name_alias = bom_station["name"]
        station.website_url = bom_station["url"]
        station.feed_url = bom_station["json_feed"]
        station.priority = 5
        station.state = bom_station["state"]
        station.altitude = bom_station["altitude"]

        if bom_station["code"] in bom_capitals:
            station.is_capital = True
            station.priority = 1

        station.geom = "SRID=4326;POINT({} {})".format(
            bom_station["lng"], bom_station["lat"]
        )

        session.add(station)

    session.commit()


def update_existing_geos():
    """
        Old method to update geos from existing facilities file on OpenNEM
    """

    station_fixture = load_data("facility_registry.json", from_fixture=True)

    stations = [{"station_code": k, **v} for k, v in station_fixture.items()]

    s = SessionLocal()

    for station_data in stations:
        station = None

        station_name = station_name_cleaner(station_data["display_name"])
        station_code = normalize_duid(station_data["station_code"])
        station_state = map_compat_facility_state(
            station_data["status"]["state"]
        )

        station = (
            s.query(Station)
            .filter(Station.network_code == station_code)
            .one_or_none()
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

        # update fueltechs
        for facility_data in facilities:
            facility_duid = facility_data["code"]
            facility_fueltech = lookup_fueltech(facility_data["fuel_tech"])

            facility = (
                s.query(Facility)
                .filter(Facility.network_code == facility_duid)
                .first()
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


def load_fixtures():
    load_fueltechs()
    load_facilitystatus()
    load_networks()
    load_network_regions()
    load_bom_stations_json()


if __name__ == "__main__":
    load_fixtures()
