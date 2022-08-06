import logging
from datetime import datetime, timedelta

from opennem.core.networks import network_from_network_code
from opennem.notifications.slack import slack_message
from opennem.settings import settings
from opennem.utils.dates import chop_delta_microseconds, parse_date
from opennem.utils.http import http

logger = logging.getLogger("opennem.monitors.opennem")


def get_slack_admin_alert_string() -> str | None:
    """Get the part of the slack message that alerts admin"""
    if not settings.slack_admin_alert:
        logger.warning("Have no slack_admin_alert set")
        return None

    return " @".join(settings.slack_admin_alert)


def check_opennem_interval_delays(network_code: str) -> bool:
    """Runs periodically and alerts if there is a current delay in output of power intervals"""
    network = network_from_network_code(network_code)

    env = ""

    if settings.debug:
        env = ".dev"

    url = f"https://data{env}.opennem.org.au/v3/stats/au/{network.code}/power/7d.json"

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

    now_date = datetime.now().astimezone(network.get_timezone())  # type: ignore

    time_delta = chop_delta_microseconds(now_date - history_date)

    logger.debug("Live time: {},  delay: {}".format(history_date, time_delta))

    # get the slack admin alert string
    slack_admin_alert = get_slack_admin_alert_string()

    if time_delta > timedelta(minutes=settings.monitor_interval_alert_threshold or 60):
        slack_message(
            f"*WARNING*: OpenNEM {network.code} interval delay on {settings.env} currently: {time_delta}. {slack_admin_alert}\n"
        )

    return True


if __name__ == "__main__":
    for network_code in ["NEM", "WEM"]:
        check_opennem_interval_delays(network_code)
