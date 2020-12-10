import re
from logging import Filter
from typing import Optional

import yaml

from opennem.core.loader import load_data

DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "opennem": {
            "level": "DEBUG",
        },
        "scrapy": {
            "level": "ERROR",
        },
        "twisted": {
            "level": "ERROR",
        },
    },
}


class SettingsNotFound(Exception):
    pass


def load_logging_config(
    filename: str = "logging.yml", fail_silent: bool = True
) -> Optional[dict]:
    """"""

    settings_file_content = load_data(filename, from_settings=True)

    if not settings_file_content:
        if fail_silent:
            return None

        raise SettingsNotFound(
            "Not a valid logging settings file: {}".format(filename)
        )

    config_data = yaml.safe_load(settings_file_content)

    return config_data


LOGGING_CONFIG = load_logging_config()

class ItemMessageFilter(Filter):
    def filter(self, record):
        # The message that logs the item actually has raw % operators in it,
        # which Scrapy presumably formats later on
        match = re.search(
            r"(Scraped from %\(src\)s)\n%\(item\)s", record.msg
        )
        if match:
            # Make the message everything but the item itself
            record.msg = match.group(1)
        # Don't actually want to filter out this record, so always return 1
        return 1
