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
        "twisted": {
            "level": "ERROR",
        },
    },
}


class SettingsNotFound(Exception):
    pass


def load_logging_config(filename: str = "logging.yml", fail_silent: bool = True) -> Optional[dict]:
    """Load logging configuration from yml file"""

    settings_file_content = load_data(filename, from_settings=True)

    if not settings_file_content:
        if fail_silent:
            return None

        raise SettingsNotFound("Not a valid logging settings file: {}".format(filename))

    config_data = yaml.safe_load(settings_file_content)

    return config_data


LOGGING_CONFIG = load_logging_config()
