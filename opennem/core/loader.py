import csv
import json
import os
from pathlib import Path
from typing import Any, List, Optional

# DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
DATA_PATH = Path(__file__) / "data"
PROJECT_DATA_PATH = Path(__file__).parent.parent.parent / "data"


class FileNotFound(Exception):
    pass


def load_data(fixture_name: str, from_project: bool = False) -> Any:
    """
        Load a CSV or JSON data file from either the library
        or project data directory

    """
    data_path = PROJECT_DATA_PATH if from_project else DATA_PATH

    if fixture_name.endswith(".csv"):
        return load_data_csv(fixture_name, data_path)

    return load_data_json(fixture_name, data_path)


def load_data_json(fixture_name: str, data_path: Path = DATA_PATH) -> Any:
    fixture_path = data_path / fixture_name

    if not fixture_path.exists() and fixture_path.is_file():
        raise FileNotFound("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture


def load_data_csv(
    filename: str, data_path: Path = DATA_PATH
) -> Optional[List[dict]]:
    """
        Load a CSV file

        @TODO use libmagic to determine encoding types since Excel saves
        can be funky
    """

    data_filepath = data_path / filename

    if not data_filepath.exists() and data_filepath.is_file():
        raise FileNotFound("Not a file: {}".format(data_filepath))

    records = []

    # leave the encoding in place now todo is to determine it
    with open(data_filepath, encoding="utf-8-sig") as fh:
        csvreader = csv.DictReader(fh)
        records = [entry for entry in csvreader]

    return records
