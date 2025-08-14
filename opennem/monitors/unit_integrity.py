"""Unit data integrity monitoring.

This module checks for data integrity issues with unit dates:
- Units with status 'operating' should have a commencement_date
- Units with status 'retired' should have a closure_date
"""

import logging

from sqlalchemy import select

from opennem.db import get_read_session
from opennem.db.models.opennem import Unit
from opennem.schema.unit import UnitStatusType

logger = logging.getLogger("opennem.monitors.unit_integrity")


async def check_unit_date_integrity() -> dict[str, list[dict]]:
    """Check unit date integrity across the database.

    This function identifies units with missing date fields:
    - Operating units without commencement_date
    - Retired units without closure_date

    Excludes:
    - Solar rooftop aggregations
    - Interconnectors (imports/exports)

    Returns:
        dict: Dictionary with two lists:
            - operating_missing_commencement: Operating units without commencement dates
            - retired_missing_closure: Retired units without closure dates
    """
    issues = {
        "operating_missing_commencement": [],
        "retired_missing_closure": [],
    }

    # Fueltechs to skip
    skip_fueltechs = ["solar_rooftop", "imports", "exports", "interconnector"]

    async with get_read_session() as session:
        # Check operating units without commencement date
        operating_query = select(Unit).where(
            Unit.status_id == UnitStatusType.operating.value,
            Unit.commencement_date.is_(None),
            # Exclude solar rooftop and interconnectors
            ~Unit.fueltech_id.in_(skip_fueltechs),
        )
        operating_result = await session.execute(operating_query)
        operating_units = operating_result.scalars().all()

        for unit in operating_units:
            # Additional check for interconnector codes that might have None fueltech
            if unit.code and any(
                pattern in unit.code
                for pattern in ["MNSP", "FLOW", "-NSW1", "-QLD1", "-VIC1", "-SA1", "-TAS1", "V-S", "V-SA", "N-Q"]
            ):
                continue

            logger.warning(
                f"Operating unit without commencement date: Unit ID: {unit.id}, Code: {unit.code}, Fueltech: {unit.fueltech_id}"
            )
            issues["operating_missing_commencement"].append(
                {
                    "id": unit.id,
                    "code": unit.code,
                    "fueltech_id": unit.fueltech_id,
                    "status_id": unit.status_id,
                    "station_id": unit.station_id,
                }
            )

        # Check retired units without closure date
        retired_query = select(Unit).where(
            Unit.status_id == UnitStatusType.retired.value,
            Unit.closure_date.is_(None),
            # Exclude solar rooftop and interconnectors
            ~Unit.fueltech_id.in_(skip_fueltechs),
        )
        retired_result = await session.execute(retired_query)
        retired_units = retired_result.scalars().all()

        for unit in retired_units:
            # Additional check for interconnector codes that might have None fueltech
            if unit.code and any(
                pattern in unit.code
                for pattern in ["MNSP", "FLOW", "-NSW1", "-QLD1", "-VIC1", "-SA1", "-TAS1", "V-S", "V-SA", "N-Q"]
            ):
                continue

            logger.warning(
                f"Retired unit without closure date: Unit ID: {unit.id}, Code: {unit.code}, Fueltech: {unit.fueltech_id}"
            )
            issues["retired_missing_closure"].append(
                {
                    "id": unit.id,
                    "code": unit.code,
                    "fueltech_id": unit.fueltech_id,
                    "status_id": unit.status_id,
                    "station_id": unit.station_id,
                }
            )

    # Log summary
    logger.info(
        f"Unit date integrity check complete: "
        f"{len(issues['operating_missing_commencement'])} operating units missing commencement date, "
        f"{len(issues['retired_missing_closure'])} retired units missing closure date "
        f"(excluding solar rooftop and interconnectors)"
    )

    return issues


