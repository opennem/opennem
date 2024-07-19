import logging

from sqlalchemy.future import select

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
    # AEMO backfill derives from APVI data
    {"state": "NSW", "network": "AEMO_ROOFTOP_BACKFILL", "network_region": "NSW1"},
    {"state": "QLD", "network": "AEMO_ROOFTOP_BACKFILL", "network_region": "QLD1"},
    {"state": "VIC", "network": "AEMO_ROOFTOP_BACKFILL", "network_region": "VIC1"},
    {"state": "TAS", "network": "AEMO_ROOFTOP_BACKFILL", "network_region": "TAS1"},
    {"state": "SA", "network": "AEMO_ROOFTOP_BACKFILL", "network_region": "SA1"},
    {"state": "NT", "network": "AEMO_ROOFTOP_BACKFILL", "network_region": "NT1"},
    # Opennem backfill derives from APVI data
    {"state": "NSW", "network": "OPENNEM_ROOFTOP_BACKFILL", "network_region": "NSW1"},
    {"state": "QLD", "network": "OPENNEM_ROOFTOP_BACKFILL", "network_region": "QLD1"},
    {"state": "VIC", "network": "OPENNEM_ROOFTOP_BACKFILL", "network_region": "VIC1"},
    {"state": "TAS", "network": "OPENNEM_ROOFTOP_BACKFILL", "network_region": "TAS1"},
    {"state": "SA", "network": "OPENNEM_ROOFTOP_BACKFILL", "network_region": "SA1"},
    {"state": "NT", "network": "OPENNEM_ROOFTOP_BACKFILL", "network_region": "NT1"},
]


async def rooftop_facilities() -> None:
    async with SessionLocal() as session:
        for state_map in STATE_NETWORK_REGION_MAP:
            state_rooftop_code = "{}_{}_{}".format(
                ROOFTOP_CODE,
                state_map["network"].upper(),
                state_map["state"].upper(),
            )

            result = await session.execute(select(Station).filter_by(code=state_rooftop_code))
            rooftop_station = result.scalars().one_or_none()

            if not rooftop_station:
                logger.info(f"Creating new station {state_rooftop_code}")
                rooftop_station = Station(
                    code=state_rooftop_code,
                )

            rooftop_station.name = "Rooftop Solar {}".format(state_map["state"])
            rooftop_station.description = "Solar rooftop facilities for {}".format(state_map["state"])
            rooftop_station.approved = False
            rooftop_station.approved_by = ""
            rooftop_station.created_by = "opennem.importer.rooftop"

            if not rooftop_station.location:
                rooftop_station.location = Location(state=state_map["state"])

            result = await session.execute(select(Facility).filter_by(code=state_rooftop_code))
            rooftop_fac = result.scalars().one_or_none()

            if not rooftop_fac:
                logger.info(f"Creating new facility {state_rooftop_code}")
                rooftop_fac = Facility(code=state_rooftop_code)

            network = state_map["network"]

            # map to separate AEMO rooftop network
            if network.upper() == "NEM":
                network = "AEMO_ROOFTOP"

            rooftop_fac.network_id = network
            rooftop_fac.network_region = state_map["network_region"]
            rooftop_fac.fueltech_id = "solar_rooftop"
            rooftop_fac.status_id = "operating"
            rooftop_fac.active = False
            rooftop_fac.dispatch_type = DispatchType.GENERATOR
            rooftop_fac.approved_by = "opennem.importer.rooftop"
            rooftop_fac.created_by = "opennem.importer.rooftop"

            rooftop_station.facilities.append(rooftop_fac)
            session.add(rooftop_fac)

            session.add(rooftop_station)

        await session.commit()


def rooftop_remap_regionids(rooftop_record: dict | None) -> dict | None:
    """Map an AEMO region code to a rooftop station code"""

    if not rooftop_record:
        return None

    if "facility_code" not in rooftop_record:
        return None

    fac_code = rooftop_record["facility_code"]

    if fac_code not in ["NSW1", "QLD1", "VIC1", "TAS1", "SA1"]:
        return None

    rooftop_fac_code = "{}_{}_{}".format(ROOFTOP_CODE, "NEM", fac_code.rstrip("1"))
    rooftop_record["facility_code"] = rooftop_fac_code

    return rooftop_record


# debug entry point
if __name__ == "__main__":
    import asyncio

    asyncio.run(rooftop_facilities())
