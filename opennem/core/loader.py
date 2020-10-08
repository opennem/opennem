import csv
import json
import os
import sys
import zipfile
from pathlib import Path
from pkgutil import get_data
from typing import Any, List, Optional

MODULE_PATH = Path(os.path.dirname(sys.modules["opennem"].__file__))
DATA_PATH = "core/data"
FIXTURE_PATH = "db/fixtures"
PROJECT_DATA_PATH = "data"

JSON_EXTENSIONS = [".json", ".jsonl", ".geojson"]


class FileNotFound(Exception):
    pass


class FileInvalid(Exception):
    pass


def load_data(
    file_name: str,
    from_project: bool = False,
    from_fixture: bool = False,
    skip_loaders: bool = False,
) -> Any:
    """
        Load a CSV or JSON data file from either the library
        or project data directory

        default loads from `opennem/core/data/`

        from_project is `opennem/data`

        from_fixture is `opennem/db/fixtures`

    """
    data_path = (
        PROJECT_DATA_PATH
        if from_project
        else FIXTURE_PATH
        if from_fixture
        else DATA_PATH
    )

    file_path = Path(file_name)

    data_content = get_data(
        "opennem", os.path.join(data_path, file_name)
    ).decode("utf-8")

    if skip_loaders:
        return data_content

    if file_path.suffix in [".zip"]:
        return load_data_zip(data_content)

    if file_path.suffix in [".csv"]:
        return load_data_csv(data_content)

    if file_path.suffix in JSON_EXTENSIONS:
        return load_data_json(data_content)

    return data_content


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


def load_data_json(file_content: str) -> Any:
    fixture: Any = None

    fixture = json.loads(file_content)

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
