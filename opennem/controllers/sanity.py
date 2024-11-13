"""
Takes Sanity webhook responses and parses into structured format for persistance and updates
"""

import logging

from portabletext_html import PortableTextRenderer
from sqlalchemy import select

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.cms.importer import create_or_update_database_facility
from opennem.db import get_write_session
from opennem.db.models.opennem import Facility, Unit
from opennem.exporter.facilities import export_facilities_static
from opennem.schema.facility import FacilitySchema
from opennem.schema.unit import UnitSchema

logger = logging.getLogger("opennem.controllers.sanity")


async def parse_sanity_webhook_request(request: dict) -> None:
    """Parse a sanity webhook response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type field present. Fields are {" + ", ".join(request.keys()) + "}")

    record_type: str = request["_type"].lower()

    if record_type in ["facility"]:
        facility = sanity_parse_facility(request)
        await create_or_update_database_facility(facility)
    elif record_type == "unit":
        unit = sanity_parse_unit(request)
        await persist_unit_record(unit)
    else:
        logger.warning(f"Unhandled record type: {record_type}")

    await export_facilities_static()


def sanity_parse_facility(request: dict) -> FacilitySchema:
    """Parse a facility response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type record present")

    if request["_type"] != "facility":
        raise Exception("Invalid request: not a facility record")

    if request.get("description") and isinstance(request["description"], list):
        rendered_description = ""
        for block in request["description"]:
            rendered_description += PortableTextRenderer(block).render()
        if rendered_description:
            request["description"] = rendered_description

    if request.get("_id"):
        request["id"] = request["_id"]

    if request.get("_updatedAt"):
        request["updated_at"] = request["_updatedAt"]

    cms_facility = FacilitySchema(**request)

    return cms_facility


def sanity_parse_unit(request: dict) -> UnitSchema:
    """Parse a facility response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type record present")

    if request["_type"] != "unit":
        raise Exception("Invalid request: not a unit record")

    cms_unit = UnitSchema(**request)

    return cms_unit


async def persist_facility_record(facility: FacilitySchema) -> None:
    """Persist a facility record to the Station table in database"""

    async with get_write_session() as session:
        facility_db = (await session.execute(select(Facility).filter(Facility.code == facility.code))).scalars().one_or_none()

        if not facility_db:
            facility_db = Facility(**facility)

        facility_db.approved = True
        facility_db.name = facility.name
        facility_db.website_url = facility.website
        facility_db.wikipedia_url = facility.wikipedia

        session.add(facility_db)
        await session.commit()


async def persist_unit_record(unit: UnitSchema) -> None:
    """Persit the unit record to facility table"""

    async with get_write_session() as session:
        unit_db = (await session.execute(select(Unit).filter(Unit.code == unit.code))).scalars().one_or_none()

        if not unit_db:
            unit_db = Unit(
                code=unit.code,
                dispatch_type=unit.dispatch_type.value,
                status_id=unit.status_id.value,
                fueltech_id=unit.fueltech_id.value,
                capacity_registered=unit.capacity_registered,
                emissions_factor_co2=unit.emissions_factor_co2,
                approved=True,
            )
        else:
            unit_db.approved = True
            unit_db.dispatch_type = unit.dispatch_type.value
            unit_db.fueltech_id = unit.fueltech_id.value
            unit_db.status_id = unit.status_id.value
            unit_db.capacity_registered = unit.capacity_registered
            unit_db.emissions_factor_co2 = unit.emissions_factor_co2

        session.add(unit_db)

        message = f"Persisted unit {unit.code} - {unit.fueltech_id} - {unit.status_id} - {unit.dispatch_type.value}"

        logger.info(message)

        await session.commit()

    await slack_message(webhook_url=settings.slack_hook_new_facilities, message=message)
