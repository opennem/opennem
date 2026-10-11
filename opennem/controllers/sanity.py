"""
Takes Sanity webhook responses and parses into structured format for persistance and updates
"""

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

    Returns None if no facility is found — this is expected when the webhook fires for a
    unit that isn't linked to a facility in our DB yet (e.g. a new/draft unit in the CMS).
    """
    async with get_read_session() as session:
        query = select(Facility).join(Unit, Facility.id == Unit.station_id).where(Unit.cms_id == cms_id)
        result = await session.execute(query)
        record = result.scalars().one_or_none()
        if record:
            return record.cms_id
        return None


async def sync_sanity_record(record_type: str, cms_id: str) -> None:
    """Sync a record changed in sanity into the database and re-export facilities.

    Runs in the ARQ worker (task_sanity_webhook), deferred after the webhook since sanity is
    eventually consistent.
    """
    record_type = record_type.lower()
    cms_id = cms_id.strip()

    if record_type in ["facility"]:
        await update_database_facilities_from_cms(cms_id=cms_id, send_slack=False)
    elif record_type == "unit":
        facility_cms_id = await get_facility_cms_id_by_unit_cms_id(cms_id)
        if facility_cms_id is None:
            logger.warning(f"No facility found for unit cms_id: {cms_id} — skipping sanity sync")
            return
        await update_database_facilities_from_cms(cms_id=facility_cms_id, send_slack=False)
    else:
        logger.warning(f"Unhandled record type: {record_type}")

    await export_facilities_static()
