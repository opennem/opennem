import logging
from typing import Dict, Optional

from opennem.core.dispatch_type import DispatchType
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Location, Station

logger = logging.getLogger(__name__)

ROOFTOP_CODE = "ROOFTOP"


STATE_NETWORK_REGION_MAP = [
    # APVI
    {"state": "NSW", "network": "APVI", "network_region": "NSW1"},
    {"state": "QLD", "network": "APVI", "network_region": "QLD1"},
    {"state": "VIC", "network": "APVI", "network_region": "VIC1"},
    {"state": "TAS", "network": "APVI", "network_region": "TAS1"},
    {"state": "SA", "network": "APVI", "network_region": "SA1"},
    {"state": "NT", "network": "APVI", "network_region": "NT1"},
    {"state": "WA", "network": "APVI", "network_region": "WEM"},
    # AEMO
    {"state": "NSW", "network": "NEM", "network_region": "NSW1"},
    {"state": "QLD", "network": "NEM", "network_region": "QLD1"},
    {"state": "VIC", "network": "NEM", "network_region": "VIC1"},
    {"state": "TAS", "network": "NEM", "network_region": "TAS1"},
    {"state": "SA", "network": "NEM", "network_region": "SA1"},
    {"state": "NT", "network": "NEM", "network_region": "NT1"},
]


def rooftop_facilities() -> None:

    session = SessionLocal()

    for state_map in STATE_NETWORK_REGION_MAP:
        state_rooftop_code = "{}_{}_{}".format(
            ROOFTOP_CODE,
            state_map["network"].upper(),
            state_map["state"].upper(),
        )

        rooftop_station = session.query(Station).filter_by(code=state_rooftop_code).one_or_none()

        if not rooftop_station:
            logger.info("Creating new station {}".format(state_rooftop_code))
            rooftop_station = Station(
                code=state_rooftop_code,
            )

        rooftop_station.name = "Rooftop Solar {}".format(state_map["state"])
        rooftop_station.description = "Solar rooftop facilities for {}".format(state_map["state"])
        rooftop_station.approved = True
        rooftop_station.approved_by = "opennem.importer.rooftop"
        rooftop_station.created_by = "opennem.importer.rooftop"

        if not rooftop_station.location:
            rooftop_station.location = Location(state=state_map["state"])

        rooftop_fac = session.query(Facility).filter_by(code=state_rooftop_code).one_or_none()

        if not rooftop_fac:
            logger.info("Creating new facility {}".format(state_rooftop_code))
            rooftop_fac = Facility(code=state_rooftop_code)

        rooftop_fac.network_id = state_map["network"]
        rooftop_fac.network_region = state_map["network_region"]
        rooftop_fac.fueltech_id = "solar_rooftop"
        rooftop_fac.status_id = "operating"
        rooftop_fac.active = True
        rooftop_fac.dispatch_type = DispatchType.GENERATOR
        rooftop_fac.approved_by = "opennem.importer.rooftop"
        rooftop_fac.created_by = "opennem.importer.rooftop"

        rooftop_station.facilities.append(rooftop_fac)
        session.add(rooftop_fac)

        session.add(rooftop_station)

    session.commit()


def rooftop_remap_regionids(rooftop_record: Dict) -> Optional[Dict]:
    """Map an AEMO region code to a rooftop station code"""
    fac_code = rooftop_record["facility_code"]

    if fac_code not in ["NSW1", "QLD1", "VIC1", "TAS1", "SA1"]:
        return None

    rooftop_fac_code = "{}_{}_{}".format(ROOFTOP_CODE, "NEM", fac_code.rstrip("1"))
    rooftop_record["facility_code"] = rooftop_fac_code

    return rooftop_record


if __name__ == "__main__":
    rooftop_facilities()
