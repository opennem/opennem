from datetime import datetime

import pytest

from opennem.api.stats.utils import get_time_series_for_station
from opennem.api.time import human_to_interval, human_to_period
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.dates import get_last_completed_interval_for_network, is_aware


@pytest.mark.parametrize(
    ["network", "interval", "date_min", "date_max", "period", "expected"],
    [
        (NetworkNEM, None, None, None, human_to_period("7d"), OpennemExportSeries()),
        (NetworkNEM, human_to_interval("1h"), None, None, human_to_period("7d"), OpennemExportSeries()),
        (NetworkWEM, None, None, None, human_to_period("7d"), OpennemExportSeries()),
    ],
)
def test_get_time_series_for_station(
    network: NetworkSchema,
    interval: TimeInterval | None,
    date_min: datetime | None = None,
    date_max: datetime | None = None,
    period: TimePeriod | None = None,
) -> None:
    subject = get_time_series_for_station(network=network, interval=interval, date_min=date_min, date_max=date_max, period=period)
    latest_network_interval = get_last_completed_interval_for_network(network=network)

    # Test has a timezone
    assert is_aware(subject.end), "End is date aware"
    assert is_aware(subject.end), "End is date aware"

    if period:
        assert subject.end == latest_network_interval, "End is latest interval"
        assert subject.start == latest_network_interval - period, "Start is latest interval minus period"
