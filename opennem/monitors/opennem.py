import logging
from datetime import datetime, timedelta

from opennem.core.networks import network_from_network_code
from opennem.notifications.slack import slack_message
from opennem.settings import settings
from opennem.utils.dates import chop_microseconds, parse_date
from opennem.utils.http import http

logger = logging.getLogger("opennem.monitors.opennem")


def check_opennem_interval_delays(network_code: str) -> bool:
    network = network_from_network_code(network_code)

    if settings.debug:
        env = ".dev"

    url = (
        f"https://data.opennem.org.au/v3/stats/au/{network.code}/power/7d.json"
        f"https://data{env}.opennem.org.au/v3/stats/au/{network.code}/power/7d.json"
    )

    resp = http.get(url)

    if resp.status_code != 200 or not resp.ok:
        logger.error("Error retrieving: {}".format(url))
        return False

    resp_json = resp.json()

    if "data" not in resp_json:
        logger.error("Error retrieving wem power: malformed response")
        return False

    data = resp_json["data"]

    fueltech_data = data.pop()

    history_end_date = fueltech_data["history"]["last"]

    history_date = parse_date(history_end_date, dayfirst=False)

    if not history_date:
        logger.error("Could not read history date for opennem interval monitor")
        return False

    now_date = datetime.now().astimezone(network.get_timezone())

    time_delta = chop_microseconds(now_date - history_date)

    logger.debug("Live time: {},  delay: {}".format(history_date, time_delta))

    if time_delta > timedelta(hours=3):
        slack_message(
            "*WARNING*: OpenNEM {} interval delay on {} currently: {}\n".format(
                network.code, settings.env, time_delta
            )
        )

    return True


if __name__ == "__main__":
    for network_code in ["NEM", "WEM"]:
        check_opennem_interval_delays(network_code)
