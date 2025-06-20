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


async def create_or_update_database_facility(facility: FacilitySchema, send_slack: bool = True, dry_run: bool = False) -> bool:
    """Create new database facilities from the CMS or update existing ones.

    This function handles both creation of new facilities and updates to existing ones.
    It uses cms_id as the primary identifier for lookups, falling back to code for
    backward compatibility. All metadata is always updated from the CMS.

    The function will:
    - Lookup facilities by cms_id first, then by code
    - Create new facilities if they don't exist
    - Always update all facility metadata from CMS
    - Create new units or update existing ones
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
        # First try to find by cms_id (primary identifier)
        facility_db = None
        if facility.cms_id:
            facility_query = select(Facility).options(selectinload(Facility.units)).where(Facility.cms_id == facility.cms_id)
            facility_db = (await session.execute(facility_query)).scalars().one_or_none()

        # If not found by cms_id, try by code (backward compatibility)
        if not facility_db:
            facility_query = select(Facility).options(selectinload(Facility.units)).where(Facility.code == facility.code)
            facility_db = (await session.execute(facility_query)).scalars().one_or_none()

        # If still not found, create new facility
        if not facility_db:
            if dry_run:
                logger.info(f"Would create new facility: {facility.code} - {facility.name}")
                return False

            facility_db = Facility(
                code=facility.code,
                name=facility.name,
                network_id=facility.network_id,
                network_region=facility.network_region,
                description=facility.description,
                wikipedia_link=facility.wikipedia,
                website_url=facility.website,
                approved=True,
                cms_id=facility.cms_id,
            )
            facility_new = True
            session.add(facility_db)
            facility_db.units = []
            facility_or_unit_created = True
        else:
            facility_new = False

        if dry_run:
            logger.info(f"Would update facility: {facility.code} - {facility.name}")
            return False

        # Always update all facility metadata from CMS
        record_updated = False

        if facility.code and facility.code != facility_db.code:
            facility_db.code = facility.code
            record_updated = True

        if facility.network_id:
            facility_db.network_id = facility.network_id
            record_updated = True

        if facility.name:
            facility_db.name = facility.name.strip()
            record_updated = True

        if facility.network_region:
            facility_db.network_region = facility.network_region.strip().upper()
            record_updated = True

        if facility.wikipedia is not None:
            facility_db.wikipedia_link = facility.wikipedia.strip() if facility.wikipedia else None
            record_updated = True

        if facility.website is not None:
            facility_db.website_url = facility.website.strip() if facility.website else None
            record_updated = True

        if facility.description is not None:
            facility_db.description = facility.description
            record_updated = True

        if facility.cms_id:
            facility_db.cms_id = facility.cms_id
            record_updated = True

        # Process units in a single transaction
        for unit in facility.units:
            # First try to find unit by cms_id (primary identifier)
            unit_db = None
            if unit.cms_id:
                # Look for unit by cms_id across all facilities
                unit_query = select(Unit).where(Unit.cms_id == unit.cms_id)
                unit_db = (await session.execute(unit_query)).scalar_one_or_none()

                # If found in a different facility, move it
                if unit_db and unit_db.station_id != facility_db.id:
                    unit_db.station_id = facility_db.id
                    record_updated = True
                    logger.info(f"Moved unit {unit.code} to facility {facility.code} ({facility_db.id})")

            # If not found by cms_id, try by code (backward compatibility)
            if not unit_db:
                # First check in current facility's units
                existing_units = {u.code: u for u in facility_db.units}
                unit_db = existing_units.get(unit.code)

                if not unit_db:
                    # Check across all facilities
                    unit_query = select(Unit).where(Unit.code == unit.code)
                    unit_db = (await session.execute(unit_query)).scalar_one_or_none()

                    if unit_db and unit_db.station_id != facility_db.id:
                        unit_db.station_id = facility_db.id
                        record_updated = True
                        logger.info(f"Moved unit {unit.code} to facility {facility.code} ({facility_db.id})")

            # If still not found, create new unit
            if not unit_db:
                unit_db = Unit(
                    code=unit.code,
                    fueltech_id=unit.fueltech_id.value if unit.fueltech_id else None,
                    status_id=unit.status_id.value if unit.status_id else None,
                    dispatch_type=unit.dispatch_type.value if unit.dispatch_type else None,
                    capacity_registered=round(unit.capacity_registered, 2) if unit.capacity_registered else None,
                    emissions_factor_co2=round(unit.emissions_factor_co2, 4) if unit.emissions_factor_co2 else None,
                    expected_operation_date=unit.expected_operation_date,
                    expected_closure_date=unit.expected_closure_date,
                    commencement_date=unit.commencement_date,
                    closure_date=unit.closure_date,
                    registered=unit.commencement_date,
                    deregistered=unit.closure_date,
                    cms_id=unit.cms_id,
                )
                facility_db.units.append(unit_db)
                record_updated = True
                facility_or_unit_created = True
                logger.info(f"Created unit {unit.code} for facility {facility.code}")

            # Always update all unit metadata from CMS
            if unit.code:
                unit_db.code = unit.code
                record_updated = True

            if unit.fueltech_id:
                unit_db.fueltech_id = unit.fueltech_id.value
                record_updated = True

            if unit.status_id:
                unit_db.status_id = unit.status_id.value
                record_updated = True

            if unit.dispatch_type:
                unit_db.dispatch_type = unit.dispatch_type.value.upper()
                record_updated = True

            if unit.capacity_registered is not None:
                unit_db.capacity_registered = round(unit.capacity_registered, 2) if unit.capacity_registered else None
                record_updated = True

            if unit.emissions_factor_co2 is not None:
                unit_db.emissions_factor_co2 = round(unit.emissions_factor_co2, 4) if unit.emissions_factor_co2 else None
                record_updated = True

            if unit.expected_operation_date is not None:
                unit_db.expected_operation_date = unit.expected_operation_date
                record_updated = True

            if unit.expected_closure_date is not None:
                unit_db.expected_closure_date = unit.expected_closure_date
                record_updated = True

            if unit.commencement_date is not None:
                unit_db.commencement_date = unit.commencement_date
                unit_db.registered = unit.commencement_date
                record_updated = True

            if unit.closure_date is not None:
                unit_db.closure_date = unit.closure_date
                unit_db.deregistered = unit.closure_date
                record_updated = True

            if unit.cms_id:
                unit_db.cms_id = unit.cms_id
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


async def update_database_facilities_from_cms(
    send_slack: bool = True, dry_run: bool = False, facility_code: str | None = None
) -> None:
    """Update all database facilities from the CMS.

    This is the main function for synchronizing the entire database with the CMS.
    Since we use cms_id as the primary identifier, the create_or_update function
    handles all the logic for creating new facilities or updating existing ones.

    The function will:
    - Get all facilities from CMS
    - Create or update each facility in the database
    - Send Slack notifications about changes (if enabled)

    Args:
        send_slack: Whether to send Slack notifications about changes
        dry_run: If True, only check for differences without making changes
        facility_code: Optional specific facility code to update
    """
    # Get facilities from CMS
    sanity_facilities = get_cms_facilities(facility_code=facility_code)
    logger.info(f"Processing {len(sanity_facilities)} facilities from CMS")

    # Track statistics and created facility codes
    created_count = 0
    updated_count = 0
    created_facility_codes = []

    # Process each facility
    for facility in sanity_facilities:
        was_created = await create_or_update_database_facility(facility, send_slack=send_slack, dry_run=dry_run)
        if was_created:
            created_count += 1
            created_facility_codes.append(facility.code)
        else:
            updated_count += 1

    # Log summary
    if dry_run:
        logger.info(f"Dry run complete: Would create {created_count} facilities, update {updated_count} facilities")
    else:
        logger.info(f"Sync complete: {created_count} facilities created, {updated_count} facilities updated")

    # Update facility seen range for new facilities if any were created
    if created_count > 0 and not dry_run:
        await update_facility_seen_range(include_first_seen=True, facility_codes=created_facility_codes)


async def check_orphaned_facilities() -> list[str]:
    """Check for facilities that exist in the database but not in the CMS.

    This is a separate function for data quality monitoring to identify
    facilities that may need to be cleaned up or investigated.

    Returns:
        List of facility codes that exist in database but not in CMS
    """
    sanity_facilities = get_cms_facilities()
    database_facilities = await get_database_facilities()

    # Get all CMS facility codes
    cms_facility_codes = {facility.code.upper() for facility in sanity_facilities}

    # Find facilities in database but not in CMS
    orphaned_facilities = []
    for db_facility in database_facilities:
        if str(db_facility.code).upper() not in cms_facility_codes:
            orphaned_facilities.append(db_facility.code)

    if orphaned_facilities:
        logger.warning(f"Found {len(orphaned_facilities)} facilities in database but not in CMS:")
        for code in orphaned_facilities[:10]:  # Show first 10
            logger.warning(f"  - {code}")
        if len(orphaned_facilities) > 10:
            logger.warning(f"  ... and {len(orphaned_facilities) - 10} more")

    return orphaned_facilities


if __name__ == "__main__":
    import asyncio

    # opennem_stations = get_opennem_stations()
    asyncio.run(update_database_facilities_from_cms(send_slack=False))
    # asyncio.run(update_facility_from_cms(facility_code="0BSSF", send_slack=False))
