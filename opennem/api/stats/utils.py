"""API Stats utilities"""

from datetime import datetime

from fastapi import HTTPException
from starlette import status

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.dates import get_last_completed_interval_for_network, is_aware


def get_time_series_for_station(
    network: NetworkSchema,
    interval: TimeInterval | None = None,
    date_min: datetime | None = None,
    date_max: datetime | None = None,
    period: TimePeriod | None = None,
) -> OpennemExportSeries:
    """For API parameters return a time serie

    Users can either specify a time range or a period. If a period is specified
    then it takes from latest back to start of that period, otherwise

    @TODO raise data error on too many return intervals, which can be calculated
    """

    # validate that we have enough information to get a time series
    if not (date_min and date_max) or not period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No time range specified. Require either date_min and date_max or period",
        )

    # get the latest interval
    latest_network_interval = get_last_completed_interval_for_network(network=network)

    # make all times aware and default them to the latest interval
    if date_min and not is_aware(date_min):
        date_min = date_min.astimezone(network.get_fixed_offset())

    if date_max and not is_aware(date_max):
        date_max = date_max.astimezone(network.get_fixed_offset())

    if not date_max:
        date_max = latest_network_interval

    # if specified a period
    if period:
        date_max = latest_network_interval
        date_min = latest_network_interval - period

    time_series = OpennemExportSeries(start=date_min, end=date_max, network=network, interval=interval, period=period)

    return time_series
