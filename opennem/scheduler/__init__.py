from huey import RedisHuey, crontab

from opennem.api.exporter import wem_run_all
from opennem.settings import get_redis_host

REDIS_HOST = get_redis_host()

huey = RedisHuey("opennem.exporter", host=REDIS_HOST)


@huey.periodic_task(crontab(minute="*/10"))
def wem_export_task():
    wem_run_all()
