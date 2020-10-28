from huey import RedisHuey, crontab

from opennem.api.export.tasks import (
    au_export_power,
    wem_export_monthly,
    wem_export_power,
    wem_export_years,
)
from opennem.exporter.geojson import export_facility_geojson
from opennem.settings import settings

huey = RedisHuey("opennem.exporter", host=settings.cache_url.host)


@huey.periodic_task(crontab(minute="*/5"))
def schedule_wem_export_task():
    wem_export_power()


@huey.periodic_task(crontab(minute="*/15"))
def schedule_wem_export_all():
    wem_export_monthly()


@huey.periodic_task(crontab(minute="*/15"))
def schedule_wem_export_years():
    wem_export_years()


@huey.periodic_task(crontab(minute="*/5"))
def schedule_export_geojson():
    export_facility_geojson()


@huey.periodic_task(crontab(minute="*/30"))
def schedule_export_au():
    au_export_power()
