"""
OpenNEM Monitor Facility First Seen

Scheduled process that checks for new DUIDs found in generation data
and alerts about them

"""
import logging
import re
from datetime import datetime

from sqlalchemy import text

from opennem.clients.slack import slack_message
from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.monitors.facility_seen")


class FacilitySeen(BaseConfig):
    code: str
    network_id: str
    seen_first: datetime | None
    seen_last: datetime | None
    generated: float | None


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

_dr_duids_match = re.compile(r"DR[VX]\w{3}\d{2}")


def ignored_duids(fac_records: list[FacilitySeen]) -> list[FacilitySeen]:
    """Filters out ignored records like dummy generators"""

    def fac_is_ignored(fac: FacilitySeen) -> FacilitySeen | None:
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

        # ignore drv/drx duids
        if fac.network_id == "NEM" and re.match(_dr_duids_match, fac.code):
            return None

        return fac

    fac_filtered = list(filter(fac_is_ignored, fac_records))

    return fac_filtered


def get_facility_first_seen(period: str) -> list[FacilitySeen]:
    """Run this and it'll check if there are new facilities in
    scada data and let you know which ones

    The query can be an expensive one so don't run to often.
    """

    engine = get_database_engine()

    query = text(
        """
        select
            fs.facility_code,
            fs.network_id,
            sum(fs.generated) as generated
        from facility_scada fs
        where
            fs.facility_code not in (select distinct code from facility)
            and fs.trading_interval > now() - interval :period
        group by 1, 2
    """
    )

    with engine.begin() as c:
        logger.debug(query)
        row = list(c.execute(query, {"period": period}))

    records: list[FacilitySeen] = [FacilitySeen(code=r[0], network_id=r[1], generated=r[2]) for r in row]

    return records


def facility_first_seen_check() -> list[FacilitySeen]:
    """Find new DUIDs and alert on them"""
    facs = get_facility_first_seen("7 days")

    facs_filtered = ignored_duids(facs)

    facs_out = []

    for fac in facs_filtered:
        msg = f"Found new facility on network {fac.network_id} with DUID: {fac.code}. Generated: {fac.generated}MW"
        slack_message(msg)
        logger.info(msg)
        facs_out.append(fac)

    return facs_out


def facility_unmapped_all(filter: bool = True) -> list[FacilitySeen]:
    """Find new DUIDs and alert on them"""
    facs = get_facility_first_seen("7 days")

    if filter:
        facs = ignored_duids(facs)

    facs = sorted(facs, key=lambda x: (x.network_id, x.code))

    return facs


# debug entry point
if __name__ == "__main__":
    seen_facilities = facility_unmapped_all()

    for f in seen_facilities:
        logger.info(f"Unmapped: {f.network_id} {f.code} {f.generated}")
