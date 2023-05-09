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

from huey import PriorityRedisHuey, crontab

from opennem import settings
from opennem.aggregates.facility_daily import run_facility_aggregates_for_latest_interval
from opennem.aggregates.network_demand import run_demand_aggregates_for_latest_interval  # noqa: F401
from opennem.api.export.map import PriorityType, refresh_export_map, refresh_weekly_export_map
from opennem.api.export.tasks import export_electricitymap, export_flows, export_metadata, export_power
from opennem.core.profiler import cleanup_database_task_profiles_basedon_retention
from opennem.core.startup import worker_startup_alert
from opennem.crawl import run_crawl
from opennem.crawlers.bom import BOMCapitals
from opennem.exporter.geojson import export_facility_geojson
from opennem.monitors.emissions import alert_missing_emission_factors
from opennem.monitors.facility_seen import facility_first_seen_check
from opennem.monitors.opennem import check_opennem_interval_delays
from opennem.pipelines.crontab import network_interval_crontab
from opennem.pipelines.nem import (
    nem_dispatch_is_crawl,
    nem_dispatch_scada_crawl,
    nem_per_day_check,
    nem_rooftop_crawl,
    nem_trading_is_crawl,
)
from opennem.pipelines.wem import wem_per_interval_check
from opennem.schema.network import NetworkAEMORooftop, NetworkNEM, NetworkWEM
from opennem.workers.daily import energy_runner_hours
from opennem.workers.daily_summary import run_daily_fueltech_summary
from opennem.workers.facility_data_ranges import update_facility_seen_range
from opennem.workers.facility_status import update_opennem_facility_status
from opennem.workers.network_data_range import run_network_data_range_update
from opennem.workers.system import clean_tmp_dir

huey = PriorityRedisHuey("opennem.scheduler", url=settings.cache_url)

logger = logging.getLogger("openenm.scheduler")

# send the startup message to slack
worker_startup_alert()


# crawler tasks live per interval for each network
@huey.periodic_task(network_interval_crontab(network=NetworkNEM), priority=50, retries=5, retry_delay=10)
@huey.lock_task("crawler_run_nem_dispatch_scada_crawl")
def crawler_run_nem_dispatch_scada_crawl() -> None:
    """dispatch_scada for NEM crawl"""
    nem_dispatch_scada_crawl()


@huey.periodic_task(network_interval_crontab(network=NetworkNEM), priority=50, retries=5, retry_delay=10)
@huey.lock_task("crawler_run_nem_dispatch_is_crawl")
def crawler_run_nem_dispatch_is_crawl() -> None:
    """dispatch_is for NEM crawl"""
    nem_dispatch_is_crawl()


@huey.periodic_task(network_interval_crontab(network=NetworkNEM), priority=50, retries=5, retry_delay=10)
@huey.lock_task("crawler_run_nem_trading_is_crawl")
def crawler_run_nem_trading_is_crawl() -> None:
    """dispatch_is for NEM crawl"""
    nem_trading_is_crawl()


@huey.periodic_task(network_interval_crontab(network=NetworkNEM), priority=50, retries=5, retry_delay=30)
@huey.lock_task("run_per_interval_flows_and_exports")
def run_per_interval_flows_and_exports() -> None:
    pass
    # @note Disabled
    # per_interval_flows_and_exports()


@huey.periodic_task(
    network_interval_crontab(network=NetworkAEMORooftop, number_minutes=1), priority=50, retries=5, retry_delay=15
)
@huey.lock_task("crawler_run_nem_rooftop_per_interval")
def crawler_run_nem_rooftop_per_interval() -> None:
    nem_rooftop_crawl()


@huey.periodic_task(network_interval_crontab(network=NetworkWEM, number_minutes=1), priority=50, retries=5, retry_delay=15)
@huey.lock_task("crawler_run_wem_per_interval")
def crawler_run_wem_per_interval() -> None:
    wem_per_interval_check()


@huey.periodic_task(crontab(minute="*/10"), priority=1)
@huey.lock_task("crawler_run_bom_capitals")
def crawler_run_bom_capitals() -> None:
    run_crawl(BOMCapitals)


