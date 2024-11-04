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

from arq import cron, run_worker
from arq.connections import RedisSettings

from opennem import settings
from opennem.tasks.tasks import (
    task_bom_capitals_crawl,
    task_nem_interval_check,
    task_run_market_notice_update,
)
from opennem.utils.httpx import httpx_factory

REDIS_SETTINGS = RedisSettings(
    host=settings.redis_url.host,  # type: ignore
    port=settings.redis_url.port,  # type: ignore
    username=settings.redis_url.username,  # type: ignore
    password=settings.redis_url.password,  # type: ignore
    ssl=settings.redis_url.scheme == "rediss",
    conn_timeout=300,
)

logger = logging.getLogger("openenm.scheduler")


async def startup(ctx):
    ctx["http"] = httpx_factory()


async def shutdown(ctx):
    await ctx["http"].aclose()


class WorkerSettings:
    queue_name = "opennem"
    cron_jobs = [
        cron(
            task_nem_interval_check,
            minute=set(range(0, 60, 5)),
            second=30,
            timeout=None,
            unique=True,
        ),
        # AEMO Market notices
        cron(
            task_run_market_notice_update,
            minute=30,
            second=30,
            timeout=None,
            unique=True,
        ),
        # BoM weather data
        cron(
            task_bom_capitals_crawl,
            minute={10, 40},
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
    ]
    # functions = (
    #     [
    #         task_nem_dispatch_scada_crawl,
    #     ],
    # )

    retry_jobs = True
    max_tries = 5
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 60 * 60 * 12  # 12 hours max task time
    redis_settings = REDIS_SETTINGS
    timezone = timezone(timedelta(hours=10))


def main() -> None:
    """Run the main worker"""
    run_worker(settings_cls=WorkerSettings)


if __name__ == "__main__":
    main()
