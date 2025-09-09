"""
Takes Sanity webhook responses and parses into structured format for persistance and updates
"""

import asyncio
import logging

from sqlalchemy import select

from opennem.cms.importer import update_database_facilities_from_cms
from opennem.db import get_read_session
from opennem.db.models.opennem import Facility, Unit
from opennem.exporter.facilities import export_facilities_static

logger = logging.getLogger("opennem.controllers.sanity")


async def get_facility_cms_id_by_unit_cms_id(cms_id: str) -> str | None:
    """Gets a facility code by a unit cms_id

    This is used in the sanity webhook when a unit is updated. We need the parent facility
    code so we can run the job to sync it.
    """
    async with get_read_session() as session:
        query = select(Facility).join(Unit, Facility.id == Unit.station_id).where(Unit.cms_id == cms_id)
        result = await session.execute(query)
        record = result.scalars().one_or_none()
        if record:
            return record.cms_id
        raise Exception(f"No facility found for unit cms_id: {cms_id}")


async def parse_sanity_webhook_request(request: dict) -> None:
    """Parse a sanity webhook response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type field present. Fields are {" + ", ".join(request.keys()) + "}")

    if "_id" not in request:
        raise Exception("Invalid request: no _id field present. Fields are {" + ", ".join(request.keys()) + "}")

    # since sanity is eventually consistent, we're going to put in a silly pause here to wait for it.
    # eventually this should be a background worker task
    await asyncio.sleep(60)

    record_type: str = request["_type"].lower()
    cms_id = request["_id"].strip()

    logger.debug(request)

    if record_type in ["facility"]:
        await update_database_facilities_from_cms(cms_id=cms_id, send_slack=False)
    elif record_type == "unit":
        facility_cms_id = await get_facility_cms_id_by_unit_cms_id(cms_id)
        await update_database_facilities_from_cms(cms_id=facility_cms_id, send_slack=False)
    else:
        logger.warning(f"Unhandled record type: {record_type}")

    await export_facilities_static()
