"""
NPI Pollution Data Controller

Handles importing and storing NPI pollution data
"""

import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from opennem.db import get_write_session
from opennem.db.models.npi import (
    INITIAL_SUBSTANCES,
    NPIFacility,
    NPIPollution,
    NPISubstance,
)
from opennem.db.models.opennem import Facility
from opennem.parsers.npi import NPIFacilityReport, parse_npi_xml

logger = logging.getLogger("opennem.controllers.npi")


async def seed_npi_substances(session: AsyncSession | None = None) -> int:
    """
    Seed the NPI substances table with initial data

    Returns:
        Number of substances added
    """
    added_count = 0

    if session:
        # Use provided session
        for substance_data in INITIAL_SUBSTANCES:
            # Check if substance already exists
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
                added_count += 1
                logger.info(f"Added substance: {substance_data['code']} - {substance_data['npi_name']}")
    else:
        # Create own session
        async with get_write_session() as session:
            for substance_data in INITIAL_SUBSTANCES:
                # Check if substance already exists
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
                    added_count += 1
                    logger.info(f"Added substance: {substance_data['code']} - {substance_data['npi_name']}")

            await session.commit()

    logger.info(f"Seeded {added_count} NPI substances")
    return added_count


async def import_npi_facility(npi_report: NPIFacilityReport, session: AsyncSession) -> NPIFacility:
    """
    Import or update an NPI facility record

    Args:
        npi_report: NPI facility report to import
        session: Database session

    Returns:
        NPIFacility record
    """
    # Check if NPI facility already exists
    stmt = select(NPIFacility).where(NPIFacility.npi_id == npi_report.jurisdiction_facility_id)
    result = await session.execute(stmt)
    npi_facility = result.scalar_one_or_none()

    if not npi_facility:
        # Create new NPI facility record
        npi_facility = NPIFacility(
            npi_id=npi_report.jurisdiction_facility_id,
            npi_name=npi_report.facility_name,
            registered_business_name=npi_report.registered_business_name,
            abn=npi_report.abn,
            acn=npi_report.acn,
            site_latitude=Decimal(str(npi_report.site_latitude)) if npi_report.site_latitude else None,
            site_longitude=Decimal(str(npi_report.site_longitude)) if npi_report.site_longitude else None,
            location_state=npi_report.site_address_state,
            site_address_suburb=npi_report.site_address_suburb,
            site_address_postcode=npi_report.site_address_postcode,
            company_website=npi_report.company_website,
            number_of_employees=npi_report.number_of_employees,
            main_activities=npi_report.main_activities,
            report_year=npi_report.report_year,
            data_start_date=npi_report.data_start_date,
            data_end_date=npi_report.data_end_date,
        )
        session.add(npi_facility)
        logger.info(f"Created new NPI facility: {npi_report.facility_name}")
    else:
        # Update existing record with latest data
        npi_facility.npi_name = npi_report.facility_name
        npi_facility.registered_business_name = npi_report.registered_business_name
        npi_facility.abn = npi_report.abn
        npi_facility.acn = npi_report.acn
        npi_facility.site_latitude = Decimal(str(npi_report.site_latitude)) if npi_report.site_latitude else None
        npi_facility.site_longitude = Decimal(str(npi_report.site_longitude)) if npi_report.site_longitude else None
        npi_facility.location_state = npi_report.site_address_state
        npi_facility.site_address_suburb = npi_report.site_address_suburb
        npi_facility.site_address_postcode = npi_report.site_address_postcode
        npi_facility.company_website = npi_report.company_website
        npi_facility.number_of_employees = npi_report.number_of_employees
        npi_facility.main_activities = npi_report.main_activities
        npi_facility.report_year = npi_report.report_year
        npi_facility.data_start_date = npi_report.data_start_date
        npi_facility.data_end_date = npi_report.data_end_date
        logger.info(f"Updated NPI facility: {npi_report.facility_name}")

    return npi_facility


