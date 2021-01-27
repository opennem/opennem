from datetime import datetime

import pytest

from opennem.utils.interval import add_human_inerval

dt_subject = datetime.fromisoformat("2021-01-20 00:00:00")
dt_subject_tz = datetime.fromisoformat("2021-01-20 00:00:00+10:00")


@pytest.mark.parametrize(
    ["dt", "interval_human", "dt_expected"],
    [
        (dt_subject, "5m", datetime.fromisoformat("2021-01-20 00:05:00")),
        (dt_subject, "1h", datetime.fromisoformat("2021-01-20 01:00:00")),
        (dt_subject, "1M", datetime.fromisoformat("2021-02-20 00:00:00")),
        (dt_subject, "1Y", datetime.fromisoformat("2022-01-20 00:00:00")),
        #
        (dt_subject, "15m", datetime.fromisoformat("2021-01-20 00:15:00")),
        (dt_subject, "12h", datetime.fromisoformat("2021-01-20 12:00:00")),
        (dt_subject, "2M", datetime.fromisoformat("2021-03-20 00:00:00")),
        (dt_subject, "2Y", datetime.fromisoformat("2023-01-20 00:00:00")),
    ],
)
def test_human_interval_sums(dt: datetime, interval_human: str, dt_expected: datetime) -> None:
    dt_subject = add_human_inerval(dt, interval_human)
    assert dt_subject == dt_expected
