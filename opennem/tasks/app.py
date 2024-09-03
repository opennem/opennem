"""Task scheduler"""

import logging
from datetime import timedelta, timezone

from arq import cron, run_worker
from arq.connections import RedisSettings

from opennem import settings
from opennem.core.startup import worker_startup_alert
from opennem.tasks.tasks import (
    task_nem_interval_check,
)

# crawler_run_nem_dispatch_scada_crawl,
# crawler_run_nem_trading_is_crawl,
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

worker_startup_alert()


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
    logger.info("Starting worker")
    run_worker(WorkerSettings)
    logger.info("Worker done")


if __name__ == "__main__":
    main()
