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


@huey.periodic_task(crontab(minute="*/5",))
def schedule_wem_export_task():
    wem_export_power()
    export_power(PriorityType.live)


@huey.periodic_task(crontab(hour="*/1"))
def schedule_wem_export_daily_most_recent():
    wem_export_daily(limit=1)
    export_energy(PriorityType.daily, latest=True)


@huey.periodic_task(crontab(hour="*/12"))
def schedule_wem_export_years():
    wem_export_daily()
    export_energy(PriorityType.daily)


@huey.periodic_task(crontab(hour="*/12"))
def schedule_wem_export_all():
    wem_export_monthly()
    export_energy(PriorityType.monthly)


@huey.periodic_task(crontab(minute="*/30"))
def schedule_export_geojson():
    export_facility_geojson()


@huey.periodic_task(crontab(minute="*/30"))
def schedule_export_au():
    export_metadata()


# monitoring tasks
@huey.periodic_task(crontab(minute="*/5"))
def monitor_wem_interval():
    get_wem_interval_delay()
