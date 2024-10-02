#!/usr/bin/env python3
import json
import logging
import pprint
from pathlib import Path

from portabletext_html import PortableTextRenderer
from pydantic import ValidationError
from sanity import Client
from sqlalchemy import select

from opennem import settings
from opennem.db import get_read_session
from opennem.db.models.opennem import Station
from opennem.schema.facility import FacilityOutputSchema

logger = logging.getLogger("sanity.importer")

client = Client(
    logger=logger,
    project_id=settings.sanity_project_id,
    dataset=settings.sanity_dataset_id,
    token=settings.sanity_api_key,
)


def get_facilities() -> list[FacilityOutputSchema]:
    res = client.query("""*[_type == 'facility'] {
            code,
            name,
            website,
            description,
            "network_id": upper(network->code),
            "network_region": upper(region->code),
            photos,
            wikipedia,
            location,
            units[]-> {
                code,
                dispatch_type,
                "status_id": status,
                "network_id": upper(network->code),
                "network_region": upper(network_region->code),
                "fueltech_id": fuel_technology->code,
                capacity_registered,
                capacity_maximum,
                storage_capacity,
                emissions_factor_co2,
                expected_closure_date,
                commencement_date,
                closure_date
            }
        }""")

    if not res or "result" not in res or not res["result"]:
        logger.error("No facilities found")
        return []

    pprint.pprint(res["result"][0])

    # compile the facility description to html
    for facility in res["result"]:
        if facility["description"] and len(facility["description"]) > 0:
            rendered_description = ""

            for _block in facility["description"]:
                rendered_description += PortableTextRenderer(_block).render()

            if rendered_description:
                facility["description"] = rendered_description

    result_models = []

    for facility in res["result"]:
        try:
            result_models.append(FacilityOutputSchema(**facility))
        except ValidationError as e:
            logger.error(f"Error creating facility model for {facility['code']}: {e}")
            logger.debug(facility)
            raise e

    return result_models


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
