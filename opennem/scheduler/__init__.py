from huey import RedisHuey, crontab

from opennem.api.export.map import PriorityType
from opennem.api.export.tasks import (
    export_energy,
    export_metadata,
    export_power,
    wem_export_daily,
    wem_export_monthly,
    wem_export_power,
)
from opennem.exporter.geojson import export_facility_geojson
from opennem.monitors.aemo_intervals import get_wem_interval_delay
from opennem.settings import settings

huey = RedisHuey("opennem.exporter", host=settings.cache_url.host)

# export tasks


@huey.periodic_task(crontab(minute="*/5"))
@huey.lock_task("schedule_live_tasks")
def schedule_live_tasks():
    wem_export_power()
    export_power(PriorityType.live)


@huey.periodic_task(crontab(hour="*/1"))
@huey.lock_task("schedule_hourly_tasks")
def schedule_hourly_tasks():
    wem_export_daily(limit=1)
    export_energy(PriorityType.daily, latest=True)


@huey.periodic_task(crontab(hour="*/12"))
@huey.lock_task("schedule_daily_tasks")
def schedule_daily_tasks():
    wem_export_daily()
    export_energy(PriorityType.daily)


@huey.periodic_task(crontab(hour="*/12"))
@huey.lock_task("schedule_wem_export_all")
def schedule_wem_export_all():
    wem_export_monthly()
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
@huey.periodic_task(crontab(minute="*/5"))
@huey.lock_task("monitor_wem_interval")
def monitor_wem_interval():
    get_wem_interval_delay()
