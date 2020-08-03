import json

from opennem.api.stations import get_stations
from opennem.exporter.encoders import OpenNEMJSONEncoder


def stations_json_records():
    stations = get_stations()

    records = []

    for station in stations:
        for facility in station.facilities:
            rec = {
                "name": station.name,
                # "oid": station.oid,
                "ocode": station.ocode,
                "code": facility.duid,
                "region": facility.network_region,
                "status": facility.status_id,
                "fueltech": facility.fueltech_id,
                "unit_id": facility.unit_id,
                "unit_num": facility.unit_number,
                "unit_cap": facility.capacity_aggregate,
                "station_cap_agg": station.capacity_aggregate,
                "station_cap_registered": station.capacity_registered,
                "added_by": facility.created_by,
                "updated_by": facility.created_by,
            }
            records.append(rec)

    return records


def stations_json_serialize():

    json_records = stations_json_records()

    json_serialized = json.dumps(
        json_records, cls=OpenNEMJSONEncoder, indent=4
    )

    return json_serialized
