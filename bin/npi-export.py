#!/usr/bin/env python
"""
Export facility code to NPI ID mappings from the database
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from opennem.db import get_read_session
from opennem.db.models.opennem import Facility


async def export_npi_mappings():
    """Export all facility code -> NPI ID mappings from the database"""

    async with get_read_session() as session:
        # Query all facilities with NPI IDs
        stmt = select(Facility.code, Facility.npi_id).where(Facility.npi_id.isnot(None)).order_by(Facility.code)

        result = await session.execute(stmt)
        mappings = result.all()

    # Convert to dictionary
    npi_mappings = {code: npi_id for code, npi_id in mappings}  # noqa: C416

    # Statistics
    print(f"Found {len(npi_mappings)} facilities with NPI IDs")

    # Save to JSON file
    output_file = Path("npi_mappings.json")
    with open(output_file, "w") as f:
        json.dump(npi_mappings, f, indent=2, sort_keys=True)

    print(f"Exported NPI mappings to {output_file}")

    # Also create a more detailed export with facility names for review
    async with get_read_session() as session:
        stmt = select(Facility.code, Facility.name, Facility.npi_id).where(Facility.npi_id.isnot(None)).order_by(Facility.code)

        result = await session.execute(stmt)
        detailed_mappings = result.all()

    detailed_data = [{"facility_code": code, "facility_name": name, "npi_id": npi_id} for code, name, npi_id in detailed_mappings]

    detailed_output_file = Path("npi_mappings_detailed.json")
    with open(detailed_output_file, "w") as f:
        json.dump(detailed_data, f, indent=2)

    print(f"Exported detailed NPI mappings to {detailed_output_file}")


if __name__ == "__main__":
    asyncio.run(export_npi_mappings())
