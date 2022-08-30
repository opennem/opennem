""" Utilities used in unit tests """
import json
from pathlib import Path
from typing import Any

TEST_FIXTURE_PATH = Path(__file__).parent.parent.parent / "tests" / "fixtures"


if not TEST_FIXTURE_PATH.is_dir():
    raise Exception("Not a directory: {}".format(TEST_FIXTURE_PATH))


def load_fixture(fixture_name: str) -> Any:
    """Loads a tests file fixture from tests/fixtures"""
    fixture_path = TEST_FIXTURE_PATH / fixture_name

    if not fixture_path.is_file():
        raise Exception("Not a file: {}".format(fixture_path))

    fixture = None

    with fixture_path.open() as fh:
        if fixture_path.suffix == ".json":
            fixture = json.load(fh)
        else:
            fixture = fh.read()

    return fixture
