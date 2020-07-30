import csv

from geojson import Feature, FeatureCollection, Point, dumps
from opennem.api.stations import get_stations
from opennem.exporter.encoders import OpenNEMGeoJSONEncoder

__all__ = ["stations_geojson_serialize"]


def stations_geojson_records():
    stations = get_stations()

    records = []

    for station in stations:

        f = Feature()

        f.properties = {
            "oid": station.oid,
            "oid": station.ocode,
            "station_id": station.id,
            "station_code": station.code,
            "facility_id": station.code,
            "network": station.network.label,
            "network_region": station.network_region,
            "state": station.state,
            "postcode": station.postcode,
            "name": station.name,
            "registered_capacity": station.capacity_registered,
            "duid_data": [],
        }

        for facility in station.facilities:
            f.properties["duid_data"].append(
                {
                    "oid": facility.oid,
                    "duid": facility.network_code,
                    "fuel_tech": facility.fueltech_id,
                    "fuel_tech_label": facility.fueltech.label
                    if facility.fueltech
                    else None,
                    "commissioned_date": facility.registered,
                    "status": facility.status_id,
                    "status_label": facility.status.label
                    if facility.status
                    else None,
                    "unit_id": facility.unit_id,
                    "unit_number": facility.unit_number,
                    "unit_size": facility.unit_capacity,
                    "unit_alias": facility.unit_alias,
                    "registered_capacity": facility.capacity_registered,
                }
            )

        records.append(f)

    return records


def stations_geojson_serialize():
    crs = {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    }

    stations = stations_geojson_records()

    geoj = FeatureCollection(stations, crs=crs, name="opennem")

    geoj["name"] = "nem_stations"
    geoj["crs"] = crs

    geoj_string = dumps(geoj, indent=4, cls=OpenNEMGeoJSONEncoder)

    return geoj_string


if __name__ == "__main__":
    stations_geojson_serialize()
