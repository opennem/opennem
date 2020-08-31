import csv
import json
import logging
from typing import List

from pydantic import ValidationError

from geojson import Feature, FeatureCollection, Point, dumps
from opennem.controllers.stations import get_stations
from opennem.core.facility_duid_map import duid_is_retired
from opennem.db import get_database_session
from opennem.exporter.encoders import OpenNEMGeoJSONEncoder, OpenNEMJSONEncoder
from opennem.schema.opennem import StationSchema

__all__ = ["stations_geojson_serialize"]


def stations_geojson_records():
    db = get_database_session()

    stations = get_stations(db)

    records = []

    for station in stations:

        geom = None

        if station.lat and station.lng:
            geom = Point((station.lat, station.lng))

        f = Feature(geometry=geom)

        f.properties = {
            "oid": station.oid,
            "ocode": station.ocode,
            "station_id": station.id,
            "station_code": station.network_code,
            "facility_id": station.network_code,
            "network": station.network.label,
            "network_country": station.network.country,
            "state": station.state.upper() if station.state else None,
            "postcode": station.postcode,
            "name": station.name,
            "capacity_registered": station.capacity_registered,
            "capacity_aggregate": station.capacity_aggregate,
            "duid_data": [],
        }

        for facility in station.facilities:
            if facility.fueltech_id is None:
                continue

            if facility.status_id is None:
                continue

            if duid_is_retired(facility.code):
                continue

            if facility.active is False:
                continue

            f.properties["duid_data"].append(
                {
                    "oid": facility.oid,
                    "duid": facility.duid,
                    "fuel_tech": facility.fueltech_id,
                    "fuel_tech_label": facility.fueltech_label,
                    "fuel_tech_renewable": facility.fueltech.renewable
                    if facility.fueltech
                    else None,
                    "commissioned_date": facility.registered,
                    "decommissioned_date": facility.deregistered,
                    "status": facility.status_id,
                    "status_label": facility.status_label,
                    "unit_id": facility.unit_id,
                    "unit_number": facility.unit_number,
                    "unit_size": facility.unit_capacity,
                    "unit_alias": facility.unit_alias,
                    # capacities for the unit
                    "capacity_registered": facility.capacity_registered,
                    "capacity_aggregate": facility.capacity_aggregate,
                    # network specific fields (DUID is one)
                    "network_region": facility.network_region,
                }
            )

        if len(f.properties["duid_data"]) > 0:
            records.append(f)

    return records


logger = logging.getLogger(__name__)


def stations_geojson_records_json(stations: List[StationSchema]):
    records = []

    for station in stations:

        geom = None

        if not station.facilities:
            continue

        if station.lat and station.lng:
            geom = Point((station.lng, station.lat))

        f = Feature(geometry=geom)

        f.properties = {
            # "oid": station.oid,
            # "ocode": station.ocode,
            "station_id": station.id,
            "station_code": station.code,
            "facility_id": station.code,
            "network": station.facilities[0].network.label,
            "network_country": station.facilities[0].network.country,
            "state": station.state,
            "postcode": station.postcode,
            "name": station.name,
            "capacity_registered": station.capacity_registered,
            # "capacity_aggregate": station.capacity_aggregate,
            "duid_data": [],
        }

        for facility in station.facilities:
            if facility.fueltech is None:
                continue

            if facility.status is None:
                continue

            if duid_is_retired(facility.code):
                continue

            if facility.active is False:
                continue

            f.properties["duid_data"].append(
                {
                    # "oid": facility.oid,
                    # "duid": facility.duid,
                    "fuel_tech": facility.fueltech.code,
                    "fuel_tech_label": facility.fueltech.label,
                    "fuel_tech_renewable": facility.fueltech.renewable,
                    "commissioned_date": facility.registered,
                    "decommissioned_date": facility.deregistered,
                    "status": facility.status.code,
                    "status_label": facility.status.label,
                    "unit_id": facility.unit_id,
                    "unit_number": facility.unit_number,
                    "unit_size": facility.unit_capacity,
                    "unit_alias": facility.unit_alias,
                    # capacities for the unit
                    "capacity_registered": facility.capacity_registered,
                    # "capacity_aggregate": facility.capacity_aggregate,
                    # network specific fields (DUID is one)
                    "network_region": facility.network_region,
                }
            )

        if len(f.properties["duid_data"]) > 0:
            records.append(f)

    return records


def stations_geojson_serialize(stations: List[StationSchema]):
    crs = {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    }

    stations = stations_geojson_records_json(stations)

    geoj = FeatureCollection(stations, crs=crs, name="opennem")

    geoj["name"] = "opennem_stations"
    geoj["crs"] = crs

    geoj_string = dumps(geoj, indent=4, cls=OpenNEMGeoJSONEncoder)

    return geoj_string


if __name__ == "__main__":
    stations_geojson_serialize()
