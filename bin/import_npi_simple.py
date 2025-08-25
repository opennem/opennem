#!/usr/bin/env python
"""
Simple import of NPI pollution data year by year
"""

import asyncio
import logging
from pathlib import Path

from sqlalchemy import select

from opennem.controllers.npi import seed_npi_substances
from opennem.db import get_write_session
from opennem.db.models.npi import NPIFacility, NPIPollution, NPISubstance
from opennem.parsers.npi import parse_npi_xml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def import_year(year: int, data_dir: Path):
    """Import data for a single year"""
    xml_file = data_dir / f"{year}.xml"

    if not xml_file.exists():
        logger.warning(f"File not found: {xml_file}")
        return 0

    logger.info(f"Processing {year} from {xml_file}")

    try:
        reports = parse_npi_xml(xml_file)
        logger.info(f"  Found {len(reports)} facility reports for {year}")

        pollution_count = 0

        async with get_write_session() as session:
            for report in reports:
                # Check if facility exists
                facility = await session.scalar(select(NPIFacility).where(NPIFacility.npi_id == report.jurisdiction_facility_id))

                if not facility:
                    # Create new facility
                    facility = NPIFacility(
                        npi_id=report.jurisdiction_facility_id,
                        npi_name=report.facility_name,
                        registered_business_name=report.registered_business_name,
                        abn=report.abn,
                        acn=report.acn,
                        site_latitude=report.site_latitude,
                        site_longitude=report.site_longitude,
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
                    session.add(facility)
                    await session.flush()

                # Import pollution data
                for emission in report.substances:
                    # Get substance
                    substance = await session.scalar(select(NPISubstance).where(NPISubstance.npi_name == emission.name))

                    if not substance:
                        logger.warning(f"  Substance not found: {emission.name}")
                        continue

                    # Determine pollution category from destination
                    category = (
                        "air" if "Air" in emission.destination else ("water" if "Water" in emission.destination else "land")
                    )

                    # Check if pollution record exists
                    existing = await session.scalar(
                        select(NPIPollution).where(
                            NPIPollution.npi_facility_id == facility.npi_id,
                            NPIPollution.substance_code == substance.code,
                            NPIPollution.report_year == year,
                            NPIPollution.pollution_category == category,
                        )
                    )

                    if not existing:
                        pollution = NPIPollution(
                            npi_facility_id=facility.npi_id,
                            substance_code=substance.code,
                            report_year=year,
                            pollution_category=category,
                            pollution_value=float(emission.quantity_kg),
                        )
                        session.add(pollution)
                        pollution_count += 1

            await session.commit()
            logger.info(f"  Imported {pollution_count} pollution records for {year}")

        return pollution_count

    except Exception as e:
        logger.error(f"Error processing {year}: {e}")
        return 0


async def main():
    """Import all years of NPI data"""
    data_dir = Path("data/npi")

    # Ensure substances are seeded
    logger.info("Seeding NPI substances...")
    await seed_npi_substances()

    # Import years from oldest to newest
    years = list(range(1998, 2024))  # 1998-2023

    total_records = 0
    for year in years:
        count = await import_year(year, data_dir)
        total_records += count

    logger.info(f"Import complete! Total pollution records imported: {total_records}")


if __name__ == "__main__":
    asyncio.run(main())