# Run energy runner for per-interval processing
@huey.periodic_task(crontab(minute="7"), priority=1)
@huey.lock_task("run_hourly_task_runner")
def run_hourly_task_runner() -> None:
    if settings.per_interval_aggregate_processing:
        energy_runner_hours(hours=1)

        for network in [NetworkNEM, NetworkWEM]:
            run_facility_aggregates_for_latest_interval(network=network)
            run_demand_aggregates_for_latest_interval(network=network)


# Checks for the overnights from aemo and then runs the daily runner
@huey.periodic_task(crontab(hour="5,15", minute="20"), retries=3, retry_delay=60, priority=50)
@huey.lock_task("nem_overnight_check")
def nem_overnight_check() -> None:
    nem_per_day_check()


# run summary
@huey.periodic_task(crontab(hour="10", minute="40"), retries=3, retry_delay=120)
@huey.lock_task("run_daily_fueltech_summary")
def nem_summary_schedule_crawl() -> None:
    run_daily_fueltech_summary(network=NetworkNEM)


@huey.periodic_task(crontab(hour="10", minute="50"), retries=3, retry_delay=120)
@huey.lock_task("run_update_opennem_facility_status")
def run_update_opennem_facility_status() -> None:
    update_opennem_facility_status()


# export tasks
@huey.periodic_task(crontab(minute="*/15"), priority=90)
@huey.lock_task("schedule_custom_tasks")
def schedule_custom_tasks() -> None:
    if settings.workers_run:
        export_electricitymap()
        export_flows()


@huey.periodic_task(crontab(hour="2", minute="19"))
@huey.lock_task("schedule_power_weeklies")
def schedule_power_weeklies() -> None:
    """
    Run weekly power outputs
    """
    export_power(priority=PriorityType.history, latest=False)


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
@huey.periodic_task(crontab(minute="*/60"), priority=80)
@huey.lock_task("monitor_opennem_intervals")
def monitor_opennem_intervals() -> None:
    if settings.env != "production":
        return None

    for network_code in ["NEM", "WEM"]:
        check_opennem_interval_delays(network_code)


@huey.periodic_task(crontab(hour="21", minute="15"), priority=10)
@huey.lock_task("monitor_emission_factors")
def monitor_emission_factors() -> None:
    alert_missing_emission_factors()


# worker tasks
@huey.periodic_task(crontab(hour="21", minute="45"))
@huey.lock_task("schedule_facility_first_seen_check")
def schedule_facility_first_seen_check() -> None:
    """Check for new DUIDS"""
    if settings.env == "production":
        facility_first_seen_check()


@huey.periodic_task(crontab(hour="22", minute="15"))
@huey.lock_task("db_facility_seen_update")
def db_facility_seen_update() -> None:
    update_facility_seen_range()


@huey.periodic_task(crontab(hour="*/1", minute="15"))
@huey.lock_task("run_run_network_data_range_update")
def run_run_network_data_range_update() -> None:
    """Updates network data_range"""
    run_network_data_range_update()


@huey.periodic_task(crontab(hour="1,12", minute="30"))
@huey.lock_task("run_refresh_export_maps")
def run_refresh_export_maps() -> None:
    refresh_export_map()
    refresh_weekly_export_map()


# energy worker tasks
@huey.periodic_task(crontab(hour="*/1", minute="10"))
@huey.lock_task("run_energy_runner_hours")
def run_energy_runner_hours() -> None:
    energy_runner_hours(hours=1)


# system tasks
@huey.periodic_task(crontab(hour="*/2", minute="55"))
@huey.lock_task("run_clean_tmp_dir")
def run_clean_tmp_dir() -> None:
    clean_tmp_dir()


@huey.periodic_task(crontab(hour="22", minute="55"))
@huey.lock_task("run_cleanup_database_task_profiles_basedon_retention")
def run_cleanup_database_task_profiles_basedon_retention() -> None:
    cleanup_database_task_profiles_basedon_retention()
