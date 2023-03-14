from datetime import date, datetime

import pytest

from opennem.core.bom import get_archive_page_for_station_code


@pytest.mark.parametrize(
    ["web_code", "month", "expected_result"],
    [
        (
            "4019",
            datetime(2021, 10, 1).date(),
            "http://www.bom.gov.au/climate/dwo/202110/html/IDCJDW4019.202110.shtml",
        ),
        (
            "0000",
            datetime(2021, 1, 1).date(),
            "http://www.bom.gov.au/climate/dwo/202101/html/IDCJDW0000.202101.shtml",
        ),
    ],
)
def test_get_archive_page_for_station_code(web_code: str, month: date, expected_result: str) -> None:
    bom_archive_page = get_archive_page_for_station_code(web_code, month)
    assert bom_archive_page == expected_result, "Returned url matches expected archive page"
