import json
from operator import attrgetter
from typing import Any, List

from opennem.core.loader import load_data
from opennem.core.normalizers import clean_capacity
from opennem.db.load_fixtures import load_fixture
from opennem.importer.compat import (
    map_compat_facility_state,
    map_compat_fueltech,
    map_compat_network_region,
)

from .schema import StationSchema


def sort_records(records: List[Any]) -> List[Any]:
    return sorted(records, key=attrgetter("network_region", "name", "duid"))


def load_registry() -> List[StationSchema]:
    """
        Loads the facility registry into a list of Station schema's
    """
    stations = load_data("facility_registry.json")

    records = []

    for station_id, station_record in stations.items():
        for duid, facility_record in station_record["duid_data"].items():

            status = map_compat_facility_state(
                station_record.get("status", {}).get("state", "")
            )
            fuel_tech = map_compat_fueltech(
                facility_record.get("fuel_tech", "")
            )
            registered_capacity = clean_capacity(
                facility_record.get("registered_capacity")
            )

            record = StationSchema(
                name=station_record["display_name"],
                station_code=station_id,
                network_region=map_compat_network_region(
                    station_record["region_id"]
                ),
                status=status,
                duid=duid,
                fueltech=fuel_tech,
                capacity=registered_capacity,
            )

            records.append(record)

    records = sort_records(records)

    return records


def load_current() -> List[StationSchema]:
    """
        Load the current project station data into a list of station schemas
    """
    stations = load_data("stations.geojson", True)

    records = []

    for s in stations.get("features", []):
        station = s.get("properties")

        for facility in station.get("duid_data", {}):

            record = StationSchema(
                name=station.get("name"),
                station_code=station.get("station_code"),
                network_region=facility.get("network_region"),
                status=facility.get("status"),
                duid=facility.get("duid"),
                fueltech=facility.get("fuel_tech"),
                capacity=facility.get("capacity_registered"),
            )

            records.append(record)

    records = sort_records(records)

    return records
