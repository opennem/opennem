"""
    Sets up logging for the main opennem project


"""

from logging import config

from opennem.settings.log import get_logging_config

logging_config = get_logging_config()
config.dictConfig(logging_config)
