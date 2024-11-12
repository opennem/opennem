"""

Task scheduler for OpenNEM

This module configures and runs the task scheduler for the OpenNEM project using the arq library.
It defines the Redis settings, startup and shutdown procedures, and schedules various cron jobs
to perform periodic tasks such as crawling BOM capitals data, checking NEM intervals, and updating
market notices.

The task scheduler is an essential component of the OpenNEM system, ensuring that data is collected,
processed, and updated in a timely manner.

Functions:
    startup(ctx): Initializes the HTTP client for the task scheduler.
    shutdown(ctx): Closes the HTTP client for the task scheduler.

Classes:
    WorkerSettings: Configuration class for the arq worker, including queue name and cron jobs.

Cron Jobs:
    - task_nem_interval_check: Runs every 5 minutes to check NEM intervals.
    - task_bom_capitals_crawl: (Not shown in the snippet) Crawls BOM capitals data.
    - task_run_market_notice_update: (Not shown in the snippet) Updates market notices.

Running the script:
    - The script can be run directly using Python, which will start the worker.
    - python -m opennem.tasks.app
    - Alternatively, it can be run through the Docker container using the `run_worker` command.
"""

import logging
from datetime import timedelta, timezone

from arq import cron
from arq.worker import create_worker

from opennem.tasks.broker import REDIS_SETTINGS
from opennem.tasks.tasks import (
    task_bom_capitals_crawl,
    task_clean_tmp_dir,
    task_export_facility_geojson,
    task_facility_first_seen_check,
    task_nem_exports,
    task_nem_interval_check,
    task_nem_rooftop_crawl,
    task_refresh_from_cms,
    task_run_energy_calculation,
    task_update_facility_seen_range,
)

logger = logging.getLogger("openenm.tasks.app")


class WorkerSettings:
    # queue_name = "opennem"
    cron_jobs = [
        # NEM Interval Check
        cron(
            task_nem_interval_check,
            minute=set(range(0, 60, 5)),
            second=30,
            timeout=None,
            unique=True,
        ),
        # NEM Rooftop
        cron(
            task_nem_rooftop_crawl,
            minute=set(range(0, 60, 30)),
            second=50,
            timeout=None,
            unique=True,
        ),
        #
        # Energy Calculation
        cron(
            task_run_energy_calculation,
            minute={2, 32},
            second=55,
            timeout=None,
            unique=True,
        ),
        # NEM exports
        cron(
            task_nem_exports,
            minute=set(range(0, 60, 5)),
            second=58,
            timeout=None,
            unique=True,
        ),
        # Facility geojson
        cron(
            task_export_facility_geojson,
            minute=3,
            second=0,
            timeout=None,
            unique=True,
        ),
        # Facility first seen
        cron(
            task_facility_first_seen_check,
            hour=9,
            minute=1,
            second=59,
            timeout=None,
            unique=True,
        ),
        # Facility seen range
        cron(
            task_update_facility_seen_range,
            minute={1, 16, 31, 46},
            second=30,
            timeout=None,
            unique=True,
        ),
        # AEMO Market notices
        # cron(
        #     task_run_market_notice_update,
        #     minute=30,
        #     second=30,
        #     timeout=None,
        #     unique=True,
        # ),
        # BoM weather data
        cron(
            task_bom_capitals_crawl,
            minute={10, 40},
            second=0,
            timeout=None,
            unique=True,
        ),
        # CMS Update
        cron(
            task_refresh_from_cms,
            minute=1,
            second=0,
            timeout=None,
            unique=True,
        ),
        # cron(
        #     crawler_run_nem_dispatch_is_crawl,
        #     minute=set(range(0, 60, 5)),
        #     second=30,
        #     timeout=None,
        #     unique=True,
        # ),
        # cron(
        #     crawler_run_nem_trading_is_crawl,
        #     minute=set(range(0, 60, 5)),
        #     second=30,
        #     timeout=None,
        #     unique=True,
        # ),
        # clean tmp dir
        cron(
            task_clean_tmp_dir,
            hour=1,
            minute=0,
            timeout=None,
            unique=True,
        ),
    ]
    redis_settings = REDIS_SETTINGS
    retry_jobs = True
    max_tries = 5
    job_timeout = 60 * 60 * 12  # 12 hours max task time
    timezone = timezone(timedelta(hours=10))


def main() -> None:
    """Run the main worker"""
    worker = create_worker(settings_cls=WorkerSettings)  # type: ignore
    worker.run()


if __name__ == "__main__":
    main()
