"""
Takes Sanity webhook responses and parses into structured format for persistance and updates
"""

import logging

from sqlalchemy import select

from opennem.db import get_write_session
from opennem.db.models.opennem import Facility, Unit
from opennem.schema.facility import CMSFacilitySchema, CMSUnitSchema

logger = logging.getLogger("opennem.controllers.sanity")


async def parse_sanity_webhook_request(request: dict) -> None:
    """Parse a sanity webhook response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type field present. Fields are {" + ", ".join(request.keys()) + "}")

    record_type: str = request["_type"].lower()

    if record_type == "facility":
        facility_record = sanity_parse_facility(request)
        await persist_facility_record(facility_record)
    elif record_type == "unit":
        unit_record = sanity_parse_unit(request)
        await persist_unit_record(unit_record)
    else:
        logger.error(f"Invalid record type: {record_type}")


def sanity_parse_facility(request: dict) -> CMSFacilitySchema:
    """Parse a facility response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type record present")

    if request["_type"] != "facility":
        raise Exception("Invalid request: not a facility record")

    facility = {
        "code": request["code"] if "code" in request else None,
        "name": request["name"] if "name" in request else None,
        "wikipedia": request["wikipedia"] if "wikipedia" in request else None,
        "website": request["website"] if "website" in request else None,
        "lat": None,
        "lng": None,
    }

    if "location" in request:
        if request["location"]["_type"] == "geopoint":
            facility["lat"] = request["location"]["lat"]
            facility["lng"] = request["location"]["lng"]

    return facility


def sanity_parse_unit(request: dict) -> dict:
    """Parse a facility response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type record present")

    if request["_type"] != "unit":
        raise Exception("Invalid request: not a unit record")

    unit = {
        "code": request["code"] if "code" in request else None,
        "emissions_factor_co2": request["emissions_factor_co2"] if "emissions_factor_co2" in request else None,
        "capacity_registered": request["capacity_registered"] if "capacity_registered" in request else None,
        "dispatch_type": request["dispatch_type"] if "dispatch_type" in request else None,
        "status": request["status"] if "status" in request else None,
    }

    return unit


async def persist_facility_record(facility: CMSFacilitySchema) -> None:
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


async def persist_unit_record(unit: CMSUnitSchema) -> None:
    """Persit the unit record to facility table"""

    async with get_write_session() as session:
        unit_db = (await session.execute(select(Unit).filter(Unit.code == unit.code))).scalars().one_or_none()

        if not unit_db:
            unit_db = Unit(**unit)

        unit_db.active = True
        unit_db.capacity_registered = unit.capacity_registered
        unit_db.dispatch_type = unit.dispatch_type.value
        unit_db.emissions_factor_co2 = unit.emissions_factor_co2
        unit_db.status_id = unit.status_id

        session.add(unit_db)
        await session.commit()
