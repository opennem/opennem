import logging
from datetime import datetime, timedelta

import requests

from opennem.core.networks import network_from_network_code
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

    time_delta = now_date - history_date

    if time_delta > timedelta(hours=3):
        slack_message(
            "WARNING: WEM live interval delay currently: {}\n\nFeed time: {}\nCurrent time: {}\n".format(
                time_delta, history_date, now_date
            )
        )


if __name__ == "__main__":
    delay = get_wem_interval_delay()
