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

from .schema import FacilitySchema, StationSchema

__all__ = ["load_registry", "load_current"]


def _sort_stations(records: List[Any]) -> List[Any]:
    return sorted(records, key=attrgetter("state", "name"))


def _sort_facilities(records: List[Any]) -> List[Any]:
    return sorted(records, key=attrgetter("duid", "status"))


def load_registry() -> List[StationSchema]:
    """
        Loads the facility registry into a list of Station schema's
    """
    stations = load_data("facility_registry.json")

    records = []

    for station_id, station_record in stations.items():
        facilities = []

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

            facility = FacilitySchema(
                network_region=map_compat_network_region(
                    station_record["region_id"]
                ),
                status=status,
                duid=duid,
                fueltech=fuel_tech,
                capacity=registered_capacity,
            )

            facilities.append(facility)

        record = StationSchema(
            name=station_record["display_name"],
            code=station_id,
            state=station_record.get("location", {}).get("state", None),
            facilities=_sort_facilities(facilities),
        )

        records.append(record)

    records = _sort_stations(records)

    return records


def load_current() -> List[StationSchema]:
    """
        Load the current project station data into a list of station schemas
    """
    station_data = load_data("stations.geojson", True)

    records = []

    for s in station_data.get("features", []):
        station = s.get("properties")

        facilities = []

        for facility in station.get("duid_data", {}):

            facility = FacilitySchema(
                network_region=facility.get("network_region"),
                status=facility.get("status"),
                duid=facility.get("duid"),
                fueltech=facility.get("fuel_tech"),
                capacity=facility.get("capacity_registered"),
            )

            facilities.append(facility)

        record = StationSchema(
            name=station.get("name"),
            code=station.get("station_code"),
            state=station.get("state"),
            facilities=_sort_facilities(facilities),
        )

        records.append(record)

    records = _sort_stations(records)

    return records
