"""
Controller to store and persist WEMDE data

"""

import logging

from opennem.schema.facility import SchemaFacilityScada

logger = logging.getLogger("opennem.controllers.wemde")


async def store_wemde_facility_intervals(records: list[SchemaFacilityScada]) -> None:
    """Persist WEMDE facility intervals"""
    pass
