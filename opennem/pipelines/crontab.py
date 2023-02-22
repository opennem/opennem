""" OpenNEM contrab tools for timing tasks """

from collections.abc import Callable
from datetime import datetime

from opennem.schema.network import NetworkSchema

# from opennem.utils.dates import get_last_completed_interval_for_network


def network_interval_crontab(
    network: NetworkSchema, seconds_period: int = 10, number_minutes: int = 2
) -> Callable[[datetime], bool]:
    """Runs a crontab for a network interval

    :param network: NetworkSchema to check (reads number of intervals)
    :param seconds_period: Seconds period to run the crontab
    :param number_minutes: Number of minutes to run the crontab
    """

    def _network_interval_crontab(timestamp: datetime) -> bool:
        _, _, _, _, M, s, _, _, _ = timestamp.timetuple()

        if s % seconds_period == 0 and M % network.interval_size in set(range(0, number_minutes)):
            return True

        return False

    return _network_interval_crontab
