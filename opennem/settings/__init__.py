"""
    settings files - read settings from env


    will read in order:

        * .env
        * .env.{environment}
        * system env
        * pydantic settings

"""


import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from opennem.settings.utils import load_env_file

from .schema import OpennemSettings

if Path(".env").is_file():
    load_dotenv()

MODULE_DIR = os.path.dirname(__file__)

ENV = os.getenv("ENV", default="development")

# settings default loader

settings: Optional[OpennemSettings] = None

_env_file = load_env_file(ENV)

# @TODO add logging
if _env_file:
    load_dotenv(dotenv_path=_env_file, override=True)

# @NOTE don't use pydantics env file support since it doesn't support multiple
settings = OpennemSettings()
