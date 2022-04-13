# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
"""
Primary scheduler runs:

 * website json export tasks
 * refreshing materialized views
 * monitoring tasks

"""
import logging
import platform

from huey import PriorityRedisHuey, crontab

from opennem.api.export.map import PriorityType
from opennem.api.export.tasks import (
    export_all_daily,
    export_all_monthly,
    export_electricitymap,
    export_energy,
    export_flows,
    export_metadata,
    export_power,
)
from opennem.crawl import CrawlerSchedule, run_crawls_by_schedule
from opennem.exporter.geojson import export_facility_geojson
from opennem.monitors.emissions import alert_missing_emission_factors
from opennem.monitors.facility_seen import facility_first_seen_check
from opennem.monitors.opennem import check_opennem_interval_delays
from opennem.monitors.set_outputs import run_set_output_check
from opennem.notifications.slack import slack_message
from opennem.settings import IS_DEV, settings  # noqa: F401
from opennem.workers.aggregates import run_aggregates_all, run_aggregates_all_days
from opennem.workers.daily_summary import run_daily_fueltech_summary
from opennem.workers.emissions import run_emission_update_day
from opennem.workers.facility_data_ranges import update_facility_seen_range
from opennem.workers.gap_fill.energy import run_energy_gapfill

# Py 3.8 on MacOS changed the default multiprocessing model
if platform.system() == "Darwin":
    import multiprocessing

    try:
        multiprocessing.set_start_method("fork")
    except RuntimeError:
        # sometimes it has already been set by
        # other libs
        pass

redis_host = None

if settings.cache_url:
    redis_host = settings.cache_url.host

huey = PriorityRedisHuey("opennem.scheduler", host=redis_host)

logger = logging.getLogger("openenm.scheduler")

regular_schedule_minute_interval = 1

if IS_DEV:
    regular_schedule_minute_interval = 5

# crawler tasks
@huey.periodic_task(crontab(minute=f"*/{regular_schedule_minute_interval}"))
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


# export tasks
@huey.periodic_task(crontab(minute="*/5"), priority=90)
@huey.lock_task("schedule_live_tasks")
def schedule_live_tasks() -> None:
    if settings.workers_run:
        export_power(priority=PriorityType.live)


@huey.periodic_task(crontab(minute="*/15"), priority=90)
@huey.lock_task("schedule_custom_tasks")
def schedule_custom_tasks() -> None:
    if settings.workers_run:
        export_electricitymap()
        export_flows()


@huey.periodic_task(crontab(hour="*/2", minute="15"), priority=50)
@huey.lock_task("schedule_export_all_daily")
def schedule_export_all_daily() -> None:
    if settings.workers_run:
        export_all_daily()
        slack_message("Finished running export_all_daily on {}".format(settings.env))


@huey.periodic_task(crontab(hour="*/2", minute="15"), priority=50)
@huey.lock_task("schedule_export_all_monthly")
def schedule_export_all_monthly() -> None:
    if settings.workers_run:
        export_all_monthly()
        slack_message("Finished running export_all_monthly on {}".format(settings.env))


@huey.periodic_task(crontab(hour="*/12", minute="19"))
@huey.lock_task("schedule_power_weeklies")
def schedule_power_weeklies() -> None:
    """
    Run weekly power outputs
    """
    export_power(priority=PriorityType.history, latest=True)


@huey.periodic_task(crontab(hour="*/1", minute="15,45"), priority=50)
@huey.lock_task("schedule_hourly_tasks")
def schedule_hourly_tasks() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.daily, latest=True)


@huey.periodic_task(crontab(hour="*/2", minute="45"))
@huey.lock_task("schedule_daily_tasks")
def schedule_daily_tasks() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.daily)


@huey.periodic_task(crontab(hour="*/2", minute="15"), priority=30)
@huey.lock_task("schedule_energy_monthlies")
def schedule_energy_monthlies() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.monthly)


# geojson maps
@huey.periodic_task(crontab(minute="*/30"), priority=50)
@huey.lock_task("schedule_export_geojson")
def schedule_export_geojson() -> None:
    if settings.workers_run:
        export_facility_geojson()


# metadata
@huey.periodic_task(crontab(hour="*/12", minute="30"), priority=30)
@huey.lock_task("schedule_export_metadata")
def schedule_export_metadata() -> None:
    if settings.workers_run:
        export_metadata()


# Monitoring tasks

# set output check
@huey.periodic_task(crontab(hour="*/12", minute="30"), priority=30)
@huey.lock_task("schedule_run_set_output_check")
def schedule_run_set_output_check() -> None:
    run_set_output_check()


@huey.periodic_task(crontab(hour="10", minute="45"))
@huey.lock_task("db_run_daily_fueltech_summary")
def db_run_daily_fueltech_summary() -> None:
    run_daily_fueltech_summary()


# run gap fill tasks
@huey.periodic_task(crontab(hour="*/1", minute="15"))
@huey.lock_task("db_run_energy_gapfil")
def db_run_energy_gapfil() -> None:
    run_energy_gapfill(days=14)

    # Run flow updates
    run_emission_update_day(days=2)


@huey.periodic_task(crontab(hour="8,16", minute="30"))
@huey.lock_task("db_run_aggregates_all")
def db_run_aggregates_all() -> None:
    run_aggregates_all()


@huey.periodic_task(crontab(hour="6", minute="45"))
@huey.lock_task("db_run_emission_tasks")
def db_run_emission_tasks() -> None:
    try:
        run_emission_update_day(days=12)
    except Exception as e:
        logger.error("Error running emission update: {}".format(str(e)))


@huey.periodic_task(crontab(minute="*/60"), priority=80)
@huey.lock_task("monitor_opennem_intervals")
def monitor_opennem_intervals() -> None:
    if settings.env != "production":
        return None

    for network_code in ["NEM", "WEM"]:
        check_opennem_interval_delays(network_code)


# @NOTE temp disable new monitoring
# @huey.periodic_task(crontab(minute="*/60"), priority=50)
# @huey.lock_task("monitor_wem_interval")
# def monitor_wem_interval() -> None:
#     if settings.env != "production":
#         return None

# aemo_wem_live_interval()


@huey.periodic_task(crontab(hour="8", minute="45"), priority=10)
@huey.lock_task("monitor_emission_factors")
def monitor_emission_factors() -> None:
    alert_missing_emission_factors()


# worker tasks
@huey.periodic_task(crontab(hour="10", minute="1"))
@huey.lock_task("schedule_facility_first_seen_check")
def schedule_facility_first_seen_check() -> None:
    """Check for new DUIDS"""
    if settings.env == "production":
        facility_first_seen_check()


@huey.periodic_task(crontab(hour="9,18", minute="45"))
@huey.lock_task("db_facility_seen_update")
def db_facility_seen_update() -> None:
    update_facility_seen_range()
    slack_message(f"Updated facility seen range on {settings.env}")
