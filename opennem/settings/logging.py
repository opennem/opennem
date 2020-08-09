import os
from typing import Optional

import yaml

LOGGING_CONFIG = {}


SETTINGS_DIR = os.path.realpath(os.path.dirname(__file__))


class SettingsNotFound(Exception):
    pass


def load_logging_config(
    filename: str = "logging.yml", fail_silent: bool = True
) -> Optional[dict]:
    """


    """

    settings_filepath = os.path.realpath(os.path.join(SETTINGS_DIR, filename))

    if not os.path.isfile(settings_filepath):
        if fail_silent:
            return dict()

        raise SettingsNotFound(
            "Not a valid logging settings file: {}".format(settings_filepath)
        )

    with open(settings_filepath, "rt") as f:
        config_data = yaml.safe_load(f.read())

    return config_data


def get_logging_config():
    return LOGGING_CONFIG


LOGGING_CONFIG = load_logging_config()
