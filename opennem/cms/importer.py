#!/usr/bin/env python3
import json
import logging
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


def get_cms_facilities(facility_code: str | None = None) -> list[FacilityOutputSchema]:
    filter_query = ""

    if facility_code:
        filter_query += f" && code == '{facility_code}'"

    query = f"""*[_type == "facility"{filter_query} && !(_id in path("drafts.**"))] {{
        _id,
        _createdAt,
        _updatedAt,
        code,
        name,
        website,
        description,
        "network_id": upper(network->code),
        "network_region": upper(region->code),
        photos,
        wikipedia,
        location,
        units[]-> {{
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
        }}
    }}"""

    res = client.query(query)

    if not res or not isinstance(res, dict) or "result" not in res or not res["result"]:
        logger.error("No facilities found")
        return []

    result_models = {}

    # compile the facility description to html
    for facility in res["result"]:
        if facility.get("description") and isinstance(facility["description"], list):
            rendered_description = ""
            for block in facility["description"]:
                rendered_description += PortableTextRenderer(block).render()
            if rendered_description:
                facility["description"] = rendered_description

        if facility.get("_id"):
            facility["id"] = facility["_id"]

        if facility["_updatedAt"]:
            facility["updated_at"] = facility["_updatedAt"]

        if facility["code"] in result_models:
            logger.warning(
                f"Duplicate facility code {facility['code']} sanity. {facility['_id']}"
                f" existing {result_models[facility['code']].id}"
            )
            continue

        try:
            result_models[facility["code"]] = FacilityOutputSchema(**facility)
        except ValidationError as e:
            logger.error(f"Error creating facility model for {facility['code']}: {e}")
            logger.debug(facility)
            raise e

    return list(result_models.values())


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

    # opennem_stations = get_opennem_stations()
    sanity_facilities = get_cms_facilities()
    database_facilities = asyncio.run(get_database_facilities())

    database_facility_codes = [facility.code for facility in database_facilities]
