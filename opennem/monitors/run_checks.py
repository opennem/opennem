#!/usr/bin/env python3
"""Run unit data integrity checks.

This script runs all unit data integrity checks and can be scheduled
to run regularly to monitor data quality.
"""

import asyncio
import logging
from datetime import datetime

from opennem.monitors.unit_integrity import check_unit_date_consistency, check_unit_date_integrity

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def run_all_checks():
    """Run all unit integrity checks and log results."""
    start_time = datetime.now()
    logger.info("Starting unit data integrity checks")

    # Run integrity checks
    integrity_issues = await check_unit_date_integrity()
    consistency_issues = await check_unit_date_consistency()

    # Summary report
    total_issues = (
        len(integrity_issues["operating_missing_commencement"])
        + len(integrity_issues["retired_missing_closure"])
        + len(consistency_issues["closure_before_commencement"])
        + len(consistency_issues["operating_with_closure"])
    )

    logger.info(f"Data integrity check completed in {(datetime.now() - start_time).total_seconds():.2f} seconds")
    logger.info(f"Total issues found: {total_issues}")

    # Log critical issues
    if integrity_issues["operating_missing_commencement"]:
        logger.warning(
            f"CRITICAL: {len(integrity_issues['operating_missing_commencement'])} operating units "
            f"without commencement date - these units may not appear in historical data correctly"
        )

    if integrity_issues["retired_missing_closure"]:
        logger.warning(
            f"CRITICAL: {len(integrity_issues['retired_missing_closure'])} retired units "
            f"without closure date - these units may incorrectly appear as still operating"
        )

    if consistency_issues["operating_with_closure"]:
        logger.warning(
            f"CRITICAL: {len(consistency_issues['operating_with_closure'])} operating units "
            f"with closure date - these units may be incorrectly marked as operating"
        )

    return {"integrity": integrity_issues, "consistency": consistency_issues, "total_issues": total_issues}


if __name__ == "__main__":
    asyncio.run(run_all_checks())
