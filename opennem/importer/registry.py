import json
import logging
from datetime import datetime
from typing import List

from opennem.core.facility.fueltechs import parse_facility_fueltech
from opennem.core.facilitystatus import parse_facility_status
from opennem.core.loader import load_data
from opennem.core.networks import network_from_network_region
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.importer.compat import (
    map_compat_facility_state,
    map_compat_fueltech,
    map_compat_network_region,
)
from opennem.schema.opennem import (
    FacilitySchema,
    LocationSchema,
    StationSchema,
)
from opennem.schema.stations import StationSet

logger = logging.getLogger("opennem.importer.registry")


def registry_to_station(registry_station: dict, _id: int) -> StationSchema:
    station = StationSchema(
        id=_id,
        code=registry_station.get("station_id", ""),
        name=registry_station.get("display_name", ""),
        network_name=registry_station.get("display_name", ""),
    )

    station.location = LocationSchema(
        state=registry_station.get("location", {}).get("state", None),
        geocode_by="opennem.registry",
        geocode_approved=True,
        lat=registry_station.get("location", {}).get("latitude", None),
        lng=registry_station.get("location", {}).get("longitude", None),
    )

    if "duid_data" not in registry_station:
        logger.info(
            "Registry: station has no duid data: {}".format(
                registry_station.get("display_name", "")
            )
        )
        return station

    for duid, registry_facility in registry_station["duid_data"].items():
        network_region = map_compat_network_region(
            registry_station.get("region_id", "")
        )

        facility = FacilitySchema(
            **{
                "code": duid,
                "created_by": "opennem.registry",
                "created_at": datetime.now(),
                "network": network_from_network_region(network_region),
                "network_region": network_region,
                "station_code": registry_station.get("station_id", ""),
                "dispatch_type": "GENERATOR",
                "status": parse_facility_status(
                    map_compat_facility_state(
                        registry_station.get("status", {}).get("state", "")
                    )
                ),
                "fueltech": parse_facility_fueltech(
                    map_compat_fueltech(
                        registry_facility.get("fuel_tech", None)
                    )
                ),
                "capacity_registered": registry_facility.get(
                    "registered_capacity", None
                ),
            }
        )
        station.facilities.append(facility)

    return station


def registry_to_stations(registry, start_id: int = 5000) -> StationSet:

    _id = start_id

    stations = StationSet()

    for station_code, station in registry.items():
        _station = registry_to_station(station, _id)

        if _station:
            station_existing = stations.get_code(_station.code)

            if station_existing:
                logger.info(
                    "Merging station {} into {}".format(
                        station_code, station_existing.code
                    )
                )
                station_existing.facilities += _station.facilities
                continue

            stations.add(_station)
            _id += 1

    return stations


def registry_import() -> StationSet:
    registry = load_data("facility_registry.json")

    on_registry = registry_to_stations(registry)

    return on_registry


def registry_export():
    stations = registry_import()

    with open("data/registry.json", "w") as fh:
        fh.write(stations.json(indent=4))

    logger.info("Wrote {} records".format(stations.length))


if __name__ == "__main__":
    registry_export()
