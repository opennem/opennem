# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
# pylint: disable=no-member
"""
Primary scheduler runs:

 * website json export tasks
 * refreshing materialized views
 * monitoring tasks

"""
import logging
import platform

from huey import PriorityRedisHuey, crontab

from opennem.api.export.map import PriorityType, refresh_export_map, refresh_weekly_export_map
from opennem.api.export.tasks import (
    export_all_daily,
    export_all_monthly,
    export_electricitymap,
    export_energy,
    export_flows,
    export_metadata,
    export_power,
)
from opennem.crawl import CrawlerSchedule, run_crawl
from opennem.crawlers.apvi import APVIRooftopTodayCrawler
from opennem.crawlers.bom import BOMCapitals
from opennem.crawlers.nemweb import (
    AEMONEMDispatchActualGEN,
    AEMONEMNextDayDispatch,
    AEMONemwebDispatchIS,
    AEMONemwebRooftop,
    AEMONemwebRooftopForecast,
    AEMONemwebTradingIS,
    AEMONNemwebDispatchScada,
)
from opennem.crawlers.wem import WEMBalancing, WEMBalancingLive, WEMFacilityScada, WEMFacilityScadaLive
from opennem.exporter.geojson import export_facility_geojson
from opennem.exporter.historic import export_historic_intervals
from opennem.monitors.emissions import alert_missing_emission_factors
from opennem.monitors.facility_seen import facility_first_seen_check
from opennem.monitors.opennem import check_opennem_interval_delays
from opennem.notifications.slack import slack_message
from opennem.settings import IS_DEV, settings  # noqa: F401
from opennem.workers.backup import run_backup
from opennem.workers.daily_summary import run_daily_fueltech_summary
from opennem.workers.emissions import run_emission_update_day
from opennem.workers.facility_data_ranges import update_facility_seen_range
from opennem.workers.fallback import daily_runner

# from opennem.workers.fallback import fallback_runner
from opennem.workers.network_data_range import run_network_data_range_update
from opennem.workers.system import clean_tmp_dir

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

logger = logging.getLogger("openenm.scheduler")

regular_schedule_minute_interval = 1
frequent_schedule_minute_interval = 5

if IS_DEV:
    regular_schedule_minute_interval = 5
    frequent_schedule_minute_interval = 5


# crawler tasks live
@huey.periodic_task(crontab(minute=f"*/{regular_schedule_minute_interval}"))
@huey.lock_task("crawler_live_nemweb_dispatch_scada")
def crawl_run_aemo_nemweb_dispatch_scada() -> None:
    run_crawl(AEMONNemwebDispatchScada)
    export_power(priority=PriorityType.live)


@huey.periodic_task(crontab(minute=f"*/{regular_schedule_minute_interval}"))
@huey.lock_task("crawler_live_nemweb_dispatch_is")
def crawler_live_nemweb_dispatch_is() -> None:
    run_crawl(AEMONemwebDispatchIS)


@huey.periodic_task(crontab(minute=f"*/{regular_schedule_minute_interval}"))
@huey.lock_task("crawler_live_nemweb_trading_is")
def crawler_live_nemweb_trading_is() -> None:
    run_crawl(AEMONemwebTradingIS)


@huey.periodic_task(crontab(minute=f"*/{regular_schedule_minute_interval}"))
@huey.lock_task("crawler_live_nemweb_rooftop")
def crawler_live_nemweb_rooftop() -> None:
    run_crawl(AEMONemwebRooftop)


@huey.periodic_task(crontab(minute="*/10"))
@huey.lock_task("crawler_run_bom_capitals")
def crawler_run_bom_capitals() -> None:
    run_crawl(BOMCapitals)


# crawler tasks frequent
@huey.periodic_task(crontab(minute="*/5"))
@huey.lock_task("crawler_run_apvi_today")
def crawler_run_apvi_today() -> None:
    run_crawl(APVIRooftopTodayCrawler)


@huey.periodic_task(crontab(minute="*/5"))
@huey.lock_task("crawler_run_wem_balancing_live")
def crawler_run_wem_balancing_live() -> None:
    run_crawl(WEMBalancingLive)


@huey.periodic_task(crontab(minute="*/5"))
@huey.lock_task("crawler_run_wem_scada_live")
def crawler_run_wem_scada_live() -> None:
    run_crawl(WEMFacilityScadaLive)


@huey.periodic_task(crontab(hour="*/1"))
@huey.lock_task("crawler_run_wem_facility_scada")
def crawler_run_wem_facility_scada() -> None:
    run_crawl(WEMFacilityScada)


@huey.periodic_task(crontab(hour="*/1"))
@huey.lock_task("crawler_run_wem_balancing")
def crawler_run_wem_balancing() -> None:
    run_crawl(WEMBalancing)


@huey.periodic_task(crontab(hour="*/6", minute="33"), retries=5, retry_delay=90)
@huey.lock_task("crawler_run_aemo_nemweb_rooftop_forecast")
def crawler_run_aemo_nemweb_rooftop_forecast() -> None:
    run_crawl(AEMONemwebRooftopForecast)


