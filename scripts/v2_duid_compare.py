#!/usr/bin/env python
"""
compare duid / fueltech with v2
"""
import csv
import logging
from pathlib import Path

from pydantic import validator

from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility
from opennem.importer.compat import map_compat_fueltech
from opennem.schema.core import BaseConfig
from opennem.settings import settings

logger = logging.getLogger("opennem.scripts.v2_duid_compare")


class CSVRecord(BaseConfig):
    facility_code: str
    network_region: str
    fueltech_id: str

    _validate_fueltech = validator("fueltech_id", pre=True)(map_compat_fueltech)


def run() -> None:
    comp_file = Path(__file__).parent / "v2_duid_dump.csv"
    csvrecords = []

    with comp_file.open() as fh:
        fieldnames = fh.readline().strip().split(",")
        csvreader = csv.DictReader(fh, fieldnames=fieldnames)
        csvrecords = list(csvreader)

    records = [CSVRecord(**i) for i in csvrecords if i["facility_code"] != "None"]

    session = SessionLocal()

    for rec in records:
        facility: Facility = (
            session.query(Facility)
            .filter_by(network_region=rec.network_region)
            .filter_by(code=rec.facility_code)
            .one_or_none()
        )

        if not facility:
            logger.debug(
                "Could not find facility {} with fueltech {}".format(
                    rec.facility_code, rec.fueltech_id
                )
            )
            continue

        if facility.fueltech_id != rec.fueltech_id:
            logger.info(
                "Fueltech mismatch for {}: v2 is {} and v3 is {}".format(
                    rec.facility_code, rec.fueltech_id, facility.fueltech_id
                )
            )


if __name__ == "__main__":
    run()
