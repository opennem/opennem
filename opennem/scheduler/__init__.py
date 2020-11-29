# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
from huey import RedisHuey, crontab

from opennem.api.export.map import PriorityType
from opennem.api.export.tasks import (
    export_energy,
    export_metadata,
    export_power,
)
from opennem.exporter.geojson import export_facility_geojson
from opennem.monitors.aemo_intervals import get_wem_interval_delay
from opennem.monitors.opennem_metadata import check_metadata_status
from opennem.settings import settings

redis_host = None

if settings.cache_url:
    redis_host = settings.cache_url.host

huey = RedisHuey("opennem.exporter", host=redis_host)
# export tasks


@huey.periodic_task(crontab(minute="*/2"))
@huey.lock_task("schedule_live_tasks")
def schedule_live_tasks() -> None:
    export_power(PriorityType.live)


@huey.periodic_task(crontab(hour="*/6"))
@huey.lock_task("schedule_power_weeklies")
def schedule_power_weeklies() -> None:
    """
    Run weekly power outputs
    """
    export_power(PriorityType.history, latest=True)


@huey.periodic_task(crontab(hour="*/1"))
@huey.lock_task("schedule_hourly_tasks")
def schedule_hourly_tasks() -> None:
    export_energy(PriorityType.daily, latest=True)


@huey.periodic_task(crontab(hour="*/6"))
@huey.lock_task("schedule_daily_tasks")
def schedule_daily_tasks() -> None:
    export_energy(PriorityType.daily)


@huey.periodic_task(crontab(hour="*/12"))
@huey.lock_task("schedule_energy_monthlies")
def schedule_energy_monthlies() -> None:
    export_energy(PriorityType.monthly)


# geojson maps
@huey.periodic_task(crontab(minute="*/30"))
@huey.lock_task("schedule_export_geojson")
def schedule_export_geojson() -> None:
    export_facility_geojson()


# metadata
@huey.periodic_task(crontab(minute="*/30"))
@huey.lock_task("schedule_export_metadata")
def schedule_export_metadata() -> None:
    export_metadata()


# monitoring tasks
@huey.periodic_task(crontab(minute="*/1"))
@huey.lock_task("monitor_wem_interval")
def monitor_wem_interval() -> None:
    get_wem_interval_delay()


@huey.periodic_task(crontab(hour="*/1"))
@huey.lock_task("monitor_metadata_status")
def monitor_metadata_status() -> None:
    check_metadata_status()
