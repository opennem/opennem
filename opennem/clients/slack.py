""" Module to send slack messages """
import dataclasses
import logging
import sys

import requests
from validators import ValidationFailure
from validators.url import url as valid_url

from opennem.settings import settings
from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger(__name__)

REQ_HEADERS = {"User-Agent": get_random_agent(), "Content-type": "application/json"}


@dataclasses.dataclass
class SlackMessageBlockMarkdown:
    text: str
    type: str = dataclasses.field(default="mrkdwn")


@dataclasses.dataclass
class SlackMessageBlockImage:
    image_url: str
    alt_text: str
    type: str = dataclasses.field(default="image")


@dataclasses.dataclass
class SlackMessageBlock:
    text: SlackMessageBlockMarkdown | None
    accessory: SlackMessageBlockImage | None
    block_id: str = dataclasses.field(default="")
    type: str = dataclasses.field(default="section")


@dataclasses.dataclass
class SlackMessage:
    """Slack message block"""

    blocks: list[SlackMessageBlock | SlackMessageBlockImage]
    text: str = dataclasses.field(default="")


def _slack_tag_list(user_list: list[str]) -> str:
    """List of slack usernames to alert to a string

    Args:
        user_list (List[str]): list of usernames

    Returns:
        str: string to tag
    """
    return " ".join([f"@{i.strip().lstrip('@')}" for i in user_list if i])


def slack_message(
    msg: str | None = None,
    text: str | None = None,
    tag_users: list[str] | None = None,
    image_url: str | None = None,
    image_alt: str | None = None,
) -> bool:
    """
    Post a slack message to the watchdog channel

    supports markdown and tagging users

    """
    if not settings.slack_notifications:
        logger.info("Slack endpoint not configured in environment")
        return False

    if not settings.slack_hook_url:
        logger.error("No slack notification endpoint configured")
        return False

    if isinstance(valid_url(settings.slack_hook_url), ValidationFailure):
        logger.error("No slack notification endpoint configured bad url")
        return False

    alert_url = settings.slack_hook_url
    tag_list = _slack_tag_list(tag_users) if tag_users else ""
    text_block: str = f"{msg} {tag_list}" if msg else ""

    # if we tag users
    if tag_list:
        text_block += f" {tag_list}"

    blocks: list[SlackMessageBlock | SlackMessageBlockImage] = []

    if image_url:
        img_block = SlackMessageBlockImage(image_url=image_url, alt_text=image_alt)
        blocks.append(img_block)

    # if we have a text block
    if text_block:
        msg_block = SlackMessageBlock(text=None, accessory=None, block_id="section_1")
        msg_block.text = SlackMessageBlockMarkdown(text=text_block)
        blocks.append(msg_block)

    logger.info(f"Sending message: {text_block} with image {image_url}")

    slack_message = SlackMessage(text=text or "", blocks=blocks)

    # as dict and exclude empty fields
    slack_body = dataclasses.asdict(slack_message, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})

    resp = requests.post(alert_url, json=slack_body)

    if resp.status_code != 200:
        logger.error(f"Error sending slack message: {resp.status_code}: {resp.text}")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("No params")
        sys.exit(1)

    msg_args = sys.argv[1:]
    slack_msg = " ".join([str(i) for i in msg_args])
    slack_return = slack_message(slack_msg, tag_users=["nik"])
