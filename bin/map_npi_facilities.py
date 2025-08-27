#!/usr/bin/env python
"""
Map NPI facilities to OpenNEM facilities

This script handles the one-time mapping of NPI facilities to OpenNEM facilities
using fuzzy string matching and other heuristics.

Dependencies (dev only):
    - fuzzywuzzy
    - python-Levenshtein

Usage:
    python bin/map_npi_facilities.py --input data/npi-data-facilities-2024.xml --output data/npi_mapping_report.txt
"""

import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from fuzzywuzzy import fuzz
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from opennem.db import get_write_session
from opennem.db.models.npi import NPIFacility
from opennem.db.models.opennem import Facility, Unit
from opennem.parsers.npi import parse_npi_xml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carbon-based fuel techs that should be mapped to NPI facilities
CARBON_FUELTECHS = [
    "coal_black",
    "coal_brown",
    "gas_ccgt",
    "gas_ocgt",
    "gas_recip",
    "gas_steam",
    "gas_wcmg",
    "distillate",
    "bioenergy_biomass",
    "bioenergy_biogas",
]


async def get_carbon_fuel_facilities(session):
    """Get all facilities that have units with carbon-based fuel techs"""
    stmt = (
        select(Facility)
        .options(selectinload(Facility.units))
        .join(Unit, Facility.id == Unit.station_id)
        .where(Unit.fueltech_id.in_(CARBON_FUELTECHS))
        .distinct()
    )

    result = await session.execute(stmt)
    return result.scalars().all()


def calculate_match_score(npi_report, facility):
    """Calculate matching score between NPI report and OpenNEM facility"""
    # FIRST CHECK: State must match - if not, return 0
    if npi_report.site_address_state and facility.network_region:
        region_to_state = {
            "NSW1": "NSW",
            "QLD1": "QLD",
            "VIC1": "VIC",
            "SA1": "SA",
            "TAS1": "TAS",
            "WEM": "WA",  # Western Australia
            "WA1": "WA",  # Also Western Australia (older code)
        }
        facility_state = region_to_state.get(facility.network_region, "")

        # If states don't match, return 0 - no cross-state matching!
        if facility_state and npi_report.site_address_state and facility_state != npi_report.site_address_state:
            return 0.0

    # Clean up the NPI facility name - remove company names and suffixes
    npi_name_clean = npi_report.facility_name.lower().strip()

    # Remove company prefixes/suffixes
    company_terms = [
        "energyaustralia",
        "truenergy",
        "agl",
        "origin",
        "alinta",
        "engie",
        "edf",
        "cs energy",
        "stanwell",
        "ratch",
        "pty ltd",
        "pty",
        "ltd",
        "limited",
        "corporation",
        "partnership",
    ]
    for term in company_terms:
        npi_name_clean = npi_name_clean.replace(term, "").strip()

    # Remove facility type suffixes
    for suffix in [
        "gas turbine station",
        "power station",
        "power plant",
        "ps",
        "energy facility",
        "renewable energy facility",
        "power project",
        "cogeneration plant",
        "cogen",
    ]:
        npi_name_clean = npi_name_clean.replace(suffix, "").strip()

    # Clean up OpenNEM facility name
    facility_name_clean = facility.name.lower().strip()
    for suffix in ["power station", "power plant", "ps", "energy facility", "renewable energy facility"]:
        facility_name_clean = facility_name_clean.replace(suffix, "").strip()

    # Special handling for numbered facilities (e.g., Braemar vs Braemar 2)
    # Extract numbers and letters from both names
    import re

    # Check for numbers at the end of names
    npi_match = re.match(r"^(.*?)\s*(\d+|[a-d])?\s*$", npi_name_clean)
    facility_match = re.match(r"^(.*?)\s*(\d+|[a-d])?\s*$", facility_name_clean)

    if npi_match and facility_match:
        npi_base = npi_match.group(1).strip()
        npi_suffix = npi_match.group(2) or ""
        facility_base = facility_match.group(1).strip()
        facility_suffix = facility_match.group(2) or ""

        # If base names are very similar but suffixes don't match, heavily penalize
        if fuzz.ratio(npi_base, facility_base) > 85:
            if npi_suffix != facility_suffix:
                # Strong penalty for mismatched numbers/letters
                # e.g., "Braemar" should not match "Braemar 2"
                if (
                    (npi_suffix and not facility_suffix)
                    or (not npi_suffix and facility_suffix)
                    or (npi_suffix != facility_suffix)
                ):
                    return fuzz.ratio(npi_base, facility_base) / 100.0 * 0.3  # Heavy penalty

    # Calculate name similarity
    name_score = fuzz.ratio(npi_name_clean, facility_name_clean) / 100.0

    # Bonus for exact match (including numbers)
    if npi_name_clean == facility_name_clean:
        return 1.0

    # Bonus for exact word matches
    npi_words = set(npi_name_clean.split())
    facility_words = set(facility_name_clean.split())
    common_words = npi_words.intersection(facility_words)
    if common_words:
        # Give strong bonus for matching key words
        word_bonus = len(common_words) / max(len(npi_words), len(facility_words)) * 0.3
        name_score = min(name_score + word_bonus, 1.0)

    return name_score


