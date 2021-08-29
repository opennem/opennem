from typing import IO, BinaryIO, Callable

from openpyxl.workbook.workbook import Workbook

from opennem.core.parsers.excel import parse_workbook


def test_excel_parser(xls_file: BinaryIO) -> None:
    parsed_excel = parse_workbook(xls_file)

    assert isinstance(parsed_excel, Workbook), "Parsed excel response is a workbook"