# daily tasks
# run daily morning task
@huey.periodic_task(crontab(hour="7,14", minute="15"), retries=3, retry_delay=120)
@huey.lock_task("db_run_energy_gapfil")
def db_run_energy_gapfil() -> None:
    run_crawl(AEMONEMDispatchActualGEN)
    run_crawl(AEMONEMNextDayDispatch)
    daily_runner(days=2)


# export tasks
@huey.periodic_task(crontab(minute="*/10"), priority=90)
@huey.lock_task("schedule_live_tasks")
def schedule_live_tasks() -> None:
    export_power(priority=PriorityType.live)


@huey.periodic_task(crontab(minute="*/15"), priority=90)
@huey.lock_task("schedule_custom_tasks")
def schedule_custom_tasks() -> None:
    if settings.workers_run:
        export_electricitymap()
        export_flows()


@huey.periodic_task(crontab(hour="8", minute="15"), priority=50)
@huey.lock_task("schedule_export_all_daily")
def schedule_export_all_daily() -> None:
    if settings.workers_run:
        export_all_daily()
        export_all_monthly()


@huey.periodic_task(crontab(hour="*/12", minute="19"))
@huey.lock_task("schedule_power_weeklies")
def schedule_power_weeklies() -> None:
    """
    Run weekly power outputs
    """
    export_power(priority=PriorityType.history, latest=True)


@huey.periodic_task(crontab(hour="*/4", minute="45"))
@huey.lock_task("run_export_latest_historic_intervals")
def run_export_latest_historic_intervals() -> None:
    """Run latest historic exports"""
    export_historic_intervals(limit=1)


@huey.periodic_task(crontab(hour="*/4", minute="15"), priority=90)
@huey.lock_task("schedule_hourly_tasks")
def schedule_hourly_tasks() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.daily, latest=True)


@huey.periodic_task(crontab(hour="10", minute="45"))
@huey.lock_task("schedule_daily_tasks")
def schedule_daily_tasks() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.daily)


@huey.periodic_task(crontab(hour="12", minute="15"), priority=30)
@huey.lock_task("schedule_energy_monthlies")
def schedule_energy_monthlies() -> None:
    if settings.workers_run:
        export_energy(priority=PriorityType.monthly)


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


# Monitoring tasks
@huey.periodic_task(crontab(hour="10", minute="45"))
@huey.lock_task("db_run_daily_fueltech_summary")
def db_run_daily_fueltech_summary() -> None:
    run_daily_fueltech_summary()


# @huey.periodic_task(crontab(hour="18", minute="30"), retries=4, retry_delay=120)
# @huey.lock_task("db_run_aggregates_all")
# def db_run_aggregates_all() -> None:
#     run_aggregates_all()


@huey.periodic_task(crontab(hour="6", minute="45"))
@huey.lock_task("db_run_emission_tasks")
def db_run_emission_tasks() -> None:
    try:
        run_emission_update_day(days=12)
    except Exception as e:
        logger.error("Error running emission update: {}".format(str(e)))


@huey.periodic_task(crontab(minute="*/60"), priority=80)
@huey.lock_task("monitor_opennem_intervals")
def monitor_opennem_intervals() -> None:
    if settings.env != "production":
        return None

    for network_code in ["NEM", "WEM"]:
        check_opennem_interval_delays(network_code)


@huey.periodic_task(crontab(hour="8", minute="45"), priority=10)
@huey.lock_task("monitor_emission_factors")
def monitor_emission_factors() -> None:
    alert_missing_emission_factors()


# worker tasks
@huey.periodic_task(crontab(hour="10", minute="1"))
@huey.lock_task("schedule_facility_first_seen_check")
def schedule_facility_first_seen_check() -> None:
    """Check for new DUIDS"""
    if settings.env == "production":
        facility_first_seen_check()


@huey.periodic_task(crontab(hour="9", minute="45"))
@huey.lock_task("db_facility_seen_update")
def db_facility_seen_update() -> None:
    update_facility_seen_range()
    slack_message(f"Updated facility seen range on {settings.env}")


@huey.periodic_task(crontab(hour="10", minute="15"))
@huey.lock_task("run_run_network_data_range_update")
def run_run_network_data_range_update() -> None:
    run_network_data_range_update()
    slack_message("Ran network data range on {}".format(settings.env))


@huey.periodic_task(crontab(hour="1,12", minute="30"))
@huey.lock_task("run_refresh_export_maps")
def run_refresh_export_maps() -> None:
    refresh_export_map()
    refresh_weekly_export_map()


# admin tasks


@huey.periodic_task(crontab(day="1", hour="15", minute="45"))
@huey.lock_task("task_run_backup")
def task_run_backup() -> None:
    dest_file = run_backup()
    slack_message(f"Ran backup on {settings.env} to {dest_file}")


@huey.periodic_task(crontab(hour="8,16", minute="45"))
@huey.lock_task("run_clean_tmp_dir")
def run_clean_tmp_dir() -> None:
    clean_tmp_dir()
