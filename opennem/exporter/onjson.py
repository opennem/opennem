import json

from opennem.controllers.stations import get_stations
from opennem.exporter.csv import stations_csv_records
from opennem.exporter.encoders import OpenNEMJSONEncoder


def stations_json_serialize():

    json_records = stations_csv_records()

    json_serialized = json.dumps(
        json_records, cls=OpenNEMJSONEncoder, indent=4
    )

    return json_serialized
