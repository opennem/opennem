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
from opennem.monitors.set_outputs import run_set_output_check
from opennem.notifications.slack import slack_message
from opennem.settings import settings

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


@huey.periodic_task(crontab(hour="12", minute="15"))
@huey.lock_task("schedule_power_weeklies_archive")
def schedule_power_weeklies_archive() -> None:
    """
    Run weekly power outputs entire archive. Note that this is 8000+ files at the moment

    @NOTE disabled as we will run manually
    """
    # export_power(priority=PriorityType.history)
    return None


@huey.periodic_task(crontab(hour="*/3", minute="45"), priority=50)
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


# set output check
@huey.periodic_task(crontab(hour="*/12", minute="30"), priority=30)
@huey.lock_task("schedule_run_set_output_check")
def schedule_run_set_output_check() -> None:
    run_set_output_check()
