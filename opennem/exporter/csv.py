import csv
from io import StringIO

from opennem.core.facility_duid_map import duid_is_retired
from opennem.schema.opennem import StationSchema


def stations_csv_records(stations: list[StationSchema]) -> list[dict]:
    records = []

    for station in stations:
        if not station.facilities or len(station.facilities) < 1:
            continue

        for facility in station.facilities:
            if facility.fueltech is None:
                continue

            if facility.status is None:
                continue

            if facility.code and duid_is_retired(facility.code):
                continue

            if facility.active is False:
                continue

            rec = {
                "name": station.name,
                "code": facility.code,
                "region": facility.network_region,
                "status": facility.status.code,
                "fueltech": facility.fueltech.code,
                "unit_id": facility.unit_id,
                "unit_num": facility.unit_number,
                # "unit_cap": facility.capacity_aggregate,
                # "station_cap_agg": station.capacity_aggregate,
                # "station_cap_registered": station.,
                # "craeted_by": facility.created_by,
            }
            records.append(rec)

    return records


def stations_csv_serialize(stations, csv_stream=None) -> StringIO:
    if not csv_stream:
        csv_stream = StringIO()

    csv_records = stations_csv_records(stations)

    csv_fieldnames = csv_records[0].keys()

    csvwriter = csv.DictWriter(csv_stream, fieldnames=csv_fieldnames)
    csvwriter.writeheader()
    csvwriter.writerows(csv_records)

    return csv_stream
