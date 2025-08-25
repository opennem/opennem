#!/usr/bin/env python
"""
Import ALL unique NPI facilities from ALL XML files
This script ensures we capture every unique facility, including retired ones
"""

import asyncio
import logging
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from opennem.db import get_write_session
from opennem.db.models.npi import INITIAL_SUBSTANCES, NPIFacility, NPISubstance
from opennem.parsers.npi import parse_npi_xml

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def ensure_substances_exist():
    """Ensure all substances are in the database"""
    async with get_write_session() as session:
        for substance_data in INITIAL_SUBSTANCES:
            stmt = select(NPISubstance).where(NPISubstance.code == substance_data["code"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                substance = NPISubstance(
                    code=substance_data["code"],
                    npi_name=substance_data["npi_name"],
                    cas_number=substance_data.get("cas_number"),
                    category=substance_data["category"],
                    unit="kg",
                    enabled=True,
                )
                session.add(substance)
                logger.info(f"Added substance: {substance_data['code']}")

        await session.commit()


async def import_all_facilities():
    """Import all unique NPI facilities from all XML files"""

    # First ensure substances exist
    await ensure_substances_exist()

    # Parse all XML files and collect ALL unique facilities
    all_facilities = {}  # npi_id -> facility data

    xml_dir = Path("data/npi")
    xml_files = sorted(xml_dir.glob("*.xml"))

    logger.info(f"Processing {len(xml_files)} XML files...")

    for xml_file in xml_files:
        year = int(xml_file.stem)
        logger.info(f"Parsing {year}...")

        try:
            reports = parse_npi_xml(xml_file)
            logger.info(f"  Found {len(reports)} facilities in {year}")

            for report in reports:
                npi_id = report.jurisdiction_facility_id

                # Store facility, keeping the most recent version
                if npi_id not in all_facilities:
                    all_facilities[npi_id] = report
                    logger.debug(f"  New facility: {report.facility_name} ({npi_id})")
                elif report.report_year > all_facilities[npi_id].report_year:
                    old_name = all_facilities[npi_id].facility_name
                    all_facilities[npi_id] = report
                    if old_name != report.facility_name:
                        logger.debug(f"  Updated {npi_id}: {old_name} -> {report.facility_name}")

        except Exception as e:
            logger.error(f"Error processing {xml_file}: {e}")

    logger.info(f"\nFound {len(all_facilities)} unique facilities across all years")

    # Now import/update all facilities in the database
    created = 0
    updated = 0
    errors = 0

    async with get_write_session() as session:
        for npi_id, report in all_facilities.items():
            try:
                # Check if facility already exists
                stmt = select(NPIFacility).where(NPIFacility.npi_id == npi_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing facility with latest data
                    existing.npi_name = report.facility_name
                    existing.registered_business_name = report.registered_business_name
                    existing.abn = report.abn
                    existing.acn = report.acn
                    existing.site_latitude = Decimal(str(report.site_latitude)) if report.site_latitude else None
                    existing.site_longitude = Decimal(str(report.site_longitude)) if report.site_longitude else None
                    existing.location_state = report.site_address_state
                    existing.site_address_suburb = report.site_address_suburb
                    existing.site_address_postcode = report.site_address_postcode
                    existing.company_website = report.company_website
                    existing.number_of_employees = report.number_of_employees
                    existing.main_activities = report.main_activities
                    existing.report_year = report.report_year
                    existing.data_start_date = report.data_start_date
                    existing.data_end_date = report.data_end_date
                    updated += 1
                    logger.debug(f"Updated: {report.facility_name} ({npi_id})")
                else:
                    # Create new facility
                    new_facility = NPIFacility(
                        npi_id=npi_id,
                        npi_name=report.facility_name,
                        registered_business_name=report.registered_business_name,
                        abn=report.abn,
                        acn=report.acn,
                        site_latitude=Decimal(str(report.site_latitude)) if report.site_latitude else None,
                        site_longitude=Decimal(str(report.site_longitude)) if report.site_longitude else None,
                        location_state=report.site_address_state,
                        site_address_suburb=report.site_address_suburb,
                        site_address_postcode=report.site_address_postcode,
                        company_website=report.company_website,
                        number_of_employees=report.number_of_employees,
                        main_activities=report.main_activities,
                        report_year=report.report_year,
                        data_start_date=report.data_start_date,
                        data_end_date=report.data_end_date,
                    )
                    session.add(new_facility)
                    created += 1
                    logger.info(f"Created: {report.facility_name} ({npi_id})")

            except Exception as e:
                logger.error(f"Error processing {npi_id}: {e}")
                errors += 1

        # Commit all changes
        await session.commit()
        logger.info("\nDatabase update complete!")

    # Final report
    logger.info("\n" + "=" * 60)
    logger.info("IMPORT SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total unique facilities found: {len(all_facilities)}")
    logger.info(f"Facilities created: {created}")
    logger.info(f"Facilities updated: {updated}")
    logger.info(f"Errors: {errors}")
    logger.info(f"Total in database: {created + updated}")

    # Verify final count
    async with get_write_session() as session:
        final_count = await session.scalar(select(func.count()).select_from(NPIFacility))
        logger.info(f"Verified database count: {final_count}")

    return {"total_found": len(all_facilities), "created": created, "updated": updated, "errors": errors}


if __name__ == "__main__":
    from sqlalchemy import func

    asyncio.run(import_all_facilities())
