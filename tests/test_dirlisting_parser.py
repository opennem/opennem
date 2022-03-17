from datetime import datetime
from pathlib import Path
from typing import Dict, Union

import pytest

from opennem.core.parsers.dirlisting import (
    DirlistingEntry,
    parse_dirlisting_datetime,
    parse_dirlisting_line,
)

from .conftest import PATH_TESTS_FIXTURES


def load_fixture(filename: str = "nemweb_dirlisting.html") -> str:
    fixture_path = PATH_TESTS_FIXTURES / Path(filename)

    if not fixture_path.is_file():
        raise Exception("Not a file: {}".format(filename))

    fixture_content = ""

    with fixture_path.open() as fh:
        fixture_content = fh.read()

    return fixture_content


@pytest.mark.parametrize(
    ["datetime_string", "datetime_expected"],
    [("Monday, November 8, 2021  2:30 PM", datetime.fromisoformat("2021-11-08T14:30"))],
)
def test_parse_dirlisting_datetime(datetime_string: str, datetime_expected: datetime) -> None:
    datetime_subject = parse_dirlisting_datetime(datetime_string)
    assert datetime_expected == datetime_subject, "Datetime parsed correctly"


@pytest.mark.parametrize(
    ["line", "result"],
    [
        (
            '     Monday, November 8, 2021  2:30 PM        18166 <a href="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip">PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip</a>',
            {
                "filename": Path("PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip"),
                "modified_date": datetime.fromisoformat("2021-11-08T14:30:00"),
                # "aemo_created_date": datetime.fromisoformat("2021-11-08T14:35:00"),
                "file_size": 18166,
                "link": "http://nemweb.com.au/Reports/Current/DispatchIS_Reports/PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip",
            },
        ),
        (
            'Monday, February 11, 2019  4:31 PM        <dir> <a href="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/DUPLICATE/">DUPLICATE</a>',
            {
                "filename": Path("DUPLICATE"),
                "modified_date": datetime.fromisoformat("2019-02-11T16:31:00"),
                "file_size": None,
                "link": "http://nemweb.com.au/Reports/Current/DispatchIS_Reports/DUPLICATE/",
            },
        ),
    ],
)
def test_dirlisting_line(line: str, result: Dict[str, Union[str, datetime, int]]) -> None:
    result_model = DirlistingEntry(**result)
    dirlisting_line_result = parse_dirlisting_line(line)

    assert result_model == dirlisting_line_result, "Models match for dirlisting line"
