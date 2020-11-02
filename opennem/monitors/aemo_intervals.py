import logging
from datetime import datetime, timedelta

import requests

from opennem.core.networks import network_from_network_code
from opennem.monitors.aemo_wem_live_intervals import (
    get_aemo_wem_live_facility_intervals_recent_date,
)
from opennem.notifications.slack import slack_message
from opennem.utils.dates import parse_date

logger = logging.getLogger(__name__)


def get_wem_interval_delay() -> bool:
    resp = requests.get("https://data.opennem.org.au/power/wem.json")

    if resp.status_code != 200:
        logger.error("Error retrieving wem power")
        return False

    resp_json = resp.json()

    if "data" not in resp_json:
        logger.error("Error retrieving wem power: malformed response")
        return False

    data = resp_json["data"]
    network_code = resp_json["code"]

    network = network_from_network_code(network_code)

    fueltech_data = data.pop()

    history_end_date = fueltech_data["history"]["last"]

    history_date = parse_date(history_end_date, dayfirst=False)
    now_date = datetime.now().astimezone(network.get_timezone())

    live_most_recent = get_aemo_wem_live_facility_intervals_recent_date()

    time_delta = now_date - history_date

    if time_delta > timedelta(hours=3):
        slack_message(
            "WARNING: WEM live interval delay currently: {}\n\nFeed time: {}\nCurrent time: {}\n".format(
                time_delta, history_date, now_date
            )
        )

    live_delta = now_date - live_most_recent

    if live_delta > timedelta(minutes=90):
        slack_message(
            "AEMO Live intervals for WEM curently delayed by {}\n\nAEMO feed most recent: {}".format(
                live_delta, live_most_recent
            )
        )


if __name__ == "__main__":
    delay = get_wem_interval_delay()
