import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound

from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.loader import load_data
from opennem.core.normalizers import (
    clean_capacity,
    name_normalizer,
    normalize_duid,
    station_name_cleaner,
)
from opennem.core.station_duid_map import (
    facility_has_station_remap,
    facility_map_station,
)
from opennem.db import db_connect
from opennem.db.models.opennem import Facility, Station
from opennem.importer.compat import (
    map_compat_facility_state,
    map_compat_fueltech,
    map_compat_network_region,
)

logger = logging.getLogger(__name__)


def load_opennem_facilities():
    station_fixture = load_data("facility_registry.json", from_fixture=True)

    stations = [{"station_code": k, **v} for k, v in station_fixture.items()]

    engine = db_connect()
    session = sessionmaker(bind=engine)
    s = session()

    for station_data in stations:
        station = None

        facilities = [
            {"code": k, **v} for k, v in station_data["duid_data"].items()
        ]

        # update facilities
        for facility_data in facilities:
            facility_duid = facility_data["code"]
            station_name = station_name_cleaner(station_data["display_name"])
            # station_code = normalize_duid(station_data["station_code"])
            station_code = facility_map_station(
                facility_duid, normalize_duid(station_data["station_code"])
            )
            station_state = map_compat_facility_state(
                station_data["status"]["state"]
            )
            station_network = (
                "WEM" if station_data["location"]["state"] == "WA" else "NEM"
            )

            station = (
                s.query(Station)
                .filter(Station.network_code == station_code)
                .one_or_none()
            )

            if not station:
                station = Station(
                    network_id=station_network,
                    code=station_code,
                    network_code=station_code,
                    name=station_name,
                    network_name=station_data["display_name"],
                    created_by="opennem.load_facilities",
                )
                logger.info(
                    "Created station: {} {} ".format(
                        station_name, station_code
                    )
                )

                s.add(station)
                s.commit()

            facility_status = station_state

            # Network region
            facility_network_region = map_compat_network_region(
                station_data["region_id"]
            )

            # Fueltech
            facility_fueltech = None

            if "fuel_tech" in facility_data and facility_data["fuel_tech"]:
                facility_fueltech = map_compat_fueltech(
                    facility_data["fuel_tech"]
                )

            # Capacity
            facility_capacity = None

            if (
                "registered_capacity" in facility_data
                and facility_data["registered_capacity"]
            ):
                facility_capacity = clean_capacity(
                    facility_data["registered_capacity"]
                )

            facility = None

            try:
                facility = (
                    s.query(Facility)
                    .filter(Facility.network_code == facility_duid)
                    .one_or_none()
                )
            except MultipleResultsFound:
                logger.error(
                    "Multiple facilities found for duid {}".format(
                        facility_duid
                    )
                )

                # facility = (
                #     s.query(Facility)
                #     .filter(Facility.network_code == facility_duid)
                #     .first()
                # )
                continue

            if not facility:
                facility = Facility(
                    code=facility_duid,
                    network_code=facility_duid,
                    network_region=facility_network_region,
                    created_by="opennem.load_facilities",
                )

                logger.info(
                    "Created facility: {} {} to station {} ".format(
                        facility_duid, facility_fueltech, station_code
                    )
                )

            if not facility.unit_id:
                facility.unit_id = 1
                facility.unit_number = 1

            if facility_capacity and not facility.unit_capacity:
                facility.unit_capacity = facility_capacity

            if facility_capacity and not facility.capacity_registered:
                facility.capacity_registered = facility_capacity

            if facility_fueltech and not facility.fueltech_id:
                facility.fueltech_id = facility_fueltech

            if not facility.status_id:
                facility.status_id = facility_status

            if not facility.station:
                facility.station = station

            s.add(facility)
            s.commit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    load_opennem_facilities()
