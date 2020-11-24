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
def schedule_live_tasks():
    export_power(PriorityType.live)


@huey.periodic_task(crontab(hour="*/1"))
@huey.lock_task("schedule_hourly_tasks")
def schedule_hourly_tasks():
    export_energy(PriorityType.daily, latest=True)


@huey.periodic_task(crontab(hour="*/6"))
@huey.lock_task("schedule_daily_tasks")
def schedule_daily_tasks():
    export_energy(PriorityType.daily)


@huey.periodic_task(crontab(hour="*/6"))
@huey.lock_task("schedule_wem_export_all")
def schedule_wem_export_all():
    export_energy(PriorityType.monthly)


@huey.periodic_task(crontab(minute="*/30"))
@huey.lock_task("schedule_export_geojson")
def schedule_export_geojson():
    export_facility_geojson()


@huey.periodic_task(crontab(minute="*/30"))
@huey.lock_task("schedule_export_metadata")
def schedule_export_metadata():
    export_metadata()


# monitoring tasks
@huey.periodic_task(crontab(minute="*/1"))
@huey.lock_task("monitor_wem_interval")
def monitor_wem_interval():
    get_wem_interval_delay()


@huey.periodic_task(crontab(hour="*/1"))
@huey.lock_task("monitor_metadata_status")
def monitor_metadata_status():
    check_metadata_status()
