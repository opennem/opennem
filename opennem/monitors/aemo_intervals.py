import logging
from datetime import datetime, timedelta

from opennem.monitors.aemo_wem_live_intervals import (
    get_aemo_wem_live_facility_intervals_recent_date,
)
from opennem.notifications.slack import slack_message
from opennem.schema.network import NetworkWEM
from opennem.settings import settings
from opennem.utils.dates import chop_microseconds

logger = logging.getLogger("opennem.monitors.aemo")


def aemo_wem_live_interval() -> bool:
    """
    Monitors the delay from the AEMO live scada data on the portal
    """
    network = NetworkWEM

    now_date = datetime.now().astimezone(network.get_timezone())

    live_most_recent = get_aemo_wem_live_facility_intervals_recent_date()

    live_delta = chop_microseconds(now_date - live_most_recent)

    logger.debug(
        "Live time: {},  delay: {}".format(live_most_recent, live_delta)
    )

    # @TODO move the minutes into settings
    if live_delta > timedelta(minutes=90):
        slack_message(
            "*WARNING*: AEMO Live intervals for WEM on {} curently delayed by {}\n\nAEMO feed most recent: {}".format(
                settings.env, live_delta, live_most_recent
            )
        )
        return True

    return False


if __name__ == "__main__":
    delay = aemo_wem_live_interval()
