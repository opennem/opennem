# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
import logging
import platform

from huey import PriorityRedisHuey, crontab

from opennem import settings
from opennem.crawl import CrawlerSchedule, run_crawls_by_schedule

# Py 3.8 on MacOS changed the default multiprocessing model
if platform.system() == "Darwin":
    import multiprocessing

    try:
        multiprocessing.set_start_method("fork")
    except RuntimeError:
        # sometimes it has already been set by
        # other libs
        pass

logger = logging.getLogger("openenm.crawler")

redis_host = None

if settings.cache_url:
    redis_host = settings.cache_url.host  # type: ignore

huey = PriorityRedisHuey("opennem.scheduler.crawler", host=redis_host)


# crawler tasks
@huey.periodic_task(crontab(minute="*/1"))
@huey.lock_task("crawler_scheduled_live")
def crawler_scheduled_live() -> None:
    run_crawls_by_schedule(CrawlerSchedule.live)


@huey.periodic_task(crontab(minute="*/5"))
@huey.lock_task("crawler_scheduled_frequent")
def crawler_scheduled_frequent() -> None:
    run_crawls_by_schedule(CrawlerSchedule.frequent)


@huey.periodic_task(crontab(minute="*/15"), retries=3, retry_delay=30)
@huey.lock_task("crawler_scheduled_quarter_hour")
def crawler_scheduled_quarter_hour() -> None:
    run_crawls_by_schedule(CrawlerSchedule.quarter_hour)


@huey.periodic_task(crontab(hour="*", minute="3,33"), retries=3, retry_delay=30)
@huey.lock_task("crawler_scheduled_half_hour")
def crawler_scheduled_half_hour() -> None:
    run_crawls_by_schedule(CrawlerSchedule.half_hour)


@huey.periodic_task(crontab(hour="*/1", minute="2"), retries=5, retry_delay=90)
@huey.lock_task("crawler_scheduled_hourly")
def crawler_scheduled_hourly() -> None:
    run_crawls_by_schedule(CrawlerSchedule.hourly)


@huey.periodic_task(crontab(hour="*/6", minute="33"), retries=5, retry_delay=90)
@huey.lock_task("crawler_scheduled_four_times_a_day")
def crawler_scheduled_four_times_a_day() -> None:
    run_crawls_by_schedule(CrawlerSchedule.four_times_a_day)


@huey.periodic_task(crontab(hour="1,13", minute="41"), retries=5, retry_delay=90)
@huey.lock_task("crawler_scheduled_twice_a_day")
def crawler_scheduled_twice_a_day() -> None:
    run_crawls_by_schedule(CrawlerSchedule.twice_a_day)


@huey.periodic_task(crontab(hour="5,8,16", minute="15"), retries=5, retry_delay=120)
@huey.lock_task("crawler_scheduled_day")
def crawler_scheduled_day() -> None:
    run_crawls_by_schedule(CrawlerSchedule.daily)
