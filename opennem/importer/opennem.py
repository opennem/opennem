import os

from opennem.core import load_data_csv
from opennem.utils import logging

logger = logging.getLogger("opennem.importer")


def run_opennem_import():
    """
        Reads the OpenNEM data source

    """

    opennem_records = load_data_csv("opennem.csv")

    for opennem_record in opennem_records:
        logger.debug(opennem_record)
