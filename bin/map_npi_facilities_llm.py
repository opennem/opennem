#!/usr/bin/env python
"""
Map remaining unmapped NPI facilities to OpenNEM facilities using LLM assistance

This script uses OpenAI's GPT-4o-mini to help match facilities that fuzzy string matching missed,
particularly those with company names embedded or other naming variations.

Usage:
    python bin/map_npi_facilities_llm.py [--apply] [--output report.txt]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from openai import OpenAI
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

sys.path.insert(0, str(Path(__file__).parent.parent))

from opennem.db import get_write_session
from opennem.db.models.npi import NPIFacility
from opennem.db.models.opennem import Facility, Unit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# State mapping from network regions
REGION_TO_STATE = {
    "NSW1": "NSW",
    "QLD1": "QLD",
    "VIC1": "VIC",
    "SA1": "SA",
    "TAS1": "TAS",
    "WEM": "WA",
    "WA1": "WA",
}


def create_llm_prompt(opennem_facility, npi_facilities_in_state):
    """Create a prompt for the LLM to match facilities"""

    # Get facility details
    fuel_types = list({u.fueltech_id for u in opennem_facility.units if u.fueltech_id in CARBON_FUELTECHS})
    capacity = sum(u.capacity_registered or 0 for u in opennem_facility.units if u.fueltech_id in CARBON_FUELTECHS)

    prompt = f"""You are helping match electricity generation facilities between two databases.

OpenNEM Facility to Match:
- Name: {opennem_facility.name}
- Code: {opennem_facility.code}
- State: {REGION_TO_STATE.get(opennem_facility.network_region, "Unknown")}
- Fuel Types: {", ".join(fuel_types)}
- Capacity: {capacity:.1f} MW

NPI Facilities in Same State (ID | Name | Business | Location):
"""

    for npi in npi_facilities_in_state:
        business = npi.registered_business_name or "N/A"
        suburb = npi.site_address_suburb or "Unknown"
        prompt += f"- {npi.npi_id} | {npi.npi_name} | {business} | {suburb}\n"

    prompt += """
Task: Identify which NPI facility (if any) corresponds to the OpenNEM facility above.

Consider:
1. The facility names may differ due to company prefixes (e.g., "AGL Torrens" vs "Torrens Island Power Station")
2. Some facilities have numbered units (e.g., "Braemar" vs "Braemar 2")
3. The NPI name might include the parent company name
4. Location/suburb can help confirm matches
5. Some OpenNEM facilities may genuinely have no NPI match (e.g., very small, closed before 1998, or non-reporting)

