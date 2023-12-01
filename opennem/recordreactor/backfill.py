"""
OpenNEM API Reactor Backfill Records

Generates records for the OpenNEM API Reactor Backfill project and will
run queries for all records back to a date defined as a parameter.

For testing on dev we run back ~6 months.
"""

import logging

logger = logging.getLogger("opennem.recordreactor.backfill")


if __name__ == "__main__":
    logger.info("OpenNEM API Reactor Backfill")
    logger.info("Generating records for all facilities")
