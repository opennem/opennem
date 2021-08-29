from typing import IO, BinaryIO, Callable

from opennem.core.parsers.excel import parse_workbook


def test_excel_parser(xls_file: BinaryIO) -> None:
    parsed_excel = parse_workbook(xls_file)

    assert isinstance(parsed_excel, dict), "Parsed excel response is a dict"
    assert len(parsed_excel.keys()), "Has at least one entry"
