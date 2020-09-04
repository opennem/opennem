import csv
import json
import os
import zipfile
from pathlib import Path
from typing import Any, List, Optional

# DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
DATA_PATH = Path(__file__).parent / "data"
PROJECT_DATA_PATH = Path(__file__).parent.parent.parent / "data"

JSON_EXTENSIONS = [".json", ".jsonl", ".geojson"]


class FileNotFound(Exception):
    pass


class FileInvalid(Exception):
    pass


def load_data(
    file_name: str, from_project: bool = False, from_fixture: bool = False
) -> Any:
    """
        Load a CSV or JSON data file from either the library
        or project data directory

    """
    data_path = PROJECT_DATA_PATH if from_project else DATA_PATH

    file_path: Path = data_path / Path(file_name)

    if not file_path.exists() and file_path.is_file():
        raise FileNotFound("Not a file: {}".format(file_path))

    if file_path.suffix in [".zip"]:
        return load_data_zip(file_path)

    if file_path.suffix in [".csv"]:
        return load_data_csv(file_path)

    if file_path.suffix in JSON_EXTENSIONS:
        return load_data_json(file_path)

    return load_data_string(file_path)


def load_data_string(file_path: Path) -> str:

    content = ""

    with open(file_path) as fh:
        content = fh.read()

    return content


def load_data_zip(file_path: Path) -> str:
    content = ""

    with zipfile.ZipFile(file_path) as zf:
        zip_files = zf.namelist()

        if len(zip_files) == 1:
            content = zf.open(zip_files[0]).read()

            if type(content) is bytes:
                content = content.decode("utf-8")

            return {"filename": zip_files[0], "content": content}

        if len(zip_files) != 1:
            raise Exception(
                "Zero or more than one file in zip file. Have {}".format(
                    len(zip_files)
                )
            )


def load_data_json(file_path: Path) -> Any:
    fixture: Any = None

    with file_path.open() as fh:
        fixture = json.load(fh)

    return fixture


def load_data_csv(file_path: Path) -> Optional[List[dict]]:
    """
        Load a CSV file

        @TODO use libmagic to determine encoding types since Excel saves
        can be funky
    """
    records = []

    # leave the encoding in place now todo is to determine it
    with open(file_path, encoding="utf-8-sig") as fh:
        csvreader = csv.DictReader(fh)
        records = [entry for entry in csvreader]

    return records
