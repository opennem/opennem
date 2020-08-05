import csv

from geojson import Feature, FeatureCollection, Point, dumps
from opennem.api.stations import get_stations
from opennem.exporter.encoders import OpenNEMGeoJSONEncoder

__all__ = ["stations_geojson_serialize"]


def stations_geojson_records():
    stations = get_stations()

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
            "registered_capacity": station.capacity_registered,
            "capacity_registered": station.capacity_registered,
            "capacity_aggregate": station.capacity_aggregate,
            "duid_data": [],
        }

        for facility in station.facilities:
            f.properties["duid_data"].append(
                {
                    "oid": facility.oid,
                    "duid": facility.duid,
                    "fuel_tech": facility.fueltech_id,
                    "fuel_tech_label": facility.fueltech_label,
                    "fuel_tech_renewable": facility.fueltech.renewable,
                    "commissioned_date": facility.registered,
                    "status": facility.status_id,
                    "status_label": facility.status_label,
                    "unit_id": facility.unit_id,
                    "unit_number": facility.unit_number,
                    "unit_size": facility.unit_capacity,
                    "unit_alias": facility.unit_alias,
                    # backwards compat field
                    "registered_capacity": facility.capacity_registered,
                    # capacities for the unit
                    "capacity_registered": facility.capacity_registered,
                    "capacity_aggregate": facility.capacity_aggregate,
                    # network specific fields (DUID is one)
                    "network_region": facility.network_region,
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

    geoj["name"] = "opennem_stations"
    geoj["crs"] = crs

    geoj_string = dumps(geoj, indent=4, cls=OpenNEMGeoJSONEncoder)

    return geoj_string


if __name__ == "__main__":
    stations_geojson_serialize()
