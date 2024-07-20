"""
Primary scheduler runs:

 * website json export tasks
 * refreshing materialized views
 * monitoring tasks

"""

import asyncio
import logging

from huey import PriorityRedisHuey, crontab

from opennem import settings
from opennem.api.export.map import PriorityType
from opennem.api.export.tasks import export_electricitymap, export_flows, export_power
from opennem.core.profiler import cleanup_database_task_profiles_basedon_retention
from opennem.core.startup import worker_startup_alert
from opennem.crawl import run_crawl
from opennem.crawlers.bom import BOMCapitals
from opennem.exporter.geojson import export_facility_geojson
from opennem.monitors.facility_seen import facility_first_seen_check
from opennem.pipelines.crontab import network_interval_crontab
from opennem.pipelines.nem import (
    nem_dispatch_is_crawl,
    nem_dispatch_scada_crawl,
    nem_per_day_check,
    nem_rooftop_crawl,
    nem_trading_is_crawl,
)
from opennem.pipelines.wem import wem_per_interval_check
from opennem.schema.network import NetworkAEMORooftop, NetworkNEM
from opennem.utils.sync import run_async_task_reusable
from opennem.workers.daily import daily_catchup_runner
from opennem.workers.facility_data_ranges import update_facility_seen_range
from opennem.workers.network_data_range import run_network_data_range_update
from opennem.workers.system import clean_tmp_dir

huey = PriorityRedisHuey("opennem.scheduler", url=str(settings.redis_url))

logger = logging.getLogger("openenm.scheduler")

# send the startup message to slack
worker_startup_alert()


# crawler tasks live per interval for each network
@huey.periodic_task(network_interval_crontab(network=NetworkNEM), priority=50, retries=2, retry_delay=10)
@huey.lock_task("crawler_run_nem_dispatch_scada_crawl")
def crawler_run_nem_dispatch_scada_crawl() -> None:
    """dispatch_scada for NEM crawl"""
    nem_dispatch_scada_crawl()


@huey.periodic_task(network_interval_crontab(network=NetworkNEM), priority=50, retries=2, retry_delay=10)
@huey.lock_task("crawler_run_nem_dispatch_is_crawl")
def crawler_run_nem_dispatch_is_crawl() -> None:
    """dispatch_is for NEM crawl"""
    nem_dispatch_is_crawl()


@huey.periodic_task(network_interval_crontab(network=NetworkNEM), priority=50, retries=2, retry_delay=10)
@huey.lock_task("crawler_run_nem_trading_is_crawl")
def crawler_run_nem_trading_is_crawl() -> None:
    """dispatch_is for NEM crawl"""
    nem_trading_is_crawl()


@huey.periodic_task(
    network_interval_crontab(network=NetworkAEMORooftop, number_minutes=1), priority=50, retries=2, retry_delay=15
)
@huey.lock_task("crawler_run_nem_rooftop_per_interval")
def crawler_run_nem_rooftop_per_interval() -> None:
    nem_rooftop_crawl()


@huey.periodic_task(crontab(hour="*/1"), priority=50, retries=5, retry_delay=15)
@huey.lock_task("crawler_run_wem_per_interval")
def crawler_run_wem_per_interval() -> None:
    wem_per_interval_check()


@huey.periodic_task(crontab(minute="*/10"), priority=1)
@huey.lock_task("crawler_run_bom_capitals")
def crawler_run_bom_capitals() -> None:
    run_crawl(BOMCapitals)


# Checks for the overnights from aemo and then runs the daily runner
@huey.periodic_task(crontab(hour="4", minute="20"))
@huey.lock_task("nem_overnight_check_always")
def nem_overnight_check_always() -> None:
    nem_per_day_check(always_run=True)


@huey.periodic_task(crontab(hour="8", minute="20"), retries=10, retry_delay=60, priority=50)
@huey.lock_task("nem_overnight_check")
def nem_overnight_check() -> None:
    nem_per_day_check()


@huey.periodic_task(crontab(hour="10", minute="20"), retries=10, retry_delay=60, priority=50)
@huey.lock_task("daily_catchup_runner_worker")
def daily_catchup_runner_worker() -> None:
    daily_catchup_runner()


# export tasks
@huey.periodic_task(crontab(minute="*/15"), priority=90)
@huey.lock_task("schedule_custom_tasks")
def schedule_custom_tasks() -> None:
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
    asyncio.run(export_facility_geojson())


# worker tasks
@huey.periodic_task(crontab(hour="20", minute="45"))
@huey.lock_task("schedule_facility_first_seen_check")
@run_async_task_reusable
async def schedule_facility_first_seen_check() -> None:
    """Check for new DUIDS"""
    await facility_first_seen_check()


@huey.periodic_task(crontab(hour="*/1", minute="15"))
@huey.lock_task("run_run_network_data_range_update")
@run_async_task_reusable
async def run_run_network_data_range_update() -> None:
    """Updates network data_range"""
    run_network_data_range_update()
    await update_facility_seen_range()


# system tasks
@huey.periodic_task(crontab(hour="*/1", minute="55"))
@huey.lock_task("run_clean_tmp_dir")
def run_clean_tmp_dir() -> None:
    clean_tmp_dir()


@huey.periodic_task(crontab(hour="22", minute="55"))
@huey.lock_task("run_cleanup_database_task_profiles_basedon_retention")
def run_cleanup_database_task_profiles_basedon_retention() -> None:
    cleanup_database_task_profiles_basedon_retention()
