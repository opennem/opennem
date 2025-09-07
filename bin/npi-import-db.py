#!/usr/bin/env python
"""
Import facility code to NPI ID mappings to the production database
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from opennem.db import get_write_session
from opennem.db.models.opennem import Facility


async def import_npi_mappings(mappings_file: Path = Path("npi_mappings.json"), dry_run: bool = True):
    """Import NPI ID mappings to the database

    Args:
        mappings_file: Path to the JSON file with mappings
        dry_run: If True, only show what would be updated without making changes
    """

    # Load mappings
    if not mappings_file.exists():
        print(f"Error: Mappings file {mappings_file} not found")
        return

    with open(mappings_file) as f:
        npi_mappings: dict[str, str] = json.load(f)

    print(f"Loaded {len(npi_mappings)} NPI mappings from {mappings_file}")

    updates_made = 0
    new_assignments = 0
    already_correct = 0
    facilities_not_found = []
    conflicts = []

    async with get_write_session() as session:
        for facility_code, npi_id in npi_mappings.items():
            # Check if facility exists
            stmt = select(Facility).where(Facility.code == facility_code)
            result = await session.execute(stmt)
            facility = result.scalar_one_or_none()

            if not facility:
                facilities_not_found.append(facility_code)
                continue

            # Check current NPI ID
            if facility.npi_id == npi_id:
                already_correct += 1
                continue

            if facility.npi_id and facility.npi_id != npi_id:
                conflicts.append(
                    {
                        "facility_code": facility_code,
                        "facility_name": facility.name,
                        "current_npi_id": facility.npi_id,
                        "new_npi_id": npi_id,
                    }
                )
                continue

            # New assignment
            if not facility.npi_id:
                new_assignments += 1
                if not dry_run:
                    facility.npi_id = npi_id
                    updates_made += 1
                else:
                    print(f"Would assign NPI ID {npi_id} to {facility_code} ({facility.name})")

        if not dry_run and updates_made > 0:
            await session.commit()
            print(f"Successfully updated {updates_made} facilities")

    # Report results
    print("\n=== Import Summary ===")
    print(f"Total mappings to import: {len(npi_mappings)}")
    print(f"Already correct: {already_correct}")
    print(f"New assignments: {new_assignments}")
    print(f"Facilities not found: {len(facilities_not_found)}")
    print(f"Conflicts detected: {len(conflicts)}")

    if facilities_not_found:
        print(f"\nFacilities not found in database: {facilities_not_found[:10]}")
        if len(facilities_not_found) > 10:
            print(f"  ... and {len(facilities_not_found) - 10} more")

    if conflicts:
        print("\n=== Conflicts (existing NPI ID differs) ===")
        for conflict in conflicts[:10]:
            print(f"  {conflict['facility_code']} ({conflict['facility_name']})")
            print(f"    Current: {conflict['current_npi_id']}")
            print(f"    New:     {conflict['new_npi_id']}")
        if len(conflicts) > 10:
            print(f"  ... and {len(conflicts) - 10} more conflicts")

        # Save conflicts to file for review
        conflicts_file = Path("npi_conflicts.json")
        with open(conflicts_file, "w") as f:
            json.dump(conflicts, f, indent=2)
        print(f"\nConflicts saved to {conflicts_file} for review")

    if dry_run:
        print("\n*** DRY RUN - No changes made ***")
        print("Run with --no-dry-run to apply changes")
    else:
        print(f"\n*** Updated {updates_made} facilities in the database ***")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import NPI ID mappings to database")
    parser.add_argument("--file", type=Path, default=Path("npi_mappings.json"), help="Path to the NPI mappings JSON file")
    parser.add_argument("--no-dry-run", action="store_true", help="Actually perform the import (default is dry run)")

    args = parser.parse_args()

    asyncio.run(import_npi_mappings(mappings_file=args.file, dry_run=not args.no_dry_run))
