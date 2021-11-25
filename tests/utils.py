"""Test utilities including paths and helper functions
"""
from pathlib import Path

# from opennem import __path__

PATH_TESTS_ROOT = Path(__file__).parent
PATH_TESTS_FIXTURES = PATH_TESTS_ROOT / "fixtures"

if not PATH_TESTS_FIXTURES.is_dir():
    raise Exception("Test fixtures path not found: {}".format(PATH_TESTS_FIXTURES))


def load_fixture(filename: str) -> str:
    """Load a test fixture and return its content. Assumes relative path"""
    fixture_path = PATH_TESTS_FIXTURES / Path(filename)

    if not fixture_path.is_file():
        raise Exception("Not a file: {}".format(filename))

    fixture_content = ""

    with fixture_path.open() as fh:
        fixture_content = fh.read()

    return fixture_content