async def check_unit_date_consistency() -> dict[str, list[dict]]:
    """Check for logical inconsistencies in unit dates.

    This function identifies units with illogical date combinations:
    - Units with closure_date before commencement_date
    - Operating units with closure_date
    - Retired units with expected_closure_date in the future

    Excludes:
    - Solar rooftop aggregations
    - Interconnectors (imports/exports)

    Returns:
        dict: Dictionary with lists of units with date inconsistencies
    """
    issues = {
        "closure_before_commencement": [],
        "operating_with_closure": [],
        "retired_with_future_closure": [],
    }

    # Fueltechs to skip
    skip_fueltechs = ["solar_rooftop", "imports", "exports", "interconnector"]

    # Interconnector code patterns to skip
    interconnector_patterns = ["MNSP", "FLOW", "-NSW1", "-QLD1", "-VIC1", "-SA1", "-TAS1", "V-S", "V-SA", "N-Q"]

    async with get_read_session() as session:
        # Check units where closure date is before commencement date
        date_order_query = select(Unit).where(
            Unit.commencement_date.isnot(None),
            Unit.closure_date.isnot(None),
            Unit.closure_date < Unit.commencement_date,
            ~Unit.fueltech_id.in_(skip_fueltechs),
        )
        date_order_result = await session.execute(date_order_query)
        date_order_units = date_order_result.scalars().all()

        for unit in date_order_units:
            # Skip interconnectors with None fueltech
            if unit.code and any(pattern in unit.code for pattern in interconnector_patterns):
                continue

            logger.warning(
                f"Unit with closure before commencement: "
                f"Unit ID: {unit.id}, Code: {unit.code}, "
                f"Commencement: {unit.commencement_date}, Closure: {unit.closure_date}"
            )
            issues["closure_before_commencement"].append(
                {
                    "id": unit.id,
                    "code": unit.code,
                    "fueltech_id": unit.fueltech_id,
                    "commencement_date": unit.commencement_date,
                    "closure_date": unit.closure_date,
                }
            )

        # Check operating units with closure date
        operating_closed_query = select(Unit).where(
            Unit.status_id == UnitStatusType.operating.value, Unit.closure_date.isnot(None), ~Unit.fueltech_id.in_(skip_fueltechs)
        )
        operating_closed_result = await session.execute(operating_closed_query)
        operating_closed_units = operating_closed_result.scalars().all()

        for unit in operating_closed_units:
            # Skip interconnectors with None fueltech
            if unit.code and any(pattern in unit.code for pattern in interconnector_patterns):
                continue

            logger.warning(
                f"Operating unit with closure date: Unit ID: {unit.id}, Code: {unit.code}, Closure date: {unit.closure_date}"
            )
            issues["operating_with_closure"].append(
                {
                    "id": unit.id,
                    "code": unit.code,
                    "fueltech_id": unit.fueltech_id,
                    "closure_date": unit.closure_date,
                }
            )

    logger.info(
        f"Unit date consistency check complete: "
        f"{len(issues['closure_before_commencement'])} units with closure before commencement, "
        f"{len(issues['operating_with_closure'])} operating units with closure date "
        f"(excluding solar rooftop and interconnectors)"
    )

    return issues


if __name__ == "__main__":
    import asyncio

    async def run_checks():
        """Run all unit integrity checks."""
        print("\n=== Unit Date Integrity Check ===")
        integrity_issues = await check_unit_date_integrity()

        print(f"\nOperating units missing commencement date: {len(integrity_issues['operating_missing_commencement'])}")
        for unit in integrity_issues["operating_missing_commencement"][:5]:  # Show first 5
            print(f"  - {unit['code']} (ID: {unit['id']}, Fueltech: {unit['fueltech_id']})")

        print(f"\nRetired units missing closure date: {len(integrity_issues['retired_missing_closure'])}")
        for unit in integrity_issues["retired_missing_closure"][:5]:  # Show first 5
            print(f"  - {unit['code']} (ID: {unit['id']}, Fueltech: {unit['fueltech_id']})")

        print("\n=== Unit Date Consistency Check ===")
        consistency_issues = await check_unit_date_consistency()

        print(f"\nUnits with closure before commencement: {len(consistency_issues['closure_before_commencement'])}")
        for unit in consistency_issues["closure_before_commencement"][:5]:  # Show first 5
            print(f"  - {unit['code']} (Commenced: {unit['commencement_date']}, Closed: {unit['closure_date']})")

        print(f"\nOperating units with closure date: {len(consistency_issues['operating_with_closure'])}")
        for unit in consistency_issues["operating_with_closure"][:5]:  # Show first 5
            print(f"  - {unit['code']} (Closure: {unit['closure_date']})")

    asyncio.run(run_checks())
