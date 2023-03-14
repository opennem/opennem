""""
Module to check AEMO REL and GI sheet updates and produce an update or report on changes
"""

import logging
from dataclasses import dataclass

from opennem.core.parsers.aemo.gi import AEMOGIRecord, download_and_parse_aemo_gi_file
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility

logger = logging.getLogger("opennem.workers.aemo_data_update")


class OpennemWorkerAEMODataUpdateException(Exception):
    """Exception raised in this module"""

    pass


@dataclass
class AEMODataUpdateResult:
    """Result of the AEMO data update"""

    new_facilities: list[AEMOGIRecord]
    updated_facilities: list[AEMOGIRecord]
    unchanged_facilities: list[AEMOGIRecord]

    def __init__(self) -> None:
        self.new_facilities = []
        self.updated_facilities = []
        self.unchanged_facilities = []

    def __repr__(self) -> str:
        return (
            f"AEMODataUpdateResult(new={len(self.new_facilities)}, updated={len(self.updated_facilities)},"
            f"unchanged={len(self.unchanged_facilities)})"
        )


def facility_matcher(records: list[AEMOGIRecord], run_update: bool = False) -> AEMODataUpdateResult:
    """This will match facilities in the database to the AEMO GI spreadsheet"""

    update_result = AEMODataUpdateResult()

    with SessionLocal() as sess:
        for gi_record in records:
            if not gi_record.duid:
                update_result.new_facilities.append(gi_record)
                continue

            gi_db: Facility | None = sess.query(Facility).filter(Facility.code == gi_record.duid).one_or_none()

            if not gi_db:
                logger.info(f"MISS: {gi_record.duid} {gi_record.name}")
                update_result.new_facilities.append(gi_record)
                continue

            if (gi_db.status_id != gi_record.status_id) or (gi_db.capacity_registered != gi_record.capacity_registered):
                logger.info(
                    f"STATUS: {gi_record.duid} {gi_record.name_network} "
                    f"({gi_db.status_id} => {gi_record.status_id}, {gi_db.capacity_registered} => {gi_record.capacity_registered}"
                )
                update_result.updated_facilities.append(gi_record)

                # if we pass the parameter then update the db record
                if run_update:
                    if gi_record.status_id:
                        gi_db.status_id = gi_record.status_id

                    if gi_record.capacity_registered:
                        gi_db.capacity_registered = gi_record.capacity_registered

                    sess.add(gi_db)
                    sess.commit()

                continue

            logger.info(f"HIT {gi_record.duid} {gi_record.name} - currently {gi_db.status_id} change to => {gi_record.status_id}")
            update_result.unchanged_facilities.append(gi_record)

    return update_result


def run_aemo_gi_data_update(run_update: bool = False) -> None:
    """Runs the AEMO GI Data update process. Will update facility capacity info and alert on new facilities"""
    records = download_and_parse_aemo_gi_file()
    record_update_set = facility_matcher(records, run_update=run_update)
    logger.info(f"Completed AEMO GI data update: {record_update_set}")


# debug entry point
if __name__ == "__main__":
    run_aemo_gi_data_update()
