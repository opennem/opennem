import io
from typing import BinaryIO, Callable

import pytest

from .utils import PATH_TESTS_FIXTURES


@pytest.fixture
def load_file() -> Callable:
    def _read_file(filename: str) -> BinaryIO:
        excel_file_path = PATH_TESTS_FIXTURES / "files" / filename

        if not excel_file_path.is_file():
            raise Exception("Could not find excel fixture at {}".format(excel_file_path))

        _fh = io.open(excel_file_path, mode="rb")

        return _fh

    return _read_file


@pytest.fixture
def xls_old_file(load_file: Callable) -> BinaryIO:
    return load_file("old.xls")


@pytest.fixture
def xls_file(load_file: Callable) -> BinaryIO:
    return load_file("excel_template_compat.xls")


@pytest.fixture
def xlsx_file(load_file: Callable) -> BinaryIO:
    return load_file("excel_template.xlsx")


@pytest.fixture
def aemo_nemweb_dispatch_scada(load_file: Callable) -> BinaryIO:
    return load_file("PUBLIC_DISPATCHSCADA_202109021255_0000000348376188.zip")
