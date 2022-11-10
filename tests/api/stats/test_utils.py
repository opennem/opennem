from datetime import datetime

import pytest

from opennem.api.stats.utils import get_time_series_for_station
from opennem.api.time import human_to_interval, human_to_period
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.dates import get_last_completed_interval_for_network, is_aware
from opennem.utils.interval import get_human_interval

nem_latest_network_interval = get_last_completed_interval_for_network(network=NetworkNEM)
# wem_latest_network_interval = get_last_completed_interval_for_network(network=NetworkWEM)


@pytest.mark.parametrize(
    ["network", "interval", "date_min", "date_max", "period", "expected"],
    [
        (
            NetworkNEM,
            None,
            None,
            None,
            human_to_period("7d"),
            OpennemExportSeries(
                start=nem_latest_network_interval - get_human_interval("7d"),
                end=nem_latest_network_interval,
                network=NetworkNEM,
                interval=NetworkNEM.get_interval(),
            ),
        ),
        # (NetworkNEM, human_to_interval("1h"), None, None, human_to_period("7d"), OpennemExportSeries()),
        # (NetworkWEM, None, None, None, human_to_period("7d"), OpennemExportSeries()),
    ],
)
def test_get_time_series_for_station(
    network: NetworkSchema,
    interval: TimeInterval | None,
    date_min: datetime | None,
    date_max: datetime | None,
    period: TimePeriod | None,
    expected: OpennemExportSeries,
) -> None:
    subject = get_time_series_for_station(network=network, interval=interval, date_min=date_min, date_max=date_max, period=period)

    # Test has a timezone
    assert is_aware(subject.end), "End is date aware"
    assert is_aware(subject.end), "End is date aware"

    if period:
        assert subject.end == nem_latest_network_interval, "End is latest interval"
        assert subject.start == nem_latest_network_interval - human_to_interval(
            period.period_human
        ), "Start is latest interval minus period"
