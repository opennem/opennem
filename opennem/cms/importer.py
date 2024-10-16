#!/usr/bin/env python3
import json
import logging
from pathlib import Path

from portabletext_html import PortableTextRenderer
from pydantic import ValidationError
from rich.prompt import Confirm
from sanity import Client
from sqlalchemy import select

from opennem import settings
from opennem.db import get_read_session
from opennem.db.models.opennem import Station
from opennem.queries.facilities import get_facility_by_code
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
                # f" existing {result_models[facility['code']].id}"
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


async def update_database_facilities_from_cms() -> None:
    """Update the database facilities from the CMS"""

    sanity_facilities = get_cms_facilities()
    database_facilities = await get_database_facilities()

    logger.info(f"Updating {len(sanity_facilities)} facilities from CMS. Have {len(database_facilities)} in database")

    sanity_facility_codes = [facility.code for facility in sanity_facilities]
    database_facility_codes = [facility.code for facility in database_facilities]

    missing_facilities = set(sanity_facility_codes) - set(database_facility_codes)

    if missing_facilities:
        logger.info(f"Missing {len(missing_facilities)} facilities in database")
        for facility in missing_facilities:
            logger.info(f" - {facility}")

    for facility in sanity_facilities:
        if facility.code not in database_facility_codes:
            logger.info(f"New facility {facility.code} - {facility.name}")
            continue

        # else get the facility from the database
        database_facility = await get_facility_by_code(facility.code)

        if not database_facility:
            logger.error(f"Facility {facility.code} not found in database .. somehow")
            continue

        logger.info(f"Updating facility {facility.code} - {facility.name}")

        # loop through each field and each unit and update the database
        for field in ["name", "website", "description", "wikipedia"]:
            cms_value = getattr(facility, field)

            if cms_value != getattr(database_facility, field):
                logger.info(f" => {field}: {getattr(database_facility, field)} needs to be updated to {cms_value}")
                confirm = Confirm.ask(f"Update {field}?")
                if not confirm:
                    continue

                setattr(database_facility, field, cms_value)

        if facility.photos:
            logger.info(f"Photos: {facility.photos}")

        if facility.location:
            logger.info(f"Location: {facility.location}")


if __name__ == "__main__":
    import asyncio

    # opennem_stations = get_opennem_stations()
    asyncio.run(update_database_facilities_from_cms())
