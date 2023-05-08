from datetime import UTC, datetime, timedelta

import pytest

from opennem.utils.dates import date_series, parse_date
from opennem.utils.timezone import is_aware


class TestUtilDates:
    def test_date_none(self):
        with pytest.raises(ValueError) as excinfo:
            parse_date(None)

        assert "Require a datetime or string" in str(excinfo), "Empty string raises exception"

    def test_date_empty(self):
        with pytest.raises(ValueError) as excinfo:
            parse_date("")

        assert "Invalid date string passed" in str(excinfo), "Empty string raises exception"

    def test_wem_date_comissioned(self):
        subject = parse_date("1/11/08 0:00")
        comparator = datetime(2008, 11, 1, 0, 0, 0)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is False, "Date has no timezone info"

    def test_nem_dispatch_interval_amiguous(self):
        subject = parse_date("1/9/19 4:00")
        comparator = datetime(2019, 9, 1, 4, 0, 0)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is False, "Date has no timezone info"

    def test_nem_dispatch_interval(self):
        subject = parse_date("30/9/19 4:00")
        comparator = datetime(2019, 9, 30, 4, 0, 0)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is False, "Date has no timezone info"

    def test_nem_dispatch_scada_interval(self):
        subject = parse_date("2020/06/01 21:35:00", dayfirst=False)
        comparator = datetime(2020, 6, 1, 21, 35, 0)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is False, "Date has no timezone info"

    def test_nem_settlementdate(self):
        subject = parse_date("2020/10/07 10:15:00", dayfirst=False)
        comparator = datetime(2020, 10, 7, 10, 15, 0)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is False, "Date has no timezone info"

    def test_nem_excel_formatted(self):
        subject = parse_date("27/9/2019  2:55:00 pm")
        comparator = datetime(2019, 9, 27, 14, 55, 0)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is False, "Date has no timezone info"

    def test_bom_date(self):
        subject = parse_date("20201008133000", dayfirst=False)
        comparator = datetime(2020, 10, 8, 13, 30, 0, 0)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is False, "Date has no timezone info"

    def test_bom_date_utc(self):
        subject = parse_date("20201008133000", dayfirst=False, is_utc=True)
        comparator = datetime(2020, 10, 8, 13, 30, 0, 0, tzinfo=UTC)

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is True, "Date has timezone info"

    def test_date_series(self):
        # defaults to now going back 30 days
        series = list(date_series(reverse=True))

        date_today = datetime.now().date()
        date_29_days_ago = date_today - timedelta(days=29)

        assert len(series) == 30, "There are 30 dates"
        assert series[0] == date_today, "First entry is today"
        assert series[29] == date_29_days_ago, "Last entry is 29 days ago"