async def map_npi_facilities(xml_source, output_file=None, apply_mapping=False, threshold=0.7):
    """
    Map NPI facilities to OpenNEM facilities

    Args:
        xml_source: Path to NPI XML file or directory containing multiple XML files
        output_file: Optional output file for mapping report
        apply_mapping: If True, update the database with mappings
        threshold: Minimum score threshold for automatic mapping
    """
    xml_source = Path(xml_source)

    # Collect all NPI reports from file(s)
    all_reports = {}  # npi_id -> most recent report

    if xml_source.is_file():
        # Single file
        logger.info(f"Parsing NPI data from {xml_source}")
        reports = parse_npi_xml(xml_source)
        for report in reports:
            all_reports[report.jurisdiction_facility_id] = report
    elif xml_source.is_dir():
        # Directory of files
        xml_files = sorted(xml_source.glob("*.xml"))
        logger.info(f"Processing {len(xml_files)} NPI data files")

        for xml_file in xml_files:
            try:
                year = int(xml_file.stem)
                logger.info(f"Processing year {year}")
                reports = parse_npi_xml(xml_file)

                for report in reports:
                    # Keep the most recent version of each facility
                    if report.jurisdiction_facility_id not in all_reports:
                        all_reports[report.jurisdiction_facility_id] = report
                    elif report.report_year > all_reports[report.jurisdiction_facility_id].report_year:
                        all_reports[report.jurisdiction_facility_id] = report

            except Exception as e:
                logger.error(f"Error processing {xml_file}: {e}")
    else:
        raise ValueError(f"Invalid path: {xml_source}")

    # Convert back to list
    reports = list(all_reports.values())
    logger.info(f"Found {len(reports)} unique NPI facilities across all years")

    # Start report
    report_lines = []
    report_lines.append("NPI Facility Mapping Report")
    report_lines.append(f"Generated: {datetime.now()}")
    report_lines.append(f"Source: {xml_source}")
    report_lines.append(f"Unique facilities: {len(reports)}")
    report_lines.append(f"Threshold: {threshold}")
    report_lines.append(f"Apply Mapping: {apply_mapping}")
    report_lines.append("=" * 80)

    async with get_write_session() as session:
        # Get carbon fuel facilities
        carbon_facilities = await get_carbon_fuel_facilities(session)
        logger.info(f"Found {len(carbon_facilities)} carbon fuel facilities in OpenNEM")

        mapped_count = 0
        unmapped_carbon = []

        for report in reports:
            report_lines.append(f"\nNPI Facility: {report.facility_name} ({report.jurisdiction_facility_id})")
            report_lines.append(f"State: {report.site_address_state}, Location: {report.site_address_suburb}")
            report_lines.append(f"Business: {report.registered_business_name}")

            # Find best matches
            matches = []
            for facility in carbon_facilities:
                if not facility.name:
                    continue

                score = calculate_match_score(report, facility)
                fuel_types = list({u.fueltech_id for u in facility.units if u.fueltech_id in CARBON_FUELTECHS})

                matches.append({"facility": facility, "score": score, "fuel_types": fuel_types})

            # Sort by score
            matches.sort(key=lambda x: x["score"], reverse=True)

            # Show top 5 matches
            report_lines.append("\nTop matches:")
            for match in matches[:5]:
                report_lines.append(
                    f"  {match['score']:.2f} - {match['facility'].name} ({match['facility'].code}) - {match['fuel_types']}"
                )

            # Apply mapping if score is above threshold
            best_match = matches[0] if matches else None
            if best_match and best_match["score"] >= threshold:
                report_lines.append(
                    f"\n✓ MATCHED to {best_match['facility'].name} "
                    f"({best_match['facility'].code}) with score {best_match['score']:.2f}"
                )
                mapped_count += 1

                if apply_mapping:
                    # Check if NPI facility exists
                    stmt = select(NPIFacility).where(NPIFacility.npi_id == report.jurisdiction_facility_id)
                    result = await session.execute(stmt)
                    npi_facility = result.scalar_one_or_none()

                    if npi_facility:
                        # Check if this NPI ID is already mapped to another facility
                        stmt = select(Facility).where(Facility.npi_id == report.jurisdiction_facility_id)
                        result = await session.execute(stmt)
                        existing_mapping = result.scalar_one_or_none()

                        if existing_mapping:
                            logger.warning(
                                f"NPI ID {report.jurisdiction_facility_id} already mapped to "
                                f"{existing_mapping.name} ({existing_mapping.code}), "
                                f"skipping mapping to {best_match['facility'].name} ({best_match['facility'].code})"
                            )
                        else:
                            # Update OpenNEM facility with NPI ID
                            stmt = (
                                update(Facility)
                                .where(Facility.code == best_match["facility"].code)
                                .values(npi_id=report.jurisdiction_facility_id)
                            )
                            await session.execute(stmt)
                            logger.info(f"Updated {best_match['facility'].code} with NPI ID {report.jurisdiction_facility_id}")
            else:
                best_score = best_match["score"] if best_match else 0
                report_lines.append(f"\n✗ NO MATCH (best score: {best_score:.2f})")

                # Track unmapped carbon facilities
                if any(keyword in report.facility_name.lower() for keyword in ["power", "energy", "coal", "gas", "thermal"]):
                    unmapped_carbon.append(
                        {
                            "npi_id": report.jurisdiction_facility_id,
                            "name": report.facility_name,
                            "state": report.site_address_state,
                            "business": report.registered_business_name,
                        }
                    )

            report_lines.append("=" * 80)

        if apply_mapping:
            await session.commit()
            logger.info("Mapping changes committed to database")

        # Add summary
        report_lines.append("\nSUMMARY")
        report_lines.append("=" * 80)
        report_lines.append(f"Total NPI facilities: {len(reports)}")
        report_lines.append(f"Facilities mapped: {mapped_count}")
        report_lines.append(f"Mapping rate: {mapped_count / len(reports) * 100:.1f}%")
        report_lines.append(f"\nUnmapped potential carbon facilities ({len(unmapped_carbon)}):")
        for facility in unmapped_carbon:
            report_lines.append(f"  - {facility['name']} ({facility['npi_id']}) - {facility['state']} - {facility['business']}")

        # Write report
        report_text = "\n".join(report_lines)
        if output_file:
            with open(output_file, "w") as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
        else:
            print(report_text)

        # Also generate unmapped OpenNEM facilities report
        stmt = (
            select(Facility)
            .options(selectinload(Facility.units))
            .join(Unit, Facility.id == Unit.station_id)
            .where(Unit.fueltech_id.in_(CARBON_FUELTECHS), Facility.npi_id.is_(None))
            .distinct()
        )
        result = await session.execute(stmt)
        unmapped_opennem = result.scalars().all()

        report_lines = ["\n\nUnmapped OpenNEM Carbon Facilities"]
        report_lines.append("=" * 80)
        for facility in sorted(
            unmapped_opennem,
            key=lambda f: sum(u.capacity_registered or 0 for u in f.units if u.fueltech_id in CARBON_FUELTECHS),
            reverse=True,
        )[:20]:
            fuel_types = list({u.fueltech_id for u in facility.units if u.fueltech_id in CARBON_FUELTECHS})
            capacity = sum(u.capacity_registered or 0 for u in facility.units if u.fueltech_id in CARBON_FUELTECHS)
            report_lines.append(f"{facility.name} ({facility.code}) - {facility.network_region}")
            report_lines.append(f"  Fuel: {fuel_types}, Capacity: {capacity:.1f} MW")

        if output_file:
            with open(output_file, "a") as f:
                f.write("\n".join(report_lines))
        else:
            print("\n".join(report_lines))


def main():
    parser = argparse.ArgumentParser(description="Map NPI facilities to OpenNEM facilities")
    parser.add_argument("--input", type=Path, required=True, help="Path to NPI XML file")
    parser.add_argument("--output", type=Path, help="Output file for mapping report (optional)")
    parser.add_argument("--apply", action="store_true", help="Apply mappings to database (otherwise dry run)")
    parser.add_argument(
        "--threshold", type=float, default=0.7, help="Minimum score threshold for automatic mapping (default: 0.7)"
    )

    args = parser.parse_args()

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1

    asyncio.run(map_npi_facilities(args.input, args.output, args.apply, args.threshold))

    return 0


if __name__ == "__main__":
    exit(main())
