import io
from pathlib import Path
from typing import BinaryIO, Callable

import pytest
from betamax import Betamax

with Betamax.configure() as config:
    config.cassette_library_dir = "tests/fixtures/cassettes"


PATH_TESTS_ROOT = Path(__file__).parent
PATH_TESTS_FIXTURES = PATH_TESTS_ROOT / "fixtures"

if not PATH_TESTS_FIXTURES.is_dir():
    raise Exception("Test fixtures path not found: {}".format(PATH_TESTS_FIXTURES))


def load_fixture_file(filename: str) -> str:
    """Load a test fixture and return its content. Assumes relative path"""
    fixture_path = PATH_TESTS_FIXTURES / Path(filename)

    if not fixture_path.is_file():
        raise Exception("Not a file: {}".format(filename))

    fixture_content = ""

    with fixture_path.open() as fh:
        fixture_content = fh.read()

    return fixture_content


def load_fixture_file_binary(filename: str, directory: str = "files") -> io.BytesIO:
    """Read a fixture file and return a file object"""
    fixture_path = PATH_TESTS_FIXTURES / directory / filename

    if not fixture_path.is_file():
        raise Exception("Could not find excel fixture at {}".format(fixture_path))

    fixture_content = io.open(fixture_path, mode="rb")

    return fixture_content


@pytest.fixture
def load_file() -> Callable:
    """Load a static file pytest fixture"""
    return load_fixture_file


@pytest.fixture
def load_file_binary() -> Callable:
    """Load a static file pytest fixture"""
    return load_fixture_file_binary


# Fixtures Below


@pytest.fixture
def xls_old_file(load_file: Callable) -> BinaryIO:
    return load_fixture_file_binary("old.xls")


@pytest.fixture
def xls_file(load_file: Callable) -> BinaryIO:
    return load_fixture_file_binary("excel_template_compat.xls")


@pytest.fixture
def xlsx_file(load_file: Callable) -> BinaryIO:
    return load_fixture_file_binary("excel_template.xlsx")


@pytest.fixture
def aemo_nemweb_dispatch_scada(load_file: Callable) -> BinaryIO:
    return load_fixture_file_binary("PUBLIC_DISPATCHSCADA_202109021255_0000000348376188.zip")
