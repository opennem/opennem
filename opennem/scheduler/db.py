# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
import platform

from huey import PriorityRedisHuey, crontab

from opennem.db.tasks import refresh_material_views, refresh_timescale_views
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

huey = PriorityRedisHuey("opennem.scheduler.db", host=redis_host)


# database tasks
# @huey.periodic_task(crontab(hour="*/3"))
# @huey.lock_task("db_refresh_ts_views")
# def db_refresh_ts_views() -> None:
#     refresh_timescale_views()


# @huey.periodic_task(crontab(minute="*/5"))
# @huey.lock_task("db_refresh_interchange")
# def db_refresh_interchange() -> None:
#     refresh_timescale_views("mv_interchange_power_nem_region", days=1)


@huey.periodic_task(crontab(hour="*/6"))
@huey.lock_task("db_refresh_material_views")
def db_refresh_material_views() -> None:
    refresh_material_views()


@huey.periodic_task(crontab(hour="/6"), priority=10)
@huey.lock_task("db_refresh_all")
def db_refresh_all() -> None:
    refresh_timescale_views(all=True)
