"""

Task scheduler for OpenNEM

This module configures and runs the task scheduler for the OpenNEM project using the arq library.
It defines the Redis settings, startup and shutdown procedures, and schedules various cron jobs
to perform periodic tasks such as crawling BOM capitals data, checking NEM intervals, and updating
market notices.

The task scheduler is an essential component of the OpenNEM system, ensuring that data is collected,
processed, and updated in a timely manner.

Functions:
    startup(ctx): Initializes the HTTP client for the task scheduler and flushes the Redis queue.
    shutdown(ctx): Closes the HTTP client for the task scheduler.

Classes:
    WorkerSettings: Configuration class for the arq worker, including queue name and cron jobs.

Running the script:
    - The script can be run directly using Python, which will start the worker.
    - python -m opennem.tasks.app
    - uv run worker
    - Alternatively, it can be run through the Docker container using the `run_worker` command.
"""

import logging
from datetime import timedelta, timezone

import logfire
from arq import cron
from arq.worker import create_worker

from opennem import settings
from opennem.api.maintenance_app import run_maintenance_app
from opennem.tasks.broker import REDIS_SETTINGS, get_redis_pool
from opennem.tasks.tasks import (
    task_apvi_crawl,
    task_bom_capitals_crawl,
    task_catchup_check,
    task_catchup_days,
    task_check_unsplit_batteries,
    task_clean_tmp_dir,
    task_export_daily_monthly,
    task_export_energy,
    task_export_facility_geojson,
    task_export_flows,
    task_facility_first_seen_check,
    task_nem_interval_check,
    task_nem_per_day_check,
    task_nem_rooftop_crawl,
    task_optimize_clickhouse_tables,
    task_refresh_from_cms,
    task_run_aggregates_demand_network_days,
    task_update_facility_first_seen,
    task_update_facility_seen_range,
    task_update_milestones,
    task_wem_day_crawl,
)
from opennem.utils.host import get_hostname
from opennem.utils.version import get_version

logger = logging.getLogger("openenm.tasks.app")


async def startup(ctx: dict) -> None:
    """Initialize the worker and flush the Redis queue on startup.

    This function is called when the worker starts up. It flushes the Redis queue
    to ensure we start with a clean slate and no stale tasks.

    Args:
        ctx (dict): The worker context
    """
    logfire.info(f"OpenNEM worker starting up on {settings.env}: v{get_version()} on host {get_hostname()}", service="worker")

    redis = await get_redis_pool()
    await redis.flushdb()
    logger.info("Redis queue flushed on startup")


class WorkerSettings:
    # queue_name = "opennem"
    on_startup = startup
    cron_jobs = [
        # NEM Interval Check
        cron(
            task_nem_interval_check,
            minute=set(range(0, 60, 5)),
            second=50,
            timeout=None,
            unique=True,
        ),
        # Milestone Updates
        cron(
            task_update_milestones,
            minute={5},  # Run at 5 minutes past every hour
            hour=set(range(0, 24, 6)),  # run every 6 hours
            second=0,
            timeout=None,
            unique=True,
        ),
        # Optimize unit_intervals table daily
        cron(
            task_optimize_clickhouse_tables,
            hour={0, 6, 12, 18},
            minute=15,
            second=0,
            timeout=None,
            unique=True,
        ),
        # NEM Rooftop
        cron(
            task_nem_rooftop_crawl,
            minute=set(range(0, 60, 5)),
            second=50,
            timeout=None,
            unique=True,
        ),
        # WEM Interval Check
        cron(
            task_wem_day_crawl,
            minute={30},
            second=58,
            timeout=None,
            unique=True,
        ),
        # APVI Rooftop
        cron(
            task_apvi_crawl,
            minute=set(range(0, 60, 15)),
            second=58,
            timeout=None,
            unique=True,
        ),
        # NEM Next Day Dispatch
        cron(
            task_nem_per_day_check,
            hour={5},
            minute=25,
            second=0,
            timeout=None,
            unique=True,
        ),
        # energy latest export
        cron(
            task_export_energy,
            # hour={0, 7, 11},
            minute=17,
            second=0,
            timeout=None,
            unique=True,
        ),
        # export daily and monthly
        cron(
            task_export_daily_monthly,
            hour=4,
            minute=17,
            second=0,
            timeout=None,
            unique=True,
        ),
        # archive exports daily
        # cron(
        #     task_sync_archive_exports,
        #     hour=7,
        #     minute=0,
        #     timeout=None,
        #     unique=True,
        # ),
        # demand aggregates
        cron(
            task_run_aggregates_demand_network_days,
            minute=27,
            second=0,
            timeout=None,
            unique=True,
        ),
        # export flows and electricitymap
        cron(
            task_export_flows,
            minute=set(range(0, 60, 15)),
            second=0,
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
            minute=set(range(1, 60, 5)),
            second=59,
            timeout=None,
            unique=True,
        ),
        cron(
            task_update_facility_first_seen,
            hour=1,
            minute=32,
            second=59,
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
        # Monitor catchup
        cron(
            task_catchup_check,
            minute=set(range(1, 60, 5)),
            second=30,
            timeout=None,
            unique=True,
        ),
        # clean tmp dir
        cron(
            task_clean_tmp_dir,
            hour=1,
            minute=0,
            timeout=None,
            unique=True,
        ),
        # catchup
        cron(
            task_catchup_days,
            minute=15,
            second=0,
            hour=0,
            timeout=None,
            unique=True,
        ),
        # Check for unsplit batteries
        cron(
            task_check_unsplit_batteries,
            hour=10,
            minute=0,
            second=0,
            timeout=None,
            unique=True,
        ),
    ]
    redis_settings = REDIS_SETTINGS
    retry_jobs = True
    max_retries = 5
    job_timeout = 60 * 60 * 12  # 12 hours max task time
    timezone = timezone(timedelta(hours=10))


def main() -> None:
    """Run the main worker"""
    from opennem import settings

    if settings.run_worker:
        worker = create_worker(settings_cls=WorkerSettings)  # type: ignore
        worker.run()
    else:
        print(" * Worker not enabled - waiting for worker to restart")
        run_maintenance_app()


if __name__ == "__main__":
    main()
