"""OpenNEM CMS Importer.

This module handles the synchronization of facility and unit data between the Sanity CMS
and the OpenNEM database. It provides functionality to:
- Import facility and unit data from the CMS
- Update existing database records
- Create new facilities and units
- Move units between facilities
- Validate data consistency

The module ensures that the OpenNEM database stays in sync with the CMS, which acts as
the source of truth for facility and unit metadata.

Note:
    All database operations are performed asynchronously using SQLAlchemy 2.0
    The module uses the Sanity.io CMS as the data source
"""

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
from opennem.schema.facility import FacilitySchema
from opennem.workers.facility_data_seen import update_facility_seen_range

logger = logging.getLogger("sanity.importer")


def get_opennem_stations() -> list[dict]:
    """Read the stations.json file containing legacy station data.

    This is a legacy function that reads the old stations.json file which was used
    before the CMS implementation. It's kept for reference and migration purposes.

    Returns:
        list[dict]: List of station dictionaries from the JSON file
    """
    stations_path = Path(__file__).parent.parent / "data" / "stations.json"
    with open(stations_path) as f:
        stations = json.load(f)

    logger.info(f"Got {len(stations)} opennem stations")
    return stations


async def get_database_facilities() -> list[Facility]:
    """Get all approved facilities with their associated units from the database.

    This function performs a joined query to get all approved facilities and their
    associated units in a single database query.

    Returns:
        list[Facility]: List of Facility objects with their units eagerly loaded
    """
    async with get_read_session() as session:
        query = select(Facility).join(Unit).where(Facility.approved == True)  # noqa: E712
        result = await session.execute(query)
        facilities = result.scalars().all()

    return facilities


def _check_facility_differences(facility: FacilitySchema, facility_db: Facility) -> dict[str, list[str]]:
    """Compare a CMS facility with database facility and return differences.

    This function performs a detailed comparison between a facility from the CMS
    and its corresponding database record, checking all relevant fields and unit
    associations.

    Args:
        facility: The facility data from CMS
        facility_db: The facility from the database

    Returns:
        dict[str, list[str]]: Dictionary containing lists of differences categorized by:
            - facility: Changes to facility-level fields
            - units: Changes to unit-level fields
            - unit_moves: Units that need to be moved between facilities
    """
    differences = {
        "facility": [],
        "units": [],
        "unit_moves": [],
    }

    # Check facility fields
    if facility.network_id != facility_db.network_id:
        differences["facility"].append(f"network_id: {facility_db.network_id} -> {facility.network_id}")

    if facility.name != facility_db.name:
        differences["facility"].append(f"name: {facility_db.name} -> {facility.name}")

    if facility.network_region != facility_db.network_region:
        differences["facility"].append(f"network_region: {facility_db.network_region} -> {facility.network_region}")

    if facility.wikipedia != facility_db.wikipedia_link:
        differences["facility"].append(f"wikipedia: {facility_db.wikipedia_link} -> {facility.wikipedia}")

    if facility.website != facility_db.website_url:
        differences["facility"].append(f"website: {facility_db.website_url} -> {facility.website}")

    # Create lookup of existing units
    existing_units = {u.code: u for u in facility_db.units}
    cms_unit_codes = {u.code for u in facility.units}
    db_unit_codes = set(existing_units.keys())

    # Check for units that need to be added or removed
    units_to_add = cms_unit_codes - db_unit_codes
    if units_to_add:
        differences["units"].append(f"New units to add: {', '.join(units_to_add)}")

    units_to_remove = db_unit_codes - cms_unit_codes
    if units_to_remove:
        differences["units"].append(f"Units to remove: {', '.join(units_to_remove)}")

    # Check each unit's fields
    for unit in facility.units:
        unit_db = existing_units.get(unit.code)
        if not unit_db:
            continue

        unit_differences = []

        if unit.fueltech_id and unit.fueltech_id.value != unit_db.fueltech_id:
            unit_differences.append(f"fueltech_id: {unit_db.fueltech_id} -> {unit.fueltech_id.value}")

        if unit.status_id and unit.status_id.value != unit_db.status_id:
            unit_differences.append(f"status_id: {unit_db.status_id} -> {unit.status_id.value}")

        if unit.dispatch_type and unit.dispatch_type.value != unit_db.dispatch_type.upper():
            unit_differences.append(f"dispatch_type: {unit_db.dispatch_type} -> {unit.dispatch_type.value}")

        if unit.capacity_registered and unit.capacity_registered != unit_db.capacity_registered:
            unit_differences.append(f"capacity_registered: {unit_db.capacity_registered} -> {round(unit.capacity_registered, 2)}")

        if unit.emissions_factor_co2 and unit.emissions_factor_co2 != unit_db.emissions_factor_co2:
            unit_differences.append(
                f"emissions_factor_co2: {unit_db.emissions_factor_co2} -> {round(unit.emissions_factor_co2, 4)}"
            )

        if unit_differences:
            differences["units"].append(f"Unit {unit.code} changes: {', '.join(unit_differences)}")

    return differences


