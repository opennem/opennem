#!/usr/bin/env python
"""
Import NPI pollution data with substance name mapping
"""

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select

from opennem.db import get_write_session
from opennem.db.models.npi import NPIFacility, NPIPollution, NPISubstance
from opennem.parsers.npi import parse_npi_xml

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_substance_mapping():
    """Load substance name mappings from JSON file"""
    mapping_file = Path("opennem/data/npi_substance_mapping.json")
    if mapping_file.exists():
        with open(mapping_file) as f:
            data = json.load(f)
            return data.get("substance_mappings", {})
    return {}


async def import_year_with_mapping(year: int, data_dir: Path, substance_mapping: dict, dry_run: bool = False):
    """Import data for a single year with substance name mapping"""
    xml_file = data_dir / f"{year}.xml"

    if not xml_file.exists():
        logger.warning(f"File not found: {xml_file}")
        return 0, 0, []

    logger.info(f"Processing {year} from {xml_file}")

    try:
        reports = parse_npi_xml(xml_file)
        logger.info(f"  Found {len(reports)} facility reports for {year}")

        pollution_count = 0
        skipped_count = 0
        unmapped_substances = set()

        async with get_write_session() as session:
            # Get all substances from DB
            db_substances = await session.execute(select(NPISubstance.npi_name, NPISubstance.code))
            substance_map = dict(db_substances)

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
                    # Try to map the substance name
                    substance_name = emission.name

                    # First check if it's already in DB
                    if substance_name in substance_map:
                        substance_code = substance_map[substance_name]
                    # Then check if we have a mapping for it
                    elif substance_name in substance_mapping:
                        mapped_name = substance_mapping[substance_name]
                        if mapped_name in substance_map:
                            substance_code = substance_map[mapped_name]
                            logger.debug(f"    Mapped '{substance_name}' -> '{mapped_name}'")
                        else:
                            unmapped_substances.add(substance_name)
                            skipped_count += 1
                            continue
                    else:
                        unmapped_substances.add(substance_name)
                        skipped_count += 1
                        continue

                    # Determine pollution category from destination
                    category = (
                        "air" if "Air" in emission.destination else ("water" if "Water" in emission.destination else "land")
                    )

                    # Check if pollution record exists
                    existing = await session.scalar(
                        select(NPIPollution).where(
                            NPIPollution.npi_facility_id == facility.npi_id,
                            NPIPollution.substance_code == substance_code,
                            NPIPollution.report_year == year,
                            NPIPollution.pollution_category == category,
                        )
                    )

                    if not existing:
                        pollution = NPIPollution(
                            npi_facility_id=facility.npi_id,
                            substance_code=substance_code,
                            report_year=year,
                            pollution_category=category,
                            pollution_value=float(emission.quantity_kg),
                        )
                        session.add(pollution)
                        pollution_count += 1

            if not dry_run:
                await session.commit()
                logger.info(f"  Imported {pollution_count} pollution records for {year}")
            else:
                logger.info(f"  [DRY RUN] Would import {pollution_count} pollution records for {year}")

            if skipped_count > 0:
                logger.warning(f"  Skipped {skipped_count} emissions due to unmapped substances")

            if unmapped_substances:
                logger.info(f"  Unmapped substances ({len(unmapped_substances)}): {sorted(unmapped_substances)[:5]}...")

        return pollution_count, skipped_count, list(unmapped_substances)

    except Exception as e:
        logger.error(f"Error processing {year}: {e}")
        import traceback

        traceback.print_exc()
        return 0, 0, []


async def main():
    """Import all years of NPI data with substance mapping"""
    data_dir = Path("data/npi")

    # Load substance mappings
    substance_mapping = load_substance_mapping()
    logger.info(f"Loaded {len(substance_mapping)} substance mappings")

    # Import years from oldest to newest
    years = list(range(1998, 2024))  # 1998-2023

    total_imported = 0
    total_skipped = 0
    all_unmapped = set()

    for year in years:
        imported, skipped, unmapped = await import_year_with_mapping(year, data_dir, substance_mapping, dry_run=False)
        total_imported += imported
        total_skipped += skipped
        all_unmapped.update(unmapped)

    logger.info("=" * 80)
    logger.info("Import complete!")
    logger.info(f"Total pollution records imported: {total_imported}")
    logger.info(f"Total emissions skipped: {total_skipped}")

    if all_unmapped:
        logger.info(f"Unique unmapped substances ({len(all_unmapped)}):")
        for substance in sorted(all_unmapped)[:20]:
            logger.info(f"  - {substance}")


if __name__ == "__main__":
    asyncio.run(main())
