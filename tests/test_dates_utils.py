from datetime import datetime

import pytest

from opennem.utils.dates import get_end_of_last_month


@pytest.mark.parametrize(
    ["dt", "dt_expected"],
    [
        ("2021-01-31 12:45:00+10:00", "2020-12-31 12:45:00+10:00"),
        ("2021-01-01 12:45:00+10:00", "2020-12-31 12:45:00+10:00"),
        ("2021-02-15 12:45:00+10:00", "2021-01-31 12:45:00+10:00"),
        ("2021-03-15 12:45:00+10:00", "2021-02-28 12:45:00+10:00"),
    ],
)
def test_get_end_of_last_month(dt: str, dt_expected: str) -> None:
    dtd = datetime.fromisoformat(dt)
    dtd_expected = datetime.fromisoformat(dt_expected)

    dt_subject = get_end_of_last_month(dtd)

    assert dt_subject == dtd_expected, "Date is end of last month"
