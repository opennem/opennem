import csv
from io import StringIO

from opennem.controllers.stations import get_stations
from opennem.core.facility_duid_map import duid_is_retired


def stations_csv_records():
    stations = get_stations()

    records = []

    for station in stations:
        for facility in station.facilities:
            if facility.fueltech_id is None:
                continue

            if facility.status_id is None:
                continue

            if duid_is_retired(facility.code):
                continue

            if facility.active == False:
                continue

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
                "updated_by": facility.updated_by,
            }
            records.append(rec)

    return records


def stations_csv_serialize(csv_stream=None):

    if not csv_stream:
        csv_stream = StringIO()

    csv_records = stations_csv_records()

    csv_fieldnames = csv_records[0].keys()

    csvwriter = csv.DictWriter(csv_stream, fieldnames=csv_fieldnames)
    csvwriter.writeheader()
    csvwriter.writerows(csv_records)

    return csv_stream
