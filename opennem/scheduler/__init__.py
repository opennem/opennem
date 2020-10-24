from huey import RedisHuey, crontab

from opennem.api.exporter import wem_export_all, wem_run_all
from opennem.exporter.geojson import export_facility_geojson
from opennem.settings import settings

huey = RedisHuey("opennem.exporter", host=settings.cache_url.host)


@huey.periodic_task(crontab(minute="*/5"))
def schedule_wem_export_task():
    wem_run_all()


@huey.periodic_task(crontab(hour="*/12"))
def schedule_wem_export_all():
    wem_export_all()


@huey.periodic_task(crontab(minute="*/5"))
def schedule_export_geojson():
    export_facility_geojson()
