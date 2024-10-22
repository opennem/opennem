#!/usr/bin/env python3
import json
import logging
from datetime import datetime
from pathlib import Path

from rich.prompt import Confirm, Prompt
from sqlalchemy import select

from opennem.cms.fieldmap import cms_field_to_database_field
from opennem.cms.queries import get_cms_facilities
from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import Facility, Location, Unit
from opennem.queries.facilities import get_facility_by_code
from opennem.schema.facility import CMSFacilitySchema

logger = logging.getLogger("sanity.importer")


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
        query = select(Facility).where(Facility.approved == True)  # noqa: E712
        result = await session.execute(query)
        facilities = result.scalars().all()

    return facilities


async def create_database_facility_from_cms(facility: CMSFacilitySchema) -> None:
    """Create new database facilities from the CMS"""

    async with get_write_session() as session:
        station = Facility(
            code=facility.code,
            name=facility.name,
            network_code=facility.network_id,
            description=facility.description,
            wikipedia_link=facility.wikipedia,
            website_url=facility.website,
            approved=True,
            created_at=datetime.now(),
        )

        if facility.location and (facility.location.lat and facility.location.lng):
            station.location = Location(geom=f"SRID=4326;POINT({facility.location.lng} {facility.location.lat})")

        for unit in facility.units:
            db_unit = Unit(
                code=unit.code,
                network_id=station.network_code,
                fueltech_id=unit.fueltech_id,
                status_id=unit.status_id,
                dispatch_type=unit.dispatch_type.value,
                capacity_registered=round(unit.capacity_registered, 2) if unit.capacity_registered else None,
                emissions_factor_co2=round(unit.emissions_factor_co2, 4) if unit.emissions_factor_co2 else None,
                expected_closure_date=unit.expected_closure_date,
                registered=unit.commencement_date,
                deregistered=unit.closure_date,
            )
            station.units.append(db_unit)

        session.add(station)

        try:
            await session.commit()
            logger.info(f"Created facility {facility.code} - {facility.name}")
        except Exception as e:
            logger.error(f"Error creating facility {facility.code} - {facility.name}: {e}")


def check_cms_duplicate_ids(facilities: list[CMSFacilitySchema]) -> tuple[list[str], list[str]]:
    """Check for duplicate ids in the CMS"""

    duplicate_facility_ids = []
    duplicate_unit_ids = []

    for facility in facilities:
        if facilities.count(facility.code) > 1:
            duplicate_facility_ids.append(facility.code)

        for unit in facility.units:
            if facilities.count(unit.code) > 1:
                duplicate_unit_ids.append(unit.code)

    if duplicate_facility_ids:
        logger.info(f"Duplicate facility ids: {duplicate_facility_ids}")

    if duplicate_unit_ids:
        logger.info(f"Duplicate unit ids: {duplicate_unit_ids}")

    return duplicate_facility_ids, duplicate_unit_ids


async def update_database_facilities_from_cms(run_updates: bool = True) -> None:
    """Update the database facilities from the CMS

    :param run_updates: Run updates to each facility. If false will only add new facilities
    """

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

    missing_facilities_database = set(database_facility_codes) - set(sanity_facility_codes)

    if missing_facilities_database:
        logger.info(f"Missing {len(missing_facilities_database)} facilities in CMS")
        for facility in missing_facilities_database:
            logger.info(f" - {facility}")

    # loop through each facility and add to database if not present or update if present
    for facility in sanity_facilities:
        if facility.code not in database_facility_codes:
            logger.info(f"New facility {facility.code} - {facility.name}")
            add_facility_prompt = Confirm.ask("Add new facility?", default=False)

            if not add_facility_prompt:
                continue

            await create_database_facility_from_cms(facility)
            continue

        if not run_updates:
            logger.info(f"Skipping update for {facility.code} - {facility.name}")
            continue

        # else get the facility from the database
        database_facility = await get_facility_by_code(facility.code)

        if not database_facility:
            logger.error(f"Facility {facility.code} not found in database .. somehow")
            continue

        logger.info(f"Updating facility {facility.code} - {facility.name}")

        # loop through each field and each unit and update the database
        for field in ["name", "website", "description", "wikipedia"]:
            database_field = cms_field_to_database_field(field)

            cms_value = getattr(facility, field)
            database_value = getattr(database_facility, database_field)

            if cms_value != database_value:
                logger.info(f" => {field}: {database_value} needs to be updated to {cms_value}")

                confirm = Prompt.ask(f"Update {field}?", choices=["y", "n", "c"], default="n")

                if confirm == "n":
                    continue

                # update the CMS record
                elif confirm == "c":
                    setattr(facility, field, database_value)

                # update the database record
                else:
                    setattr(database_facility, database_field, cms_value)


if __name__ == "__main__":
    import asyncio

    # opennem_stations = get_opennem_stations()
    asyncio.run(update_database_facilities_from_cms())
