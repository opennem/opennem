""" OpenNEM cli interface

run with either the opennem entry point or:

$ python -m opennem.cli
"""
import logging
from typing import Optional

import click

from opennem.api.export.map import PriorityType
from opennem.api.export.tasks import export_all_monthly, export_energy, export_power
from opennem.core.crawlers.cli import cmd_crawl_cli
from opennem.db.load_fixtures import load_bom_stations_json, load_fixtures
from opennem.db.tasks import refresh_views
from opennem.db.views import init_aggregation_policies
from opennem.db.views.init import init_views_cli
from opennem.exporter.geojson import export_facility_geojson
from opennem.exporter.historic import export_historic_intervals
from opennem.importer.all import run_all
from opennem.importer.db import import_all_facilities
from opennem.importer.db import init as db_init
from opennem.importer.mms import mms_export
from opennem.importer.opennem import opennem_import
from opennem.settings import settings
from opennem.workers.aggregates import run_aggregate_days
from opennem.workers.daily import all_runner, daily_runner
from opennem.workers.energy import run_energy_update_archive, run_energy_update_days

logger = logging.getLogger("opennem.cli")


@click.group()
def main() -> None:
    pass


@click.group()
def cmd_db() -> None:
    pass


@click.command()
def cmd_db_init() -> None:
    db_init()


@click.command()
def cmd_db_fixtures() -> None:
    load_fixtures()
    logger.info("Fixtures loaded")


@click.command()
def cmd_db_refresh() -> None:
    refresh_views()


@click.command()
@click.option("--purge", is_flag=True, help="Purge unmapped views")
def cmd_db_views(purge: bool) -> None:
    init_views_cli(purge=purge)


@click.command()
def cmd_db_aggregations() -> None:
    init_aggregation_policies()


@click.group()
def cmd_import() -> None:
    pass


@click.group()
def cmd_export() -> None:
    pass


@click.command()
def cmd_import_opennem() -> None:
    opennem_import()


@click.command()
def cmd_import_facilities() -> None:
    import_all_facilities()
    export_facility_geojson()


@click.command()
def cmd_import_bom_stations() -> None:
    load_bom_stations_json()


@click.command()
def cmd_import_mms() -> None:
    mms_export()


@click.command()
def cmd_import_all() -> None:
    run_all()


@click.command()
def cmd_export_power() -> None:
    export_power(priority=PriorityType.live)


@click.command()
def cmd_export_energy() -> None:
    export_energy()


@click.command()
def cmd_export_energy_monthly() -> None:
    export_all_monthly()


@click.command()
def cmd_export_all() -> None:
    run_energy_update_days(days=5)
    run_aggregate_days(days=5)
    export_energy(latest=True)
    export_energy(priority=PriorityType.monthly)


@click.group()
def cmd_weather() -> None:
    pass


@click.command()
def cmd_weather_init() -> None:
    load_bom_stations_json()


# Tasks


@click.group()
def cmd_task() -> None:
    pass


@click.command()
@click.option("--year", required=True, type=int)
@click.option("--fueltech", required=False, type=str)
def cmd_task_energy(year: int, fueltech: Optional[str] = None) -> None:
    run_energy_update_archive(year, fueltech=fueltech)


@click.command()
@click.option("--days", required=False, type=int, default=2)
def cmd_task_daily(days: int) -> None:
    daily_runner(days=days)


@click.command()
def cmd_task_all() -> None:
    """
    Runs gap fill, daily and aggregate tasks
    """
    all_runner()


@click.command()
@click.option("--weeks", required=False, type=int, default=None)
def cmd_task_historic(weeks: int | None) -> None:
    """
    Runs the historic exports for number of weeks

    Args:
        weeks (int | None): number of weeks to run
    """
    export_historic_intervals(limit=weeks)


main.add_command(cmd_crawl_cli, name="crawl")
main.add_command(cmd_db, name="db")
main.add_command(cmd_import, name="import")
main.add_command(cmd_export, name="export")
main.add_command(cmd_weather, name="weather")
main.add_command(cmd_task, name="task")

cmd_import.add_command(cmd_import_opennem, name="opennem")
cmd_import.add_command(cmd_import_mms, name="mms")
cmd_import.add_command(cmd_import_all, name="all")
cmd_import.add_command(cmd_import_facilities, name="facilities")
cmd_import.add_command(cmd_import_bom_stations, name="bom")

cmd_export.add_command(cmd_export_all, name="all")
cmd_export.add_command(cmd_export_power, name="power")
cmd_export.add_command(cmd_export_energy, name="energy")
cmd_export.add_command(cmd_export_energy_monthly, name="energy_monthly")

cmd_db.add_command(cmd_db_init, name="init")
cmd_db.add_command(cmd_db_fixtures, name="fixtures")
cmd_db.add_command(cmd_db_refresh, name="refresh")
cmd_db.add_command(cmd_db_views, name="views")
cmd_db.add_command(cmd_db_aggregations, name="aggregations")

cmd_weather.add_command(cmd_weather_init, name="init")

cmd_task.add_command(cmd_task_energy, name="energy")
cmd_task.add_command(cmd_task_daily, name="daily")
cmd_task.add_command(cmd_task_all, name="all")
cmd_task.add_command(cmd_task_historic, name="historic")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)

        if settings.debug:
            import traceback

            traceback.print_exc()
