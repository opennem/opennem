"""
Takes Sanity webhook responses and parses into structured format for persistance and updates
"""
import logging

from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Station

logger = logging.getLogger("opennem.controllers.sanity")


def parse_sanity_webhook(request: dict) -> None:
    """Parse a sanity webhook response"""
    if "_type" not in request:
        raise Exception("Invalid request: no _type field present. Fields are {" + ", ".join(request.keys()) + "}")

    record_type: str = request["_type"].lower()

    if record_type == "facility":
        facility_record = sanity_parse_facility(request)
        persist_facility_record(facility_record)
    elif record_type == "unit":
        unit_record = sanity_parse_unit(request)
        persist_unit_record(unit_record)
    else:
        logger.error(f"Invalid record type: {record_type}")


def sanity_parse_facility(request: dict) -> dict:
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


def persist_facility_record(facility_record: dict) -> None:
    """Persist a facility record to the Station table in database"""

    with SessionLocal() as session:
        facility = session.query(Station).filter(Station.code == facility_record["code"]).one_or_none()

        if not facility:
            facility = Station(**facility_record)

        facility.approved = True
        facility.name = facility_record["name"]
        facility.network_name = facility_record["name"]
        facility.website_url = facility_record["website"]
        facility.wikipedia_url = facility_record["wikipedia"]

        session.add(facility)
        session.commit()


def persist_unit_record(unit_record: dict) -> None:
    """Persit the unit record to facility table"""

    with SessionLocal() as session:
        unit = session.query(Facility).filter(Facility.code == unit_record["code"]).one_or_none()

        if not unit:
            unit = Facility(**unit_record)

        unit.active = True
        unit.approved = True
        unit.capacity_registered = unit_record["capacity_registered"]
        unit.dispatch_type = unit_record["dispatch_type"]
        unit.emissions_factor_co2 = unit_record["emissions_factor_co2"]
        unit.status = unit_record["status"]

        session.add(unit)
        session.commit()
