"""
    settings files - read settings from env and from config.yml



"""


import os

from .schema import OpennemSettings

MODULE_DIR = os.path.dirname(__file__)

ENV = os.getenv("ENV", default="development")

MYSQL_HOST_URL = os.getenv("MYSQL_HOST_URL", default=False)

# settings default loader

settings = None

if ENV == "development":
    settings = OpennemSettings()
else:
    if os.path.isfile(".env.production"):
        settings = OpennemSettings(_env_file=".env.production")
    else:
        settings = OpennemSettings()
