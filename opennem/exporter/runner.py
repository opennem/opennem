import json
import logging
from typing import List

from pydantic import ValidationError

from opennem.importer.all import run_all
from opennem.importer.opennem import opennem_import
from opennem.schema.opennem import StationSchema

logger = logging.getLogger("opennem.exporter")


def load_stations(file_path: str = "opennem.json") -> List[StationSchema]:
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


if __name__ == "__main__":
    run_all()
    stations = opennem_import()
