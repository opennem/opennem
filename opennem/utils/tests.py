import json
import os
from typing import Any

TEST_FIXTURE_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def load_fixture(fixture_name: str) -> Any:
    fixture_path = os.path.join(TEST_FIXTURE_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture
