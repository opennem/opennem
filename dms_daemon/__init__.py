import os

import yaml

MODULE_DIR = os.path.dirname(__file__)

with open(os.path.join(MODULE_DIR, "config.yml"), "r") as ymlfile:
    CONFIG = yaml.safe_load(ymlfile)
