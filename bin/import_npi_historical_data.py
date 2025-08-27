#!/usr/bin/env python
"""
Import all historical NPI pollution data from XML files
"""

import asyncio
import logging
from pathlib import Path

from opennem.controllers.npi import import_all_npi_historical_data

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Import all historical NPI data"""
    data_dir = Path("data/npi")

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    logger.info(f"Starting import of historical NPI data from {data_dir}")

    try:
        result = await import_all_npi_historical_data(data_dir=str(data_dir), dry_run=False)
        logger.info(f"Import completed: {result}")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
