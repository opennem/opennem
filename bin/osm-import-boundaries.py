#!/usr/bin/env python
"""
Fetch OSM boundary polygons for facilities and store in the database.

Reads osm_way_id from each facility, fetches the polygon/multipolygon
from the OSM API, and stores it in the boundary column.

Handles both ways (positive IDs) and relations (negative IDs).
"""

import asyncio
import time

from sqlalchemy import select, update

from opennem.core.parsers.osm import get_osm_geom
from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import Facility


async def import_osm_boundaries(dry_run: bool = True, facility_code: str | None = None):
    """Fetch OSM boundaries and store in DB"""

    async with get_read_session() as session:
        stmt = select(Facility.code, Facility.name, Facility.osm_way_id, Facility.boundary).where(Facility.osm_way_id.isnot(None))

        if facility_code:
            stmt = stmt.where(Facility.code == facility_code)

        stmt = stmt.order_by(Facility.code)
        result = await session.execute(stmt)
        facilities = result.all()

    print(f"Found {len(facilities)} facilities with osm_way_id")

    already_have = sum(1 for f in facilities if f.boundary is not None)
    need_fetch = [f for f in facilities if f.boundary is None]

    print(f"Already have boundary: {already_have}")
    print(f"Need to fetch: {len(need_fetch)}")

    if not need_fetch:
        print("Nothing to do")
        return

    if dry_run:
        print("\n*** DRY RUN — would fetch boundaries for: ***")
        for f in need_fetch[:20]:
            osm_type = "relation" if int(f.osm_way_id) < 0 else "way"
            print(f"  {f.code:<20} {f.osm_way_id:<16} ({osm_type}) {f.name}")
        if len(need_fetch) > 20:
            print(f"  ... and {len(need_fetch) - 20} more")
        print("\nRun with --no-dry-run to apply")
        return

    print(f"\n*** Fetching {len(need_fetch)} boundaries from OSM API ***")

    success_count = 0
    error_count = 0
    errors: list[tuple[str, str]] = []

    for i, f in enumerate(need_fetch, 1):
        osm_type = "relation" if int(f.osm_way_id) < 0 else "way"
        try:
            geom = await get_osm_geom(f.osm_way_id)

            async with get_write_session() as session:
                await session.execute(update(Facility).where(Facility.code == f.code).values(boundary=geom))
                await session.commit()

            success_count += 1
            print(f"  [{i}/{len(need_fetch)}] {f.code} ({osm_type}) OK")

        except Exception as e:
            error_count += 1
            error_msg = str(e)[:80]
            errors.append((f.code, error_msg))
            print(f"  [{i}/{len(need_fetch)}] {f.code} ({osm_type}) ERROR: {error_msg}")

        # Rate limit: ~1 req/sec to be polite to OSM API
        time.sleep(1.0)

    print(f"\n*** Done: {success_count} succeeded, {error_count} failed ***")

    if errors:
        print("\nFailed facilities:")
        for code, msg in errors:
            print(f"  {code}: {msg}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import OSM boundary polygons for facilities")
    parser.add_argument("--no-dry-run", action="store_true", help="Actually fetch and store (default is dry run)")
    parser.add_argument("--facility-code", type=str, help="Only process a single facility")

    args = parser.parse_args()

    asyncio.run(import_osm_boundaries(dry_run=not args.no_dry_run, facility_code=args.facility_code))
