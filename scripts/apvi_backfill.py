#!/usr/bin/env python
""" OpenNEM script to backfill historic APVI data

will run from first_seen date forward
"""
import logging

from opennem.crawlers.apvi import run_apvi_crawl
from opennem.schema.network import NetworkAPVI
from opennem.utils.dates import date_series, get_today_nem

logger = logging.getLogger("opennem.apvi_backfill")


def run_apvi_backfill(days: int | None = None) -> None:
    """For a number of days run APVI backfill"""
    if not NetworkAPVI.data_first_seen:
        raise Exception("Require a data first seen date for network to parse")

    for date_run in date_series(start=NetworkAPVI.data_first_seen, end=get_today_nem().date(), reverse=False):
        if days and days <= 0:
            break

        logger.info(f"Running APVI crawl for {date_run}")

        try:
            apvi_forecast_return = run_apvi_crawl(date_run)
            logger.info(f"APVI crawl for {date_run} inserted {apvi_forecast_return.inserted_records} records")
        except Exception as e:
            logger.error(f"Error for {date_run}: {e}")

        if days:
            days -= 1


if __name__ == "__main__":
    run_apvi_backfill()