async def import_npi_pollution_data(npi_report: NPIFacilityReport, npi_facility: NPIFacility, session: AsyncSession) -> int:
    """
    Import pollution data for an NPI facility

    Args:
        npi_report: NPI facility report with pollution data
        npi_facility: NPIFacility database record
        session: Database session

    Returns:
        Number of pollution records imported
    """
    imported_count = 0

    # Get all enabled substances
    stmt = select(NPISubstance).where(NPISubstance.enabled.is_(True))
    result = await session.execute(stmt)
    substances_dict = {s.npi_name: s.code for s in result.scalars().all()}

    # Process each reported substance
    for substance_data in npi_report.substances:
        # Skip if substance not in our tracking list
        if substance_data.name not in substances_dict:
            continue

        substance_code = substances_dict[substance_data.name]

        # Determine pollution category and subcategory
        pollution_category = "air"  # Default
        pollution_subcategory = "total"  # Default

        destination_lower = substance_data.destination.lower()
        if "water" in destination_lower:
            pollution_category = "water"
        elif "land" in destination_lower:
            pollution_category = "land"

        if "point" in destination_lower:
            pollution_subcategory = "point"
        elif "fugitive" in destination_lower:
            pollution_subcategory = "fugitive"
        elif "total" in destination_lower:
            pollution_subcategory = "total"

        # Skip non-total values for now (we'll aggregate point + fugitive = total)
        if pollution_subcategory != "total":
            continue

        # Check if pollution record already exists
        stmt = select(NPIPollution).where(
            NPIPollution.npi_facility_id == npi_facility.npi_id,
            NPIPollution.substance_code == substance_code,
            NPIPollution.report_year == npi_report.report_year,
            NPIPollution.pollution_category == pollution_category,
            NPIPollution.pollution_subcategory == pollution_subcategory,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            existing.pollution_value = substance_data.quantity_kg
            logger.debug(f"Updated pollution record for {npi_facility.npi_name} - {substance_data.name}")
        else:
            # Create new pollution record
            pollution_record = NPIPollution(
                npi_facility_id=npi_facility.npi_id,
                substance_code=substance_code,
                report_year=npi_report.report_year,
                pollution_category=pollution_category,
                pollution_subcategory=pollution_subcategory,
                pollution_value=substance_data.quantity_kg,
                pollution_unit="kg",
            )

            # Determine data quality based on estimation methods
            if substance_data.direct_measurement:
                pollution_record.data_quality = "measured"
            elif substance_data.engineering_calc:
                pollution_record.data_quality = "calculated"
            elif substance_data.emission_factors:
                pollution_record.data_quality = "emission_factors"
            else:
                pollution_record.data_quality = "estimated"

            session.add(pollution_record)
            imported_count += 1

    return imported_count


async def import_npi_xml_file(file_path: Path | str, dry_run: bool = False) -> dict[str, Any]:
    """
    Import NPI data from an XML file

    Note: This only imports the data. Use bin/map_npi_facilities.py to map facilities to OpenNEM.

    Args:
        file_path: Path to the NPI XML file
        dry_run: If True, don't commit changes

    Returns:
        Dictionary with import statistics
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    logger.info(f"Importing NPI data from {file_path}")

    # Parse the XML file
    reports = parse_npi_xml(file_path)
    logger.info(f"Parsed {len(reports)} facility reports")

    # Ensure substances are seeded first
    await seed_npi_substances()

    stats = {
        "total_reports": len(reports),
        "facilities_created": 0,
        "facilities_updated": 0,
        "pollution_records_imported": 0,
        "errors": [],
    }

    async with get_write_session() as session:
        for report in reports:
            try:
                # Import NPI facility
                npi_facility = await import_npi_facility(report, session)

                # Check if it's new or updated
                await session.flush()
                if session.new and npi_facility in session.new:
                    stats["facilities_created"] += 1
                else:
                    stats["facilities_updated"] += 1

                # Import pollution data
                imported = await import_npi_pollution_data(report, npi_facility, session)
                stats["pollution_records_imported"] += imported

            except Exception as e:
                logger.error(f"Error importing facility {report.facility_name}: {e}")
                stats["errors"].append(f"{report.facility_name}: {str(e)}")

        if dry_run:
            logger.info("Dry run - rolling back transaction")
            await session.rollback()
        else:
            await session.commit()
            logger.info("Import complete - transaction committed")

    return stats


async def import_all_npi_historical_data(
    data_dir: Path | str = "data/npi", years: list[int] | None = None, dry_run: bool = False
) -> dict[str, Any]:
    """
    Import all historical NPI data from multiple XML files

    This will process all unique facilities across all years, ensuring
    retired facilities are captured even if they only appear in older data.

    Args:
        data_dir: Directory containing NPI XML files
        years: Optional list of specific years to import (default: all available)
        dry_run: If True, don't commit changes

    Returns:
        Dictionary with aggregated import statistics
    """
    if isinstance(data_dir, str):
        data_dir = Path(data_dir)

    # Find all XML files
    xml_files = sorted(data_dir.glob("*.xml"))

    if years:
        # Filter to specific years if requested
        xml_files = [f for f in xml_files if int(f.stem) in years]

    logger.info(f"Found {len(xml_files)} NPI data files to import")

    # Track unique facilities across all years
    all_facilities = {}  # npi_id -> facility data
    total_stats = {
        "files_processed": 0,
        "total_facilities": 0,
        "unique_facilities": 0,
        "facilities_created": 0,
        "facilities_updated": 0,
        "pollution_records_imported": 0,
        "years_covered": [],
        "errors": [],
    }

    # First pass: collect all unique facilities
    for xml_file in xml_files:
        year = int(xml_file.stem)
        total_stats["years_covered"].append(year)

        logger.info(f"Processing year {year} from {xml_file}")

        try:
            reports = parse_npi_xml(xml_file)
            total_stats["total_facilities"] += len(reports)

            for report in reports:
                # Store the most recent version of each facility
                if report.jurisdiction_facility_id not in all_facilities:
                    all_facilities[report.jurisdiction_facility_id] = report
                elif report.report_year > all_facilities[report.jurisdiction_facility_id].report_year:
                    # Update with more recent data
                    all_facilities[report.jurisdiction_facility_id] = report

        except Exception as e:
            logger.error(f"Error processing {xml_file}: {e}")
            total_stats["errors"].append(f"{xml_file.name}: {str(e)}")

    total_stats["unique_facilities"] = len(all_facilities)
    logger.info(f"Found {len(all_facilities)} unique facilities across all years")

    # Ensure substances are seeded first
    await seed_npi_substances()

    # Second pass: import all unique facilities and their pollution data
    async with get_write_session() as session:
        for _npi_id, facility_report in all_facilities.items():
            try:
                # Import the facility record
                npi_facility = await import_npi_facility(facility_report, session)

                # Check if it's new or updated
                await session.flush()
                if session.new and npi_facility in session.new:
                    total_stats["facilities_created"] += 1
                else:
                    total_stats["facilities_updated"] += 1

            except Exception as e:
                logger.error(f"Error importing facility {facility_report.facility_name}: {e}")
                total_stats["errors"].append(f"{facility_report.facility_name}: {str(e)}")

        # Now import pollution data from all years
        for xml_file in xml_files:
            year = int(xml_file.stem)
            logger.info(f"Importing pollution data for year {year}")

            try:
                reports = parse_npi_xml(xml_file)

                for report in reports:
                    # Get the facility from DB
                    stmt = select(NPIFacility).where(NPIFacility.npi_id == report.jurisdiction_facility_id)
                    result = await session.execute(stmt)
                    npi_facility = result.scalar_one_or_none()

                    if npi_facility:
                        # Import pollution data for this year
                        imported = await import_npi_pollution_data(report, npi_facility, session)
                        total_stats["pollution_records_imported"] += imported

            except Exception as e:
                logger.error(f"Error importing pollution data from {xml_file}: {e}")
                total_stats["errors"].append(f"{xml_file.name} pollution data: {str(e)}")

        total_stats["files_processed"] = len(xml_files)

        if dry_run:
            logger.info("Dry run - rolling back transaction")
            await session.rollback()
        else:
            await session.commit()
            logger.info("Import complete - transaction committed")

    # Log summary
    logger.info("Import Summary:")
    logger.info(f"  Files processed: {total_stats['files_processed']}")
    logger.info(f"  Years covered: {min(total_stats['years_covered'])} - {max(total_stats['years_covered'])}")
    logger.info(f"  Total facility records: {total_stats['total_facilities']}")
    logger.info(f"  Unique facilities: {total_stats['unique_facilities']}")
    logger.info(f"  Facilities created: {total_stats['facilities_created']}")
    logger.info(f"  Facilities updated: {total_stats['facilities_updated']}")
    logger.info(f"  Pollution records: {total_stats['pollution_records_imported']}")
    logger.info(f"  Errors: {len(total_stats['errors'])}")

    return total_stats


async def get_facility_pollution(facility_code: str, year: int | None = None) -> list[dict[str, Any]]:
    """
    Get pollution data for a facility

    Args:
        facility_code: OpenNEM facility code
        year: Optional year filter

    Returns:
        List of pollution records
    """
    async with get_write_session() as session:
        # Get the facility's NPI ID
        stmt = select(Facility).where(Facility.code == facility_code)
        result = await session.execute(stmt)
        facility = result.scalar_one_or_none()

        if not facility or not facility.npi_id:
            return []

        # Build query for pollution data
        stmt = (
            select(NPIPollution, NPISubstance)
            .join(NPISubstance, NPIPollution.substance_code == NPISubstance.code)
            .where(NPIPollution.npi_facility_id == facility.npi_id)
            .options(selectinload(NPIPollution.substance))
        )

        if year:
            stmt = stmt.where(NPIPollution.report_year == year)

        stmt = stmt.order_by(NPIPollution.report_year.desc(), NPISubstance.npi_name)

        result = await session.execute(stmt)
        records = result.all()

        # Format results
        pollution_data = []
        for pollution, substance in records:
            pollution_data.append(
                {
                    "year": pollution.report_year,
                    "substance_code": substance.code,
                    "substance_name": substance.npi_name,
                    "category": substance.category,
                    "pollution_category": pollution.pollution_category,
                    "value_kg": float(pollution.pollution_value),
                    "data_quality": pollution.data_quality,
                }
            )

        return pollution_data


async def get_npi_facility_by_id(npi_id: str) -> dict[str, Any] | None:
    """
    Get NPI facility information by ID

    Args:
        npi_id: NPI facility ID

    Returns:
        Facility information or None
    """
    async with get_write_session() as session:
        stmt = select(NPIFacility).where(NPIFacility.npi_id == npi_id)
        result = await session.execute(stmt)
        facility = result.scalar_one_or_none()

        if not facility:
            return None

        return {
            "npi_id": facility.npi_id,
            "npi_name": facility.npi_name,
            "registered_business_name": facility.registered_business_name,
            "abn": facility.abn,
            "acn": facility.acn,
            "location": {
                "latitude": float(facility.site_latitude) if facility.site_latitude else None,
                "longitude": float(facility.site_longitude) if facility.site_longitude else None,
                "state": facility.location_state,
                "suburb": facility.site_address_suburb,
                "postcode": facility.site_address_postcode,
            },
            "company_website": facility.company_website,
            "number_of_employees": facility.number_of_employees,
            "main_activities": facility.main_activities,
            "report_year": facility.report_year,
        }
