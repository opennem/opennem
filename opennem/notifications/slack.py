import logging
import sys

import requests
from validators import ValidationFailure
from validators.url import url as valid_url

from opennem.settings import settings
from opennem.settings.scrapy import USER_AGENT

logger = logging.getLogger(__name__)

REQ_HEADERS = {"User-Agent": USER_AGENT, "Content-type": "application/json"}


def slack_message(msg: str) -> bool:
    """
    Post a slack message to the watchdog channel

    """
    if not settings.slack_notifications:
        return False

    if not settings.slack_hook_url:
        logger.error("No slack notification endpoint configured")
        return False

    if isinstance(valid_url(settings.slack_hook_url), ValidationFailure):
        logger.error("No slack notification endpoint configured bad url")
        return False

    alert_url = settings.slack_hook_url

    resp = requests.post(alert_url, json={"text": msg})

    if resp.status_code != 200:
        logger.error("Error sending slack message")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    msg_args = sys.argv[1:]
    slack_msg = " ".join([str(i) for i in msg_args])
    slack_message(slack_msg)
