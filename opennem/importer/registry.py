import json
import logging

from opennem.core.facilitystatus import parse_facility_status
from opennem.core.loader import load_data
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.importer.compat import map_compat_facility_state

logger = logging.getLogger("opennem.importer.registry")


def map_station(registry_station):
    station = {
        "name": registry_station.get("display_name", ""),
        "code": registry_station.get("station_id", ""),
        "station_code": registry_station.get("station_id", ""),
        "lat": registry_station.get("location", {}).get("latitude", None),
        "lng": registry_station.get("location", {}).get("longitude", None),
        "facilities": [],
    }

    if "duid_data" not in registry_station:
        logger.info(
            "Registry: station has no duid data: {}".format(
                registry_station.get("display_name", "")
            )
        )
        return station

    for duid, registry_facility in registry_station["duid_data"].items():
        facility = {
            # "date_start": "1998-10-25T00:00:00",
            # "date_end": "2016-03-11T00:00:00",
            "code": duid,
            "network_region": registry_station.get("region_id", ""),
            "station_code": registry_station.get("station_id", ""),
            "dispatch_type": "GENERATOR",
            "status": parse_facility_status(
                map_compat_facility_state(
                    registry_station.get("status", {}).get("state", "")
                )
            ),
            "capacity_registered": registry_facility.get(
                "registered_capacity", None
            ),
        }
        station["facilities"].append(facility)

    return station


def map_registry(registry):

    _id = 5000

    registry_mapped = {}

    for station_code, station in registry.items():
        _station = map_station(station)
        _station = {"id": _id, **_station}

        registry_mapped[station_code] = _station

    return registry_mapped


def registry_import():
    registry = load_data("facility_registry.json")

    on_registry = map_registry(registry)

    return on_registry


def registry_export():
    nem_registry = registry_import()

    with open("data/registry.json", "w") as fh:
        json.dump(nem_registry, fh, indent=4, cls=OpenNEMJSONEncoder)

    logger.info("Wrote {} records".format(len(nem_registry.keys())))


if __name__ == "__main__":
    registry_export()
