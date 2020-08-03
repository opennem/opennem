import csv
from io import StringIO

from opennem.api.stations import get_stations


def stations_csv_records():
    stations = get_stations()

    records = []

    for station in stations:
        for facility in station.facilities:
            rec = {
                "oid": station.oid,
                "ocode": station.ocode,
                "name": station.name,
                "network": facility.network_code,
                "region": facility.network_region,
                "status": facility.status_label,
                "fueltech": facility.fueltech_label,
                "added_by": facility.created_by,
                "updated_by": facility.created_by,
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