Response format (JSON only, no other text):
{
  "matched": true/false,
  "npi_id": "NPI_ID or null",
  "confidence": "high/medium/low",
  "reasoning": "Brief explanation"
}
"""

    return prompt


async def map_with_llm(opennem_facility, npi_facilities_in_state):
    """Use OpenAI GPT-4o-mini to match a facility"""

    prompt = create_llm_prompt(opennem_facility, npi_facilities_in_state)

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at matching electricity generation facilities. " "Always respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            # temperature=0.1,  # Low temperature for consistency
        )

        # Parse the response
        response_text = response.choices[0].message.content.strip()

        # Try to extract JSON from the response
        try:
            # Handle case where LLM wraps JSON in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)

            # Validate expected fields
            if not all(key in result for key in ["matched", "npi_id", "confidence", "reasoning"]):
                logger.warning(f"Incomplete response for {opennem_facility.name}: {result}")
                return {"matched": False, "npi_id": None, "confidence": "low", "reasoning": "Invalid LLM response format"}

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {opennem_facility.name}: {e}")
            logger.debug(f"Response was: {response_text}")
            return {"matched": False, "npi_id": None, "confidence": "low", "reasoning": f"JSON parse error: {str(e)}"}

    except Exception as e:
        logger.error(f"OpenAI API error for {opennem_facility.name}: {e}")
        return {"matched": False, "npi_id": None, "confidence": "low", "reasoning": f"API error: {str(e)}"}


async def main(apply_mapping=False, output_file=None, limit=None):
    """Main function to run LLM-assisted mapping"""

    report_lines = []
    report_lines.append("LLM-Assisted NPI Facility Mapping Report")
    report_lines.append("=" * 80)

    async with get_write_session() as session:
        # Get all unmapped carbon fuel facilities
        stmt = (
            select(Facility)
            .options(selectinload(Facility.units))
            .join(Unit, Facility.id == Unit.station_id)
            .where(Unit.fueltech_id.in_(CARBON_FUELTECHS), Facility.npi_id.is_(None))
            .distinct()
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        unmapped_facilities = result.scalars().all()

        # Sort by capacity (largest first)
        unmapped_facilities = sorted(
            unmapped_facilities,
            key=lambda f: sum(u.capacity_registered or 0 for u in f.units if u.fueltech_id in CARBON_FUELTECHS),
            reverse=True,
        )

        # Apply limit if specified
        if limit:
            unmapped_facilities = unmapped_facilities[:limit]

        report_lines.append(f"Found {len(unmapped_facilities)} unmapped carbon fuel facilities")
        if limit:
            report_lines.append(f"Processing first {limit} facilities")

        # Get all NPI facilities
        stmt = select(NPIFacility)
        result = await session.execute(stmt)
        all_npi_facilities = result.scalars().all()

        # Group NPI facilities by state
        npi_by_state = {}
        for npi in all_npi_facilities:
            state = npi.location_state
            if state not in npi_by_state:
                npi_by_state[state] = []
            npi_by_state[state].append(npi)

        mapped_count = 0
        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0
        no_match_count = 0

        # Process each unmapped facility
        for i, facility in enumerate(unmapped_facilities, 1):
            # Get the state
            state = REGION_TO_STATE.get(facility.network_region)
            if not state:
                report_lines.append(f"\n[{i}] Skipping {facility.name} - unknown state for region {facility.network_region}")
                continue

            # Get NPI facilities in the same state
            npi_in_state = npi_by_state.get(state, [])
            if not npi_in_state:
                report_lines.append(f"\n[{i}] No NPI facilities found in {state} for {facility.name}")
                no_match_count += 1
                continue

            # Get facility info
            fuel_types = list({u.fueltech_id for u in facility.units if u.fueltech_id in CARBON_FUELTECHS})
            capacity = sum(u.capacity_registered or 0 for u in facility.units if u.fueltech_id in CARBON_FUELTECHS)

            report_lines.append(f"\n[{i}] {facility.name} ({facility.code})")
            report_lines.append(f"  State: {state}, Fuel: {fuel_types}, Capacity: {capacity:.1f} MW")

            logger.info(f"Processing {i}/{len(unmapped_facilities)}: {facility.name}")

            # Use LLM to find match
            result = await map_with_llm(facility, npi_in_state)

            if result["matched"]:
                mapped_count += 1
                if result["confidence"] == "high":
                    high_confidence += 1
                elif result["confidence"] == "medium":
                    medium_confidence += 1
                else:
                    low_confidence += 1

                # Get the matched NPI facility name
                matched_npi = next((npi for npi in npi_in_state if npi.npi_id == result["npi_id"]), None)
                npi_name = matched_npi.npi_name if matched_npi else "Unknown"

                report_lines.append(f"  ✓ Matched to {npi_name} ({result['npi_id']}) - {result['confidence']} confidence")
                report_lines.append(f"    Reasoning: {result['reasoning']}")

                if apply_mapping and result["confidence"] in ["high", "medium"]:
                    # Check if NPI ID already mapped
                    stmt = select(Facility).where(Facility.npi_id == result["npi_id"])
                    existing = await session.execute(stmt)
                    if not existing.scalar_one_or_none():
                        # Apply the mapping
                        stmt = update(Facility).where(Facility.code == facility.code).values(npi_id=result["npi_id"])
                        await session.execute(stmt)
                        report_lines.append("    → Applied mapping to database")
                    else:
                        report_lines.append("    → NPI ID already mapped to another facility")
            else:
                no_match_count += 1
                report_lines.append("  ✗ No match found")
                report_lines.append(f"    Reasoning: {result['reasoning']}")

        if apply_mapping:
            await session.commit()
            report_lines.append("\nMappings committed to database")

        # Summary
        report_lines.append("\n" + "=" * 80)
        report_lines.append("SUMMARY")
        report_lines.append(f"Total unmapped facilities processed: {len(unmapped_facilities)}")
        report_lines.append(f"Facilities matched: {mapped_count}")
        report_lines.append(f"  High confidence: {high_confidence}")
        report_lines.append(f"  Medium confidence: {medium_confidence}")
        report_lines.append(f"  Low confidence: {low_confidence}")
        report_lines.append(f"No matches found: {no_match_count}")

        if mapped_count > 0:
            report_lines.append(f"\nMatch rate: {mapped_count / len(unmapped_facilities) * 100:.1f}%")

    # Output report
    report_text = "\n".join(report_lines)
    if output_file:
        with open(output_file, "w") as f:
            f.write(report_text)
        logger.info(f"Report saved to {output_file}")
    else:
        print(report_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map NPI facilities using LLM assistance")
    parser.add_argument("--apply", action="store_true", help="Apply mappings to database")
    parser.add_argument("--output", type=Path, help="Output file for report")
    parser.add_argument("--limit", type=int, help="Limit number of facilities to process (for testing)")

    args = parser.parse_args()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    asyncio.run(main(apply_mapping=args.apply, output_file=args.output, limit=args.limit))
