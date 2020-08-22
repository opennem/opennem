import csv
import json
import os
from typing import Any, List, Optional

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


class FileNotFound(Exception):
    pass


def load_data_json(fixture_name: str) -> Any:
    fixture_path = os.path.join(DATA_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise FileNotFound("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture


def load_data_csv(filename: str) -> Optional[List[dict]]:
    """
        Load a CSV file

        @TODO use libmagic to determine encoding types since Excel saves
        can be funky
    """

    data_filepath = os.path.join(DATA_PATH, filename)

    if not os.path.isfile(data_filepath):
        raise FileNotFound("Not a file: {}".format(data_filepath))

    records = []

    # leave the encoding in place now todo is to determine it
    with open(data_filepath, encoding="utf-8-sig") as fh:
        csvreader = csv.DictReader(fh)
        records = [entry for entry in csvreader]

    return records
