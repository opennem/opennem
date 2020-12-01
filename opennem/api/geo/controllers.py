from typing import Dict, List

from geojson_pydantic.geometries import Point

from opennem.db.models.opennem import Station

from .schema import FacilityFeature, FacilityGeo


def stations_to_geojson(stations: List[Station]) -> FacilityGeo:
    features = []

    for station in stations:
        if not station.location:
            continue

        if not station.facilities or len(station.facilities) < 1:
            continue

        feature_dict: Dict = dict(properties=dict())

        feature_dict["properties"] = {
            "station_id": station.id,
            "station_code": station.code,
            "facility_id": station.code,
            "network": station.facilities[0].network.label,
            "network_country": station.facilities[0].network.country,
            "state": station.location.state,
            "postcode": station.location.postcode,
            "name": station.name,
            "capacity_registered": station.capacity_registered,
            # "capacity_aggregate": station.capacity_aggregate,
            "duid_data": [],
        }

        for facility in station.facilities:

            if not facility.fueltech:
                continue

            feature_dict["properties"]["duid_data"].append(
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

        feature = FacilityFeature(**feature_dict)

        if station.location and station.location.geom:
            geom = Point(
                coordinates=(station.location.lng, station.location.lat)
            )

            if not feature.geometry:
                feature.geometry = geom

        features.append(feature)

    crs = {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    }

    geo = FacilityGeo(features=features, crs=crs, name="opennem.facilities")

    return geo
