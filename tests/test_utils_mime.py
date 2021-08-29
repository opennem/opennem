from typing import BinaryIO

from opennem.utils.mime import is_zip


def test_old_xls_file_is_not_zip(xls_old_file: BinaryIO) -> None:
    assert is_zip(xls_old_file) is False, "Old XLS files are not zips"


def test_xls_file_is_not_zip(xls_file: BinaryIO) -> None:
    assert is_zip(xls_file) is True, "New XLS files are zips"


def test_xlsx_file_is_not_zip(xlsx_file: BinaryIO) -> None:
    assert is_zip(xlsx_file) is True, "XLSX files are zips"
