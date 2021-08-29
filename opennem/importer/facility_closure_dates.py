import logging
from typing import Optional

from opennem.core.parsers.aemo.facility_closures import parse_aemo_closures_xls
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility

logger = logging.getLogger("opennem.importer.facility_closure_dates")


def import_aemo_facility_closure_dates() -> bool:
    closure_records = parse_aemo_closures_xls()
    session = SessionLocal()

    for record in closure_records:
        facility: Optional[Facility] = (
            session.query(Facility)
            .filter_by(network_id="NEM")
            .filter_by(code=record.duid)
            .one_or_none()
        )

        if not facility:
            logger.info("Could not find facility {} - {}".format(record.duid, record.station_name))
            continue

        facility.expected_closure_date = record.expected_closure_date
        facility.expected_closure_year = record.expected_closure_year

        session.add(facility)

    session.commit()

    return True


if __name__ == "__main__":
    import_aemo_facility_closure_dates()
