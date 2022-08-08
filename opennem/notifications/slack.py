""" Module to send slack messages """
import logging
import sys
from typing import List, Optional

import requests
from validators import ValidationFailure
from validators.url import url as valid_url

from opennem.settings import settings
from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger(__name__)

REQ_HEADERS = {"User-Agent": get_random_agent(), "Content-type": "application/json"}


def _slack_tag_list(user_list: List[str]) -> str:
    """List of slack usernames to alert to a string

    Args:
        user_list (List[str]): list of usernames

    Returns:
        str: string to tag
    """
    _tag_list = " ".join([f"@{i.strip().lstrip('@')}" for i in user_list if i])

    return _tag_list


def slack_message(msg: str, tag_users: list[str] = None) -> bool:
    """
    Post a slack message to the watchdog channel

    """
    if not settings.slack_notifications:
        logger.error("Slack endpoint not configured in environment")
        return False

    if not settings.slack_hook_url:
        logger.error("No slack notification endpoint configured")
        return False

    if isinstance(valid_url(settings.slack_hook_url), ValidationFailure):
        logger.error("No slack notification endpoint configured bad url")
        return False

    alert_url = settings.slack_hook_url
    tag_list: Optional[str] = ""

    if tag_users:
        tag_list = _slack_tag_list(tag_users)

    composed_message = f"{msg} {tag_list}"

    logger.info("Sending message: {}".format(composed_message))

    resp = requests.post(alert_url, json={"text": composed_message})

    if resp.status_code != 200:
        logger.error("Error sending slack message")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("No params")
        sys.exit(1)

    msg_args = sys.argv[1:]
    slack_msg = " ".join([str(i) for i in msg_args])
    slack_return = slack_message(slack_msg, tag_users=["nik"])
