#!/usr/bin/env python3
import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.cms.queries import get_cms_facilities
from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import Facility, Unit
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
        query = select(Facility).join(Unit).where(Facility.approved == True)  # noqa: E712
        result = await session.execute(query)
        facilities = result.scalars().all()

    return facilities


async def create_or_update_database_facility(facility: CMSFacilitySchema, send_slack: bool = True) -> None:
    """Create new database facilities from the CMS"""

    # created_date = get_today_opennem()
    facility_new = False
    record_updated = False

    async with get_write_session() as session:
        facility_query = select(Facility).options(selectinload(Facility.units)).where(Facility.code == facility.code)
        facility_db = (await session.execute(facility_query)).scalars().one_or_none()

        if not facility_db:
            facility_db = Facility(
                code=facility.code,
                name=facility.name,
                network_id=facility.network_id,
                network_region=facility.network_region,
                description=facility.description,
                wikipedia_link=facility.wikipedia,
                website_url=facility.website,
                approved=True,
                # created_at=created_date,
            )
            facility_new = True

        if facility.network_id and facility.network_id != facility_db.network_id:
            facility_db.network_id = facility.network_id
            record_updated = True

        if facility.name and facility.name != facility_db.name:
            facility_db.name = facility.name.strip()
            record_updated = True

        if facility.network_region and facility.network_region != facility_db.network_region:
            facility_db.network_region = facility.network_region.strip().upper()
            record_updated = True

        if facility.wikipedia and facility.wikipedia != facility_db.wikipedia_link:
            facility_db.wikipedia_link = facility.wikipedia.strip()
            record_updated = True

        if facility.website and facility.website != facility_db.website_url:
            facility_db.website_url = facility.website.strip()
            record_updated = True
        # if facility_db.location and (facility_db.location.lat and facility_db.location.lng):
        # facility_db.geom = f"SRID=4326;POINT({facility_db.location.lng} {facility_db.location.lat})"

        for unit in facility.units:
            unit_db = next((x for x in facility_db.units if x.code == unit.code), None)

            unit_db_lookup_mismatch = (await session.execute(select(Unit).where(Unit.code == unit.code))).scalar_one_or_none()

            # if the unit is in the database on another station, move it to the new station
            if unit_db_lookup_mismatch and (unit_db_lookup_mismatch.station_id != facility_db.id):
                unit_db_lookup_mismatch.station_id = facility_db.id
                unit_db = unit_db_lookup_mismatch
                record_updated = True
                logger.info(f"Moved unit {unit.code} to facility {facility.code}")

            if not unit_db:
                unit_db = Unit(
                    code=unit.code,
                    fueltech_id=unit.fueltech_id,
                    status_id=unit.status_id,
                    dispatch_type=unit.dispatch_type.value,
                    capacity_registered=round(unit.capacity_registered, 2) if unit.capacity_registered else None,
                    emissions_factor_co2=round(unit.emissions_factor_co2, 4) if unit.emissions_factor_co2 else None,
                    expected_closure_date=unit.expected_closure_date,
                    registered=unit.commencement_date,
                    deregistered=unit.closure_date,
                    # created_at=created_date,
                )
                facility_db.units.append(unit_db)
                record_updated = True
                logger.info(f"Created unit {unit.code} for facility {facility.code}")

            if unit.fueltech_id and unit.fueltech_id != unit_db.fueltech_id:
                unit_db.fueltech_id = unit.fueltech_id
                record_updated = True

            if unit.status_id and unit.status_id != unit_db.status_id:
                unit_db.status_id = unit.status_id
                record_updated = True

            if unit.dispatch_type and unit.dispatch_type.value != unit_db.dispatch_type.upper():
                unit_db.dispatch_type = unit.dispatch_type.value.upper()
                record_updated = True

            if unit.capacity_registered and unit.capacity_registered != unit_db.capacity_registered:
                unit_db.capacity_registered = round(unit.capacity_registered, 2) if unit.capacity_registered else None
                record_updated = True

            if unit.emissions_factor_co2 and unit.emissions_factor_co2 != unit_db.emissions_factor_co2:
                unit_db.emissions_factor_co2 = round(unit.emissions_factor_co2, 4) if unit.emissions_factor_co2 else None
                record_updated = True

            unit_db.approved = True

        session.add(facility_db)

        try:
            await session.commit()
            update_type = "New" if facility_new else "Updated"

            if record_updated:
                logger.info(f"{update_type} facility {facility_db.code} - {facility_db.name}")

            if send_slack:
                await slack_message(
                    webhook_url=settings.slack_hook_new_facilities,
                    message=f"{update_type} facility {facility_db.code} - {facility_db.name}",
                )
        except Exception as e:
            logger.error(f"Error creating facility {facility_db.code} - {facility_db.name}: {e}")


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


async def update_facility_from_cms(facility_code: str, send_slack: bool = True) -> None:
    """Update a single facility from the CMS"""

    sanity_facilities = get_cms_facilities(facility_code=facility_code)

    if not sanity_facilities:
        logger.info(f"Facility {facility_code} not found in CMS")
        return

    await create_or_update_database_facility(sanity_facilities[0], send_slack=send_slack)


async def update_database_facilities_from_cms(send_slack: bool = True) -> None:
    """Update the database facilities from the CMS

    :param run_updates: Run updates to each facility. If false will only add new facilities
    """

    sanity_facilities = get_cms_facilities()
    database_facilities = await get_database_facilities()

    logger.info(f"Updating {len(sanity_facilities)} facilities from CMS. Have {len(database_facilities)} in database")

    sanity_facility_codes = [facility.code.upper() for facility in sanity_facilities]

    missing_facilities = {code.upper() for code in sanity_facility_codes} - {
        str(facility.code).upper() for facility in database_facilities
    }

    if missing_facilities:
        logger.info(f"Missing {len(missing_facilities)} facilities in database")
        for facility in missing_facilities:
            logger.info(f" - {facility}")

    missing_facilities_database = {str(facility.code).upper() for facility in database_facilities} - {
        code.upper() for code in sanity_facility_codes
    }

    if missing_facilities_database:
        logger.info(f"Missing {len(missing_facilities_database)} facilities in CMS")
        for facility in missing_facilities_database:
            logger.info(f" - {facility}")

    # loop through each facility and add to database if not present or update if present
    for facility in sanity_facilities:
        await create_or_update_database_facility(facility, send_slack=send_slack)


if __name__ == "__main__":
    import asyncio

    # opennem_stations = get_opennem_stations()
    # asyncio.run(update_database_facilities_from_cms(send_slack=False))
    asyncio.run(update_facility_from_cms(facility_code="CROOKWF3", send_slack=False))
