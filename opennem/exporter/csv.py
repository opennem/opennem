import csv
from io import StringIO
from typing import List

from opennem.controllers.stations import get_stations
from opennem.core.facility_duid_map import duid_is_retired
from opennem.db import get_database_session
from opennem.schema.opennem import StationSchema


def stations_csv_records(stations: List[StationSchema]):
    records = []

    for station in stations:
        for facility in station.facilities:
            if facility.fueltech is None:
                continue

            if facility.status is None:
                continue

            if duid_is_retired(facility.code):
                continue

            if facility.active is False:
                continue

            rec = {
                "name": station.name,
                "oid": station.oid(),
                "ocode": station.ocode(),
                "code": facility.code,
                "region": facility.network_region,
                "status": facility.status.code,
                "fueltech": facility.fueltech.code,
                "unit_id": facility.unit_id,
                "unit_num": facility.unit_number,
                # "unit_cap": facility.capacity_aggregate,
                # "station_cap_agg": station.capacity_aggregate,
                "station_cap_registered": station.capacity_registered,
                "craeted_by": facility.created_by,
            }
            records.append(rec)

    return records


def stations_csv_serialize(stations, csv_stream=None):

    if not csv_stream:
        csv_stream = StringIO()

    csv_records = stations_csv_records(stations)

    csv_fieldnames = csv_records[0].keys()

    csvwriter = csv.DictWriter(csv_stream, fieldnames=csv_fieldnames)
    csvwriter.writeheader()
    csvwriter.writerows(csv_records)

    return csv_stream
