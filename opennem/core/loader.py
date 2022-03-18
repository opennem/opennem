""" Core loaders that handle files """
import csv
import json
import logging
import os
import sys
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from pkgutil import get_data, get_loader
from typing import Any, List, Optional, Union

logger = logging.getLogger("opennem.core.loader")

MODULE_PATH_FULL = sys.modules["opennem"].__file__
MODULE_PATH = None
PROJECT_ROOT = None

if MODULE_PATH_FULL:
    MODULE_PATH = Path(os.path.dirname(MODULE_PATH_FULL))
    PROJECT_ROOT = MODULE_PATH.parent

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
    return_path: bool = False,
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

    if return_path:
        module_path = Path(get_loader("opennem").path).parent
        return module_path / data_path / file_name

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


@dataclass
class ZipFileReturn:
    filename: str
    content: Union[str, bytes]


def load_data_zip(file_path: Union[Path, BytesIO], decode_return: bool = True) -> ZipFileReturn:
    """Loadds a ZipFile from a file path or buffer and returns an object with the content"""
    content: Union[str, bytes] = ""

    with zipfile.ZipFile(file_path) as zf:
        zip_files = zf.namelist()

        if len(zip_files) == 1:
            content = zf.open(zip_files[0]).read()

            if type(content) is bytes and decode_return:
                content = content.decode("utf-8")

        if len(zip_files) != 1:
            raise Exception(
                "Zero or more than one file in zip file. Have {}".format(len(zip_files))
            )

    return ZipFileReturn(filename=zip_files[0], content=content)


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
