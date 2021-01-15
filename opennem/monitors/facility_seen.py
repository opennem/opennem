"""
OpenNEM Monitor Facility First Seen

Scheduled process that checks for new DUIDs found in generation data
and alerts about them

"""
import logging
from datetime import datetime
from typing import List, Optional

from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig

# from opennem.notifications.slack import slack_message

logger = logging.getLogger("opennem.monitors.facility_seen")


class FacilitySeen(BaseConfig):
    code: str
    network_id: str
    seen_first: Optional[datetime]
    seen_last: Optional[datetime]


def get_facility_first_seen() -> List[FacilitySeen]:
    """Run this and it'll check if there are new facilities in
    scada data and let you know which ones

    The query can be an expensive one so don't run to often.
    """

    engine = get_database_engine()

    __query = """
        select
            distinct fs.facility_code,
            fs.network_id
        from facility_scada fs
        where
            fs.facility_code not in (select distinct code from facility);
    """

    with engine.connect() as c:
        logger.debug(__query)
        row = list(c.execute(__query))

    records: List[FacilitySeen] = [FacilitySeen(code=r[0], network_id=r[1]) for r in row]

    return records


def facility_first_seen_check() -> None:
    return None


if __name__ == "__main__":
    facility_first_seen_check()
