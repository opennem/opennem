from typing import Optional

import yaml

from opennem.core.loader import load_data


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


def get_logging_config():
    return LOGGING_CONFIG


LOGGING_CONFIG = load_logging_config()
