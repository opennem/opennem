"""
    Sets up logging for the main opennem project


"""


from logging import config

from opennem.settings.log import load_logging_config

if logging_config := load_logging_config():
    config.dictConfig(logging_config)
