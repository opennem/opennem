# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
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
from opennem.exporter.geojson import export_facility_geojson
from opennem.monitors.aemo_intervals import aemo_wem_live_interval
from opennem.monitors.database import check_database_live
from opennem.monitors.emissions import alert_missing_emission_factors
from opennem.monitors.facility_seen import facility_first_seen_check
from opennem.monitors.opennem import check_opennem_interval_delays
from opennem.notifications.slack import slack_message
from opennem.settings import settings
from opennem.utils.scrapyd import job_schedule_all
from opennem.workers.facility_data_ranges import update_facility_seen_range

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


# export tasks
@huey.periodic_task(crontab(minute="*/5"), priority=90)
@huey.lock_task("schedule_live_tasks")
def schedule_live_tasks() -> None:
    if settings.workers_run:
        export_power(priority=PriorityType.live)
        export_flows()


@huey.periodic_task(crontab(minute="*/15"), priority=90)
@huey.lock_task("schedule_custom_tasks")
def schedule_custom_tasks() -> None:
    if settings.workers_run:
        export_electricitymap()


@huey.periodic_task(crontab(hour="13", minute="15"), priority=50)
@huey.lock_task("schedule_export_all_daily")
def schedule_export_all_daily() -> None:
    if settings.workers_run:
        export_all_daily()
        slack_message("Finished running export_all_daily on {}".format(settings.env))


@huey.periodic_task(crontab(hour="12", minute="15"), priority=50)
@huey.lock_task("schedule_export_all_monthly")
def schedule_export_all_monthly() -> None:
    if settings.workers_run:
        export_all_monthly()
        slack_message("Finished running export_all_monthly on {}".format(settings.env))


@huey.periodic_task(crontab(hour="*/1", minute="15, 45"), priority=50)
@huey.lock_task("schedule_hourly_tasks")
def schedule_hourly_tasks() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.daily, latest=True)


@huey.periodic_task(crontab(hour="22", minute="45"))
@huey.lock_task("schedule_daily_tasks")
def schedule_daily_tasks() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.daily)
        slack_message("Finished running energy dailies on {}".format(settings.env))


@huey.periodic_task(crontab(hour="22", minute="15"), priority=30)
@huey.lock_task("schedule_energy_monthlies")
def schedule_energy_monthlies() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.monthly)
        slack_message("Finished running energy_monthlies on {}".format(settings.env))


# geojson maps
@huey.periodic_task(crontab(hour="*/1"), priority=50)
@huey.lock_task("schedule_export_geojson")
def schedule_export_geojson() -> None:
    if settings.workers_run:
        export_facility_geojson()


# metadata
@huey.periodic_task(crontab(hour="*/12"), priority=30)
@huey.lock_task("schedule_export_metadata")
def schedule_export_metadata() -> None:
    if settings.workers_run:
        export_metadata()


# monitoring tasks
@huey.periodic_task(crontab(minute="*/30"), priority=80)
@huey.lock_task("monitor_opennem_intervals")
def monitor_opennem_intervals() -> None:
    for network_code in ["NEM", "WEM"]:
        check_opennem_interval_delays(network_code)


@huey.periodic_task(crontab(minute="*/30"), priority=50)
@huey.lock_task("monitor_wem_interval")
def monitor_wem_interval() -> None:
    aemo_wem_live_interval()


@huey.periodic_task(crontab(hour="12", minute="45"), priority=10)
@huey.lock_task("monitor_emission_factors")
def monitor_emission_factors() -> None:
    alert_missing_emission_factors()


@huey.periodic_task(crontab(hour="*", minute="*/30"))
def monitor_database() -> None:
    check_database_live()


# worker tasks
@huey.periodic_task(crontab(hour="23", minute="1"))
@huey.lock_task("schedule_facility_first_seen_check")
def schedule_facility_first_seen_check() -> None:
    """Check for new DUIDS"""
    facility_first_seen_check()


@huey.periodic_task(crontab(hour="4,10,16,22", minute="1"))
@huey.lock_task("db_facility_seen_update")
def db_facility_seen_update() -> None:
    if settings.workers_db_run:
        r = update_facility_seen_range()

        if r:
            slack_message("Ran facility seen range on {}".format(settings.env))


# spider tasks
@huey.periodic_task(crontab(hour="23", minute="55"))
@huey.lock_task("schedule_spider_catchup_tasks")
def spider_catchup_tasks() -> None:
    catchup_spiders = [
        "au.bom.capitals",
        "au.apvi.current",
        "au.nem.day.dispatch_is",
        "au.nem.day.dispatch_scada",
        "au.nem.day.rooftop",
        "au.nem.day.trading_is",
        "au.nem.week.dispatch",
        "au.nem.week.dispatch_actual_gen",
    ]

    for _spider_name in catchup_spiders:
        job_schedule_all(_spider_name)
