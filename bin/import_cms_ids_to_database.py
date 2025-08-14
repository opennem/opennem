#!/usr/bin/env python3
"""Import CMS IDs into database.

This one-off script imports cms_id values from the Sanity CMS into the OpenNEM database
for all facilities and units. It matches records by code and updates the cms_id field.
If a record exists in CMS but not in the database, it creates it.
If a record exists in the database but not in CMS, it reports it.
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem.cms.queries import get_cms_facilities
from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import Facility, Unit

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def get_all_database_facilities() -> list[Facility]:
    """Get all facilities with their units from the database."""
    async with get_read_session() as session:
        query = select(Facility).options(selectinload(Facility.units))
        # .where(Unit.fueltech_id.in_('solar_rooftop', 'imp'))
        result = await session.execute(query)
        facilities = result.scalars().unique().all()
    return facilities


async def check_cms_facilities_in_database() -> None:
    """Check which CMS facilities exist in the database and warn about missing ones.

    This method:
    1. Gets all facilities from CMS
    2. Attempts to find them in database by cms_id first
    3. If not found by cms_id, attempts to find by code
    4. Warns about facilities not found by cms_id
    5. Warns about facilities not found by code either
    """
    logger.info("Checking CMS facilities against database...")

    # Get facilities from CMS
    cms_facilities = get_cms_facilities()
    logger.info(f"Found {len(cms_facilities)} facilities in CMS")

    # Get all facilities from database
    db_facilities = await get_all_database_facilities()
    logger.info(f"Found {len(db_facilities)} facilities in database")

    # Create lookup dictionaries for database facilities
    db_facilities_by_cms_id = {f.cms_id: f for f in db_facilities if f.cms_id}
    db_facilities_by_code = {f.code: f for f in db_facilities}

    # Track statistics
    stats = {
        "found_by_cms_id": 0,
        "found_by_code_only": 0,
        "not_found_at_all": 0,
        "missing_cms_id": [],
        "missing_completely": [],
    }

    # Check each CMS facility
    for cms_facility in cms_facilities:
        # logger.info(f"\nChecking facility: {cms_facility.code} - {cms_facility.name}")
        # logger.info(f"  CMS ID: {cms_facility.cms_id}")

        # First try to find by cms_id
        db_facility_by_cms_id = db_facilities_by_cms_id.get(cms_facility.cms_id)

        if db_facility_by_cms_id:
            logger.info(
                f"{cms_facility.code} - {cms_facility.name}:  ✅ Found in database by cms_id: {db_facility_by_cms_id.cms_id}"
            )
            stats["found_by_cms_id"] += 1
        else:
            logger.warning(f"{cms_facility.code} - {cms_facility.name}:  ⚠️  CMS ID {cms_facility.cms_id} not found in database")  # noqa: E501
            stats["missing_cms_id"].append(cms_facility.code)

            # Try to find by code
            db_facility_by_code = db_facilities_by_code.get(cms_facility.code)

            if db_facility_by_code:
                logger.warning(f"  ⚠️  But found matching facility by code: {db_facility_by_code.code}")
                logger.warning(f"      Database facility cms_id: {db_facility_by_code.cms_id}")
                stats["found_by_code_only"] += 1
            else:
                logger.error("  ❌ No matching facility found by code either")
                stats["not_found_at_all"] += 1
                stats["missing_completely"].append(cms_facility.code)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("CMS FACILITIES CHECK SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total CMS facilities: {len(cms_facilities)}")
    logger.info(f"Found by cms_id: {stats['found_by_cms_id']}")
    logger.info(f"Found by code only (missing cms_id): {stats['found_by_code_only']}")
    logger.info(f"Not found at all: {stats['not_found_at_all']}")

    if stats["missing_cms_id"]:
        logger.warning(f"\nFacilities missing cms_id in database: {len(stats['missing_cms_id'])}")
        for code in sorted(stats["missing_cms_id"])[:20]:  # Show first 20
            logger.warning(f"  - {code}")
        if len(stats["missing_cms_id"]) > 20:
            logger.warning(f"  ... and {len(stats['missing_cms_id']) - 20} more")

    if stats["missing_completely"]:
        logger.error(f"\nFacilities completely missing from database: {len(stats['missing_completely'])}")
        for code in sorted(stats["missing_completely"])[:20]:  # Show first 20
            logger.error(f"  - {code}")
        if len(stats["missing_completely"]) > 20:
            logger.error(f"  ... and {len(stats['missing_completely']) - 20} more")


async def sync_cms_ids(facility_code: str | None = None, dry_run: bool = False) -> None:
    """Sync cms_id values from CMS to database.

    Args:
        facility_code: Optional facility code to sync only one facility (for testing)
        dry_run: If True, only log changes without making them
    """
    # Get facilities from CMS
    logger.info(f"Fetching facilities from CMS{f' (code: {facility_code})' if facility_code else ''}...")
    cms_facilities = get_cms_facilities(facility_code=facility_code)
    logger.info(f"Found {len(cms_facilities)} facilities in CMS")

    # Get all facilities from database
    logger.info("Fetching facilities from database...")
    db_facilities = await get_all_database_facilities()
    logger.info(f"Found {len(db_facilities)} facilities in database")

    # Create lookup dictionaries
    cms_facilities_by_code = {f.code: f for f in cms_facilities}

    # Track statistics
    stats = {
        "facilities_updated": 0,
        "facilities_created": 0,
        "units_updated": 0,
        "units_created": 0,
        "facilities_not_in_cms": [],
        "units_not_in_cms": [],
    }

    # First, check for database facilities not in CMS
    for db_facility in db_facilities:
        if db_facility.code not in cms_facilities_by_code:
            stats["facilities_not_in_cms"].append(db_facility.code)
            logger.warning(f"Facility {db_facility.code} exists in database but not in CMS")

    # Process each CMS facility
    async with get_write_session() as session:
        for cms_facility in cms_facilities:
            logger.info(f"\nProcessing facility: {cms_facility.code} - {cms_facility.name}")
            logger.info(f"  CMS ID: {cms_facility.cms_id}")

            # Find facility in database
            facility_query = select(Facility).options(selectinload(Facility.units)).where(Facility.code == cms_facility.code)
            db_facility = (await session.execute(facility_query)).scalars().unique().one_or_none()

            if db_facility:
                # Update existing facility
                if db_facility.cms_id != cms_facility.cms_id:
                    logger.info(f"  Updating facility cms_id: {db_facility.cms_id} -> {cms_facility.cms_id}")
                    if not dry_run:
                        db_facility.cms_id = cms_facility.cms_id
                    stats["facilities_updated"] += 1
                else:
                    logger.info("  Facility cms_id already up to date")
            else:
                # Create new facility
                logger.info(f"  Creating new facility: {cms_facility.code}")
                if not dry_run:
                    db_facility = Facility(
                        code=cms_facility.code,
                        name=cms_facility.name,
                        network_id=cms_facility.network_id,
                        network_region=cms_facility.network_region,
                        description=cms_facility.description,
                        wikipedia_link=cms_facility.wikipedia,
                        website_url=cms_facility.website,
                        approved=True,
                        cms_id=cms_facility.cms_id,
                    )
                    session.add(db_facility)
                stats["facilities_created"] += 1
                db_facility = None  # Reset for unit processing

            # Process units
            if cms_facility.units:
                logger.info(f"  Processing {len(cms_facility.units)} units...")

                # Get existing units for this facility
                existing_units = {}
                if db_facility:
                    existing_units = {u.code: u for u in db_facility.units}

                for cms_unit in cms_facility.units:
                    logger.info(f"    Unit: {cms_unit.code}")
                    logger.info(f"      CMS ID: {cms_unit.cms_id}")

                    # First check if unit exists in current facility
                    db_unit = existing_units.get(cms_unit.code)

                    if not db_unit:
                        # Check if unit exists elsewhere in database
                        unit_query = select(Unit).where(Unit.code == cms_unit.code)
                        db_unit = (await session.execute(unit_query)).scalar_one_or_none()

                        if db_unit:
                            logger.info(f"      Unit found in different facility (station_id: {db_unit.station_id})")

                    if db_unit:
                        # Update existing unit
                        if db_unit.cms_id != cms_unit.cms_id:
                            logger.info(f"      Updating unit cms_id: {db_unit.cms_id} -> {cms_unit.cms_id}")
                            if not dry_run:
                                db_unit.cms_id = cms_unit.cms_id
                            stats["units_updated"] += 1
                        else:
                            logger.info("      Unit cms_id already up to date")

                        # Update station_id if needed
                        if db_facility and db_unit.station_id != db_facility.id:
                            logger.info(f"      Moving unit to facility {cms_facility.code}")
                            if not dry_run:
                                db_unit.station_id = db_facility.id
                    else:
                        # Create new unit
                        logger.info(f"      Creating new unit: {cms_unit.code}")
                        if not dry_run and db_facility:
                            db_unit = Unit(
                                code=cms_unit.code,
                                fueltech_id=cms_unit.fueltech_id.value if cms_unit.fueltech_id else None,
                                status_id=cms_unit.status_id.value if cms_unit.status_id else None,
                                dispatch_type=cms_unit.dispatch_type.value if cms_unit.dispatch_type else None,
                                capacity_registered=round(cms_unit.capacity_registered, 2)
                                if cms_unit.capacity_registered
                                else None,
                                emissions_factor_co2=round(cms_unit.emissions_factor_co2, 4)
                                if cms_unit.emissions_factor_co2
                                else None,
                                expected_operation_date=cms_unit.expected_operation_date,
                                expected_closure_date=cms_unit.expected_closure_date,
                                commencement_date=cms_unit.commencement_date,
                                closure_date=cms_unit.closure_date,
                                registered=cms_unit.commencement_date,
                                deregistered=cms_unit.closure_date,
                                cms_id=cms_unit.cms_id,
                                station_id=db_facility.id,
                                approved=True,
                            )
                            session.add(db_unit)
                        stats["units_created"] += 1

        # Check for database units not in CMS
        cms_unit_codes = set()
        for cms_facility in cms_facilities:
            if cms_facility.units:
                cms_unit_codes.update(u.code for u in cms_facility.units)

        all_units_query = select(Unit)
        all_db_units = (await session.execute(all_units_query)).scalars().all()

        for db_unit in all_db_units:
            if db_unit.code not in cms_unit_codes:
                stats["units_not_in_cms"].append(db_unit.code)
                logger.warning(f"Unit {db_unit.code} exists in database but not in CMS")

        # Commit changes
        if not dry_run:
            await session.commit()
            logger.info("\nChanges committed to database")
        else:
            logger.info("\nDry run - no changes made")

    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Facilities updated with cms_id: {stats['facilities_updated']}")
    logger.info(f"Facilities created: {stats['facilities_created']}")
    logger.info(f"Units updated with cms_id: {stats['units_updated']}")
    logger.info(f"Units created: {stats['units_created']}")

    if stats["facilities_not_in_cms"]:
        logger.warning(f"\nFacilities in database but not in CMS: {len(stats['facilities_not_in_cms'])}")
        for code in sorted(stats["facilities_not_in_cms"])[:10]:  # Show first 10
            logger.warning(f"  - {code}")
        if len(stats["facilities_not_in_cms"]) > 10:
            logger.warning(f"  ... and {len(stats['facilities_not_in_cms']) - 10} more")

    if stats["units_not_in_cms"]:
        logger.warning(f"\nUnits in database but not in CMS: {len(stats['units_not_in_cms'])}")
        for code in sorted(stats["units_not_in_cms"])[:10]:  # Show first 10
            logger.warning(f"  - {code}")
        if len(stats["units_not_in_cms"]) > 10:
            logger.warning(f"  ... and {len(stats['units_not_in_cms']) - 10} more")


async def main():
    """Main function to run the import."""
    import argparse

    parser = argparse.ArgumentParser(description="Import CMS IDs into database")
    parser.add_argument("--facility-code", help="Process only a specific facility code (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be changed")
    parser.add_argument("--check-cms", action="store_true", help="Check which CMS facilities exist in database")

    args = parser.parse_args()

    if args.check_cms:
        await check_cms_facilities_in_database()
    else:
        # Test with specific facility code if provided
        if args.facility_code:
            logger.info(f"Testing with facility code: {args.facility_code}")

        await sync_cms_ids(facility_code=args.facility_code, dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
