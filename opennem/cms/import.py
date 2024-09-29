#!/usr/bin/env python3
import json
import logging
import pprint
from pathlib import Path

from sanity import Client
from sqlalchemy import select

from opennem import settings
from opennem.db import get_read_session
from opennem.db.models.opennem import Station

logger = logging.getLogger("sanity.importer")

client = Client(
    logger=logger,
    project_id=settings.sanity_project_id,
    dataset=settings.sanity_dataset_id,
    token=settings.sanity_api_key,
)


def get_facilities() -> list[dict]:
    res = client.query("""*[_type == 'facility'] {
            code,
            name,
            website,
            description,
            "network_id": upper(network->code),
            "network_region": upper(region->code),
            photos[]-> { url },
            location,
            units[]-> {
                code,
                dispatch_type,
                status,
                "network_region": upper(network_region->code),
                "fueltech_id": fuel_technology->code,
                capacity_registered
            }
        }""")

    if not res or not res["result"]:
        logger.error("No facilities found")
        return []

    # sort all the facilities by updated at
    # for facility in sorted(res["result"], key=lambda x: x["_updatedAt"], reverse=False):
    # print(facility["code"], facility["_updatedAt"])

    logger.info(f"Got {len(res['result'])} sanity facilities")

    pprint.pprint(res["result"][0])

    return res["result"]


def get_opennem_stations() -> list[dict]:
    """read the stations.json file and print out the codes"""
    stations_path = Path(__file__).parent.parent / "data" / "stations.json"
    with open(stations_path) as f:
        stations = json.load(f)

    logger.info(f"Got {len(stations)} opennem stations")

    return stations


async def get_database_facilities():
    """Get all facilities with their associated station information from the database"""

    async with get_read_session() as session:
        query = select(Station).where(Station.approved == True)  # noqa: E712
        # .join(Facility, Facility.station_id == Station.id)
        result = await session.execute(query)
        facilities = result.scalars().all()

    return facilities


if __name__ == "__main__":
    import asyncio

    opennem_stations = get_opennem_stations()
    sanity_facilities = get_facilities()
    database_facilities = asyncio.run(get_database_facilities())

    database_facility_codes = [facility.code for facility in database_facilities]

    # find the facilities that are not in the opennem stations
    for facility in sanity_facilities:
        # find it based on "code" field in opennem stations
        if facility["code"] not in database_facility_codes:
            logger.info(f"Facility {facility['code']} not in database stations")
