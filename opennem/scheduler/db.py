# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
import platform

from huey import PriorityRedisHuey, crontab

from opennem.api.export.tasks import export_energy
from opennem.db.tasks import refresh_material_views
from opennem.notifications.slack import slack_message
from opennem.settings import settings
from opennem.workers.energy import run_energy_update_days
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

huey = PriorityRedisHuey("opennem.scheduler.db", host=redis_host)

# 6:45AM AEST
@huey.periodic_task(crontab(hour="20,23", minute="45"))
@huey.lock_task("db_refresh_material_views")
def db_refresh_material_views() -> None:
    run_energy_update_days(days=2)
    refresh_material_views("mv_facility_all")
    refresh_material_views("mv_network_fueltech_days")
    refresh_material_views("mv_region_emissions")
    refresh_material_views("mv_interchange_energy_nem_region")
    export_energy(latest=False)
    slack_message("Ran daily energy update and material views on {}".format(settings.env))


# Catchup task
@huey.periodic_task(crontab(hour="2, 14", minute="45"))
def db_refresh_catchup() -> None:
    refresh_material_views("mv_network_fueltech_days")
    refresh_material_views("mv_region_emissions")
    refresh_material_views("mv_interchange_energy_nem_region")


@huey.periodic_task(crontab(hour="*/1", minute="15,45"))
@huey.lock_task("db_refresh_material_views_recent")
def db_refresh_material_views_recent() -> None:
    refresh_material_views("mv_facility_45d")
    refresh_material_views("mv_region_emissions_45d")


# @NOTE optimized can now run every hour but shouldn't have to
@huey.periodic_task(crontab(hour="*/1", minute="10,40"))
@huey.lock_task("db_refresh_energies_yesterday")
def db_refresh_energies_yesterday() -> None:
    run_energy_update_days(days=2)


@huey.periodic_task(crontab(hour="22"))
@huey.lock_task("db_facility_seen_update")
def db_facility_seen_update() -> None:
    if settings.workers_db_run:
        update_facility_seen_range(False)
        slack_message("Ran facility seen range on {}".format(settings.env))
