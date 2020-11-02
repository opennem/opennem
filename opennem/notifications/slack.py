import logging

import requests

from opennem.settings import settings
from opennem.settings.scrapy import USER_AGENT

logger = logging.getLogger(__name__)

REQ_HEADERS = {"User-Agent": USER_AGENT, "Content-type": "application/json"}


def slack_message(msg: str) -> bool:
    """
        Post a slack message to the watchdog channel

    """
    resp = requests.post(settings.slack_hook_url, json={"text": msg})

    if resp.status_code != 200:
        logger.error("Error sending slack message")
        return False

    return True
