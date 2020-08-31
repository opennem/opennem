import json
from typing import List

from pydantic import ValidationError

from opennem.exporter.aws import write_to_s3
from opennem.exporter.csv import stations_csv_serialize
from opennem.exporter.geojson import stations_geojson_serialize
from opennem.exporter.local import write_to_local
from opennem.exporter.onjson import stations_json_serialize
from opennem.importer.all import run_all
from opennem.importer.opennem import opennem_import
from opennem.schema.opennem import StationSchema
from opennem.utils.log_config import logging

logger = logging.getLogger("opennem.exporter")


def load_stations():
    with open("data/opennem.json") as fh:
        __data = json.load(fh)

    stations: List[StationSchema] = []

    for i in __data.values():
        try:
            stations.append(StationSchema(**i))
        except ValidationError as e:
            logger.error(
                "Error with record: {} {}: {}".format(i["code"], i["name"], e)
            )

    return stations


def stations_geojson_to_s3(stations: List[StationSchema]):
    stations_geojson = stations_geojson_serialize(stations)

    facilities_path = "geo/au_facilities.json"

    file_length = write_to_s3(facilities_path, stations_geojson)

    return file_length


def stations_geojson_to_local(stations: List[StationSchema]):
    stations_geojson = stations_geojson_serialize(stations)

    write_to_local("stations.geojson", stations_geojson)


def stations_csv_to_local(stations: List[StationSchema]):
    stations_csv = stations_csv_serialize(stations)

    write_to_local("stations.csv", stations_csv)


def stations_json_to_local(stations: List[StationSchema]):
    stations_json = stations_json_serialize(stations)

    write_to_local("stations.json", stations_json)


if __name__ == "__main__":
    run_all()
    stations = opennem_import()

    stations_geojson_to_s3(stations.copy())
    stations_geojson_to_local(stations.copy())
    stations_csv_to_local(stations.copy())
    stations_json_to_local(stations.copy())
