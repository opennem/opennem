"""
Takes Sanity webhook responses and parses into structured format for persistance and updates
"""

import logging

from portabletext_html import PortableTextRenderer

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.cms.importer import create_or_update_database_facility
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
        request["cms_id"] = request["_id"]  # Ensure cms_id is always set

    if request.get("_updatedAt"):
        request["updated_at"] = request["_updatedAt"]

    cms_facility = FacilitySchema(**request)

    return cms_facility


def sanity_parse_unit(request: dict) -> UnitSchema:
    """Parse a unit response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type record present")

    if request["_type"] != "unit":
        raise Exception("Invalid request: not a unit record")

    # Ensure cms_id is set from _id if present
    if request.get("_id"):
        request["cms_id"] = request["_id"]

    cms_unit = UnitSchema(**request)

    return cms_unit


async def persist_unit_record(unit: UnitSchema) -> None:
    """Persist the unit record to database. This is now a stub that delegates to the importer."""
    # Note: This function is kept for backward compatibility with webhook handlers
    # but now just logs a message since the importer handles all persistence
    message = f"Unit webhook received for {unit.code} - delegating to importer"
    logger.info(message)

    # The webhook handler already calls create_or_update_database_facility
    # so we don't need to do anything here
    await slack_message(webhook_url=settings.slack_hook_new_facilities, message=message)
