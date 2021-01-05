import csv
import json
import logging
import os
import sys
import zipfile
from pathlib import Path
from pkgutil import get_data, get_loader
from typing import Any, List, Optional

logger = logging.getLogger("opennem.core.loader")

MODULE_PATH = Path(os.path.dirname(sys.modules["opennem"].__file__))
DATA_PATH = "core/data"
FIXTURE_PATH = "db/fixtures"
SETTINGS_PATH = "settings"
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
    from_settings: bool = False,
    skip_loaders: bool = False,
    content_type: str = "utf-8",
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
        else SETTINGS_PATH
        if from_settings
        else DATA_PATH
    )

    file_path = Path(file_name)

    data_content = get_data("opennem", os.path.join(data_path, file_name))

    if not data_content:
        return None

    if skip_loaders:
        return data_content.decode(content_type)

    if file_path.suffix in [".zip"]:
        return load_data_zip(os.path.join(data_path, file_name))

    if file_path.suffix in [".csv"]:
        return load_data_csv(data_content.decode(content_type))

    if file_path.suffix in JSON_EXTENSIONS:
        return load_data_json(data_content.decode(content_type))

    return data_content


def get_data_path() -> Path:
    """
    Get project data path
    """
    pkg_path = None
    p = None

    try:
        p = get_loader("opennem")
    except Exception:
        logger.error("Error could not get data path for opennem package")

    if p:
        pkg_path = Path(p.get_filename()).parent

    # Fall back to getting data path using directories
    else:
        pkg_path = Path(__file__).parent.parent.parent

    data_path = pkg_path / PROJECT_DATA_PATH

    if not data_path.is_dir():
        raise Exception("No data path: {}".format(data_path))

    return data_path


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
