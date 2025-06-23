"""
OpenNEM Monitor Facility First Seen

Scheduled process that checks for new DUIDs found in generation data
and alerts about them

"""

import logging
from datetime import datetime

from sqlalchemy import text

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db import db_connect
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.monitors.facility_seen")


class FacilitySeen(BaseConfig):
    code: str
    network_id: str
    seen_first: datetime | None = None
    seen_last: datetime | None = None
    generated: float | None = None


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

        # ignore the Point Henry Smelter loads
        if fac.network_id == "NEM" and fac.code.startswith("PTH0"):
            return None

        # ignore demo VPPs
        if fac.network_id == "NEM" and fac.code in NEM_VPPS:
            return None

        # ignore demand response DUIDs
        if fac.network_id == "NEM" and fac.code.startswith("DRX"):
            return None

        return fac

    fac_filtered = list(filter(fac_is_ignored, fac_records))

    return fac_filtered


async def get_facility_first_seen(period: str) -> list[FacilitySeen]:
    """Run this and it'll check if there are new facilities in
    scada data and let you know which ones

    The query can be an expensive one so don't run to often.
    """

    engine = db_connect()

    query = text(
        f"""
        select
            fs.facility_code,
            fs.network_id,
            round(abs(sum(fs.generated)), 2) as generated
        from facility_scada fs
        where
            fs.facility_code not in (select distinct code from units)
            and fs.interval > now() - interval '{period}'
        group by 1, 2
        """
    )

    async with engine.begin() as conn:
        logger.debug(query)
        row = await conn.execute(query)

    records: list[FacilitySeen] = [FacilitySeen(code=r[0], network_id=r[1], generated=r[2]) for r in row]

    return records


async def facility_first_seen_check(
    only_generation: bool = True, filter_ignored_duids: bool = True, send_slack: bool = False
) -> list[FacilitySeen]:
    """Find new DUIDs and alert on them

    Args:
        only_generation (bool, optional): only return those with generation data in scada. Defaults to True.
        filter_ignored_duids (bool, optional): use the filter function to filter out supurfulous DUIDs. Defaults to False.

    Returns:
        list[FacilitySeen]: a list of FacilitySeen models
    """
    facs = await get_facility_first_seen("7 days")

    if filter_ignored_duids:
        facs = ignored_duids(facs)

    facs_out = []

    for fac in facs:
        if only_generation and fac.generated is not None and fac.generated > 0:
            generated_out = round(fac.generated / 6, 2)  # noqa: F841

            msg = (
                f"[{settings.env.upper()}] Found new facility on network {fac.network_id} with DUID: "
                f"{fac.code}. Generated: {generated_out}MW"
            )

            if send_slack:
                await slack_message(
                    webhook_url=settings.slack_hook_new_facilities, tag_users=settings.slack_admin_alert, message=msg
                )
                logger.debug(msg)

            facs_out.append(fac)
        else:
            msg = (
                f"[{settings.env.upper()}] Found new facility on network {fac.network_id} with DUID: "
                f"{fac.code}. No generation data"
            )
            logger.debug(msg)
            facs_out.append(fac)

    return sorted(facs_out, key=lambda x: x.code, reverse=False)


# debug entry point
if __name__ == "__main__":
    import asyncio

    asyncio.run(facility_first_seen_check(send_slack=True, only_generation=True))
