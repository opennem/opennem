import os

from opennem.core import load_data_csv
from opennem.db.models.opennem import Facility, Station
from opennem.utils.log_config import logging

logger = logging.getLogger("opennem.importer")

RECORD_MODEL_MAP = {
    "STATION": Station,
    "FACILITY": Facility,
}


def run_opennem_import():
    """
        Reads the OpenNEM data source

    """

    opennem_records = load_data_csv("opennem.csv")

    for rec in opennem_records:
        logger.debug(rec)

        if not "record_type" in rec:
            raise Exception("Invalid CSV: No record_type")

        record_type = rec["record_type"]

        if not record_type in RECORD_MODEL_MAP:
            raise Exception(
                "Invalid record type: {} is not a valid record type".format(
                    record_type
                )
            )

        record_model = RECORD_MODEL_MAP[record_type]
