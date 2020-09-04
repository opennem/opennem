import json
from typing import List

from opennem.controllers.stations import get_stations
from opennem.exporter.csv import stations_csv_records
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.schema.opennem import StationSchema


def stations_json_serialize(stations: List[StationSchema]):

    json_records = stations_csv_records(stations)

    json_serialized = json.dumps(
        json_records, cls=OpenNEMJSONEncoder, indent=4
    )

    return json_serialized
