from datetime import datetime

from opennem.schema.network import NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.timezone import is_aware


class TestTimezones:
    def test_wem_settlementdate_tz(self) -> None:
        subject = parse_date("2020/10/07 10:15:00", dayfirst=False, network=NetworkWEM)
        comparator = datetime(2020, 10, 7, 10, 15, 0, tzinfo=NetworkWEM.get_timezone())

        assert subject == comparator, "Parses date correctly"
        assert is_aware(subject) is True, "Date has timezone info"
