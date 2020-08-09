"""
    Sets up logging for the main opennem project


"""

import logging
from logging import config

from opennem.settings import get_logging_config

logging_config = get_logging_config()
config.dictConfig(logging_config)
