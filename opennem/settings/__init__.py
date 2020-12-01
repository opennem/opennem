"""
    settings files - read settings from env


    will read in order:

        * .env
        * .env.{environment}
        * system env
        * pydantic settings

"""
import logging
import logging.config
import os

from dotenv import load_dotenv

from opennem.settings.log import LOGGING_CONFIG
from opennem.settings.utils import load_env_file
from opennem.utils.proc import running_as_scrapy

from .schema import OpennemSettings

MODULE_DIR = os.path.dirname(__file__)

ENV = os.getenv("ENV", default="development")

env_files = load_env_file(ENV)

# Load the env files
# @TODO add logging
for _env_file in env_files:
    load_dotenv(dotenv_path=_env_file, override=True)

# @NOTE don't use pydantics env file support since it doesn't support multiple
settings: OpennemSettings = OpennemSettings()


# skip if the current cli is scrapy
if LOGGING_CONFIG and not running_as_scrapy():
    # don't mess with scrapy logging

    logging.config.dictConfig(LOGGING_CONFIG)

    log_level = logging.getLevelName(settings.log_level)

    # set root log level
    logging.root.setLevel(log_level)

    opennem_logger = logging.getLogger("opennem")
    opennem_logger.setLevel(log_level)
