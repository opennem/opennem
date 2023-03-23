""" OpenNEM contrab tools for timing tasks """

import logging
from collections.abc import Callable
from datetime import datetime

from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.pipelines.cron")
# from opennem.utils.dates import get_last_completed_interval_for_network


def network_interval_crontab(network: NetworkSchema, number_minutes: int = 2) -> Callable[[datetime], bool]:
    """Runs a crontab for a network interval

    :param network: NetworkSchema to check (reads number of intervals)
    :param seconds_period: Seconds period to run the crontab
    :param number_minutes: Number of minutes to run the crontab
    """

    def _network_interval_crontab(timestamp: datetime) -> bool:
        _, _, _, _, M, s, _, _, _ = timestamp.timetuple()

        if M % network.interval_size in set(range(0, number_minutes)):
            logging.debug(f"Running crontab for {network.code} at {timestamp}")
            return True

        return False

    return _network_interval_crontab
