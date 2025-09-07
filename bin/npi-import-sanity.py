#!/usr/bin/env python
"""
Import facility code to NPI ID mappings to Sanity CMS
"""

import json
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from opennem import settings

load_dotenv()


class SanityClient:
    """Client for interacting with Sanity CMS API"""

    def __init__(self, project_id: str, dataset: str, token: str, api_version: str = "2024-01-01"):
        self.project_id = project_id
        self.dataset = dataset
        self.token = token
        self.api_version = api_version
        self.base_url = f"https://{project_id}.api.sanity.io/v{api_version}"

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def query(self, groq_query: str) -> dict:
        """Execute a GROQ query against Sanity"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/data/query/{self.dataset}",
                params={"query": groq_query},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def patch_document(self, document_id: str, patches: list) -> dict:
        """Patch a Sanity document"""
        mutations = [{"patch": {"id": document_id, "set": patches[0]["set"] if patches and "set" in patches[0] else {}}}]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/data/mutate/{self.dataset}",
                json={"mutations": mutations},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()


async def import_npi_to_sanity(mappings_file: Path = Path("npi_mappings.json"), dry_run: bool = True):
    """Import NPI ID mappings to Sanity CMS

    Args:
        mappings_file: Path to the JSON file with mappings
        dry_run: If True, only show what would be updated without making changes
    """

    # Load environment variables for Sanity
    project_id = settings.sanity_project_id
    dataset = settings.sanity_dataset_id
    token = settings.sanity_api_key

    if not all([project_id, token]):
        print("Error: Missing Sanity configuration")
        print("Please set the following environment variables:")
        print("  SANITY_PROJECT_ID")
        print("  SANITY_TOKEN")
        print("  SANITY_DATASET (optional, defaults to 'production')")
        return

    # Load mappings
    if not mappings_file.exists():
        print(f"Error: Mappings file {mappings_file} not found")
        return

    with open(mappings_file) as f:
        npi_mappings: dict[str, str] = json.load(f)

    print(f"Loaded {len(npi_mappings)} NPI mappings from {mappings_file}")
    print(f"Connecting to Sanity project: {project_id} (dataset: {dataset})")

    client = SanityClient(project_id, dataset, token)

    # Query all facilities from Sanity
    groq_query = '*[_type == "facility"]{_id, code, name, npiId}'

    try:
        result = await client.query(groq_query)
        sanity_facilities = result.get("result", [])
    except Exception as e:
        print(f"Error querying Sanity: {e}")
        return

    print(f"Found {len(sanity_facilities)} facilities in Sanity")

    # Build lookup by facility code
    sanity_by_code = {f["code"]: f for f in sanity_facilities if f.get("code")}

    # Process updates
    updates_needed = []
    new_assignments = 0
    already_correct = 0
    facilities_not_found = []
    conflicts = []

    for facility_code, npi_id in npi_mappings.items():
        sanity_facility = sanity_by_code.get(facility_code)

        if not sanity_facility:
            facilities_not_found.append(facility_code)
            continue

        current_npi_id = sanity_facility.get("npiId")

        if current_npi_id == npi_id:
            already_correct += 1
            continue

        if current_npi_id and current_npi_id != npi_id:
            conflicts.append(
                {
                    "facility_code": facility_code,
                    "facility_name": sanity_facility.get("name", "Unknown"),
                    "sanity_id": sanity_facility["_id"],
                    "current_npi_id": current_npi_id,
                    "new_npi_id": npi_id,
                }
            )
            continue

        # New assignment needed
        if not current_npi_id:
            new_assignments += 1
            updates_needed.append(
                {
                    "facility_code": facility_code,
                    "facility_name": sanity_facility.get("name", "Unknown"),
                    "sanity_id": sanity_facility["_id"],
                    "npi_id": npi_id,
                }
            )

    # Report findings
    print("\n=== Import Summary ===")
    print(f"Total mappings to import: {len(npi_mappings)}")
    print(f"Already correct: {already_correct}")
    print(f"New assignments needed: {new_assignments}")
    print(f"Facilities not found in Sanity: {len(facilities_not_found)}")
    print(f"Conflicts detected: {len(conflicts)}")

    if facilities_not_found:
        print(f"\nFacilities not found in Sanity (first 10): {facilities_not_found[:10]}")
        if len(facilities_not_found) > 10:
            print(f"  ... and {len(facilities_not_found) - 10} more")

    if conflicts:
        print("\n=== Conflicts (existing NPI ID differs) ===")
        for conflict in conflicts[:10]:
            print(f"  {conflict['facility_code']} ({conflict['facility_name']})")
            print(f"    Sanity ID: {conflict['sanity_id']}")
            print(f"    Current: {conflict['current_npi_id']}")
            print(f"    New:     {conflict['new_npi_id']}")
        if len(conflicts) > 10:
            print(f"  ... and {len(conflicts) - 10} more conflicts")

        # Save conflicts to file for review
        conflicts_file = Path("npi_sanity_conflicts.json")
        with open(conflicts_file, "w") as f:
            json.dump(conflicts, f, indent=2)
        print(f"\nConflicts saved to {conflicts_file} for review")

    if updates_needed:
        print(f"\n=== Updates to Apply ({len(updates_needed)} facilities) ===")
        for update in updates_needed[:5]:
            print(f"  {update['facility_code']} ({update['facility_name']})")
            print(f"    Sanity ID: {update['sanity_id']}")
            print(f"    NPI ID: {update['npi_id']}")
        if len(updates_needed) > 5:
            print(f"  ... and {len(updates_needed) - 5} more")

    if dry_run:
        print("\n*** DRY RUN - No changes made ***")
        print("Run with --no-dry-run to apply changes")
    else:
        print(f"\n*** Applying updates to {len(updates_needed)} facilities in Sanity ***")

        success_count = 0
        error_count = 0

        for i, update in enumerate(updates_needed, 1):
            try:
                await client.patch_document(update["sanity_id"], [{"set": {"npiId": update["npi_id"]}}])
                success_count += 1
                print(f"  [{i}/{len(updates_needed)}] Updated {update['facility_code']}")

                # Rate limit to avoid overwhelming the API
                if i % 10 == 0:
                    time.sleep(0.5)

            except Exception as e:
                error_count += 1
                print(f"  [{i}/{len(updates_needed)}] ERROR updating {update['facility_code']}: {e}")

        print(f"\n*** Update complete: {success_count} succeeded, {error_count} failed ***")


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Import NPI ID mappings to Sanity CMS")
    parser.add_argument("--file", type=Path, default=Path("npi_mappings.json"), help="Path to the NPI mappings JSON file")
    parser.add_argument("--no-dry-run", action="store_true", help="Actually perform the import (default is dry run)")

    args = parser.parse_args()

    asyncio.run(import_npi_to_sanity(mappings_file=args.file, dry_run=not args.no_dry_run))
