"""
OpenNEM Monitor Facility First Seen

Scheduled process that checks for new DUIDs found in generation data
and alerts about them

"""
import logging
from datetime import datetime
from typing import List, Optional

from opennem.db import get_database_engine
from opennem.notifications.slack import slack_message
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.monitors.facility_seen")


class FacilitySeen(BaseConfig):
    code: str
    network_id: str
    seen_first: Optional[datetime]
    seen_last: Optional[datetime]


# This is a list of NEM VPP's that aren't mapped yet
# they're all currently in demo state
# info at : https://arena.gov.au/assets/2021/02/aemo-virtual-power-plant-demonstrations-report-3.pdf
NEM_VPPS = [
    "VSSEL1V1",
    "VSSAEV1",
    "VSSSE1V1",
    "VSNSN1V1",
    "VSSSH1S1",
    "VSVEL2S1",
    "VSNEL2S1",
    "VSQHT1V1",
]


def ignored_duids(fac_records: List[FacilitySeen]) -> List[FacilitySeen]:
    """Filters out ignored records like dummy generators"""

    def fac_is_ignored(fac: FacilitySeen) -> Optional[FacilitySeen]:

        # dummy generators for AEMO NEM
        if fac.network_id == "NEM" and fac.code.startswith("DG_"):
            return None

        # reserve trader for AEMO NEM
        if fac.network_id == "NEM" and fac.code.startswith("RT_"):
            return None

        # V1 are possible FCAS providers for AEMO NEM
        if fac.network_id == "NEM" and fac.code.endswith("V1"):
            return None

        # loads for AEMO NEM
        if fac.network_id == "NEM" and fac.code.endswith("L1"):
            return None

        # ignore the Point Henry Smelter loads
        if fac.network_id == "NEM" and fac.code.startswith("PTH0"):
            return None

        # ignore demo VPPs
        if fac.network_id == "NEM" and fac.code in NEM_VPPS:
            return None

        return fac

    fac_filtered = list(filter(fac_is_ignored, fac_records))

    return fac_filtered


def get_facility_first_seen(period: Optional[str] = None) -> List[FacilitySeen]:
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
            fs.facility_code not in (select distinct code from facility)
            {period_query}
    """

    period_query = f"and fs.trading_interval > now() - interval '{period}'" if period else ""

    query = __query.format(period_query=period_query)

    with engine.connect() as c:
        logger.debug(query)
        row = list(c.execute(query))

    records: List[FacilitySeen] = [FacilitySeen(code=r[0], network_id=r[1]) for r in row]

    return records


def facility_first_seen_check() -> List[FacilitySeen]:
    """Find new DUIDs and alert on them"""
    facs = get_facility_first_seen("3 days")

    facs_filtered = ignored_duids(facs)

    facs_out = []

    for fac in facs_filtered:
        msg = "Found new facility on network {} with DUID: {}".format(fac.network_id, fac.code)
        slack_message(msg)
        logger.info(msg)
        facs_out.append(fac)

    return facs_out


def facility_unmapped_all(filter: bool = True) -> List[FacilitySeen]:
    """Find new DUIDs and alert on them"""
    facs = get_facility_first_seen("3 days")

    if filter:
        facs = ignored_duids(facs)

    return facs


# debug entry point
if __name__ == "__main__":
    seen_facilities = facility_first_seen_check()