async def create_or_update_database_facility(facility: FacilitySchema, send_slack: bool = True, dry_run: bool = False) -> bool:
    """Create new database facilities from the CMS or update existing ones.

    This function handles both creation of new facilities and updates to existing ones.
    It performs a detailed comparison of facility and unit data before making any changes,
    and can operate in a dry-run mode for testing purposes.

    The function will:
    - Create new facilities if they don't exist
    - Update facility metadata if it has changed
    - Create new units
    - Update unit metadata
    - Move units between facilities if needed
    - Send Slack notifications of changes (if enabled)

    Args:
        facility: The facility data from CMS
        send_slack: Whether to send Slack notifications about changes
        dry_run: If True, only check for differences without making changes

    Raises:
        Exception: Any database errors during the update process

    Returns:
        bool: True if the facility or unit was created.
    """
    facility_or_unit_created = False
    async with get_write_session() as session:
        # Load facility and its units in a single query with eager loading
        facility_query = select(Facility).options(selectinload(Facility.units)).where(Facility.code == facility.code)
        facility_db = (await session.execute(facility_query)).scalars().one_or_none()

        if not facility_db:
            if dry_run:
                logger.info(f"Would create new facility: {facility.code} - {facility.name}")
                return

            facility_db = Facility(
                code=facility.code,
                name=facility.name,
                network_id=facility.network_id,
                network_region=facility.network_region,
                description=facility.description,
                wikipedia_link=facility.wikipedia,
                website_url=facility.website,
                approved=True,
            )
            facility_new = True
            session.add(facility_db)
            facility_db.units = []
            facility_or_unit_created = True
        else:
            facility_new = False
            # Check for differences before making any changes
            differences = _check_facility_differences(facility, facility_db)

            if not any(differences.values()):
                logger.debug(f"No changes needed for facility {facility.code}")
                return

            if dry_run:
                if differences["facility"]:
                    logger.info(f"Would update facility {facility.code}:")
                    for diff in differences["facility"]:
                        logger.info(f"  - {diff}")
                if differences["units"]:
                    logger.info(f"Would update units for {facility.code}:")
                    for diff in differences["units"]:
                        logger.info(f"  - {diff}")
                return

        record_updated = False

        # Only proceed with updates if we have differences and not in dry_run mode
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

        # Create a lookup dict of existing units
        existing_units = {u.code: u for u in facility_db.units}

        # Process units in a single transaction
        for unit in facility.units:
            unit_db = existing_units.get(unit.code)

            if not unit_db:
                # Load unit from database if it exists but not in current facility
                unit_query = select(Unit).where(Unit.code == unit.code)
                unit_db = (await session.execute(unit_query)).scalar_one_or_none()

                if unit_db and unit_db.station_id != facility_db.id:
                    unit_db.station_id = facility_db.id
                    record_updated = True
                    logger.info(f"Moved unit {unit.code} to facility {facility.code} ({facility_db.id})")

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
                )
                facility_db.units.append(unit_db)
                record_updated = True
                facility_or_unit_created = True
                logger.info(f"Created unit {unit.code} for facility {facility.code}")

            if unit.fueltech_id and unit.fueltech_id.value != unit_db.fueltech_id:
                unit_db.fueltech_id = unit.fueltech_id.value
                record_updated = True

            if unit.status_id and unit.status_id.value != unit_db.status_id:
                unit_db.status_id = unit.status_id.value
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

        if record_updated:
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
                raise

    return facility_or_unit_created


def check_cms_duplicate_ids(facilities: list[FacilitySchema]) -> tuple[list[str], list[str]]:
    """Check for duplicate facility and unit IDs in the CMS data.

    This function helps maintain data integrity by identifying any duplicate
    facility or unit codes in the CMS data, which should be unique.

    Args:
        facilities: List of facilities from the CMS

    Returns:
        tuple[list[str], list[str]]: Two lists containing:
            - List of duplicate facility codes
            - List of duplicate unit codes
    """
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
    """Update a single facility from the CMS.

    This function provides a targeted way to update a specific facility and its
    units from the CMS data. Useful for single facility updates or testing.

    Args:
        facility_code: The facility code to update
        send_slack: Whether to send Slack notifications about changes

    Note:
        If the facility is not found in the CMS, a log message is generated
        but no error is raised.
    """
    sanity_facilities = get_cms_facilities(facility_code=facility_code)

    if not sanity_facilities:
        logger.info(f"Facility {facility_code} not found in CMS")
        return

    facility_or_unit_created = await create_or_update_database_facility(sanity_facilities[0], send_slack=send_slack)

    if facility_or_unit_created:
        logger.info(f"Created facility {facility_code}")
    else:
        logger.info(f"Updated facility {facility_code}")


async def update_database_facilities_from_cms(send_slack: bool = True, dry_run: bool = False) -> None:
    """Update all database facilities from the CMS.

    This is the main function for synchronizing the entire database with the CMS.
    It performs a full comparison of all facilities and their units, identifying
    missing or changed records, and updating the database accordingly.

    The function will:
    - Identify facilities missing from the database
    - Identify facilities missing from the CMS
    - Update all facilities that have changes
    - Create new facilities as needed
    - Send Slack notifications about changes (if enabled)

    Args:
        send_slack: Whether to send Slack notifications about changes
        dry_run: If True, only check for differences without making changes
    """
    sanity_facilities = get_cms_facilities()
    database_facilities = await get_database_facilities()

    logger.info(f"Checking {len(sanity_facilities)} facilities from CMS against {len(database_facilities)} in database")

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

    facility_or_unit_created = False

    # loop through each facility and add to database if not present or update if present
    for facility in sanity_facilities:
        _create_or_update = await create_or_update_database_facility(facility, send_slack=send_slack, dry_run=dry_run)
        if _create_or_update:
            facility_or_unit_created = True

    if facility_or_unit_created:
        logger.info(f"Created {facility_or_unit_created} facilities")
        await update_facility_seen_range(include_first_seen=True, facility_codes=list(missing_facilities))


if __name__ == "__main__":
    import asyncio

    # opennem_stations = get_opennem_stations()
    asyncio.run(update_database_facilities_from_cms(send_slack=False))
    # asyncio.run(update_facility_from_cms(facility_code="0BSSF", send_slack=False))
