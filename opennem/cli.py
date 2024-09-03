"""OpenNEM cli interface

run with either the opennem entry point or:

$ python -m opennem.cli
"""

import asyncio
import logging

import asyncclick as click

from opennem import settings
from opennem.core.crawlers.cli import cmd_crawl_cli
from opennem.db.load_fixtures import load_bom_stations_json, load_fixtures, load_fueltechs
from opennem.exporter.historic import export_historic_intervals
from opennem.importer.db import import_all_facilities
from opennem.importer.db import init as db_init
from opennem.parsers.aemo.cli import cmd_data_cli

logger = logging.getLogger("opennem.cli")


@click.group()
def main() -> None:
    pass


@click.group()
def cmd_db() -> None:
    pass


@click.command()
def cmd_db_init() -> None:
    asyncio.run(db_init())


@click.command()
def cmd_db_fixtures() -> None:
    asyncio.run(load_fixtures())
    logger.info("Fixtures loaded")


@click.group()
def cmd_import() -> None:
    pass


@click.group()
def cmd_export() -> None:
    pass


@click.command()
def cmd_import_facilities() -> None:
    asyncio.run(import_all_facilities())


@click.command()
def cmd_import_fueltechs() -> None:
    asyncio.run(load_fueltechs())


@click.command()
def cmd_import_bom_stations() -> None:
    asyncio.run(load_bom_stations_json())


@click.command()
def cmd_weather_init() -> None:
    asyncio.run(load_bom_stations_json())


# Tasks


@click.group()
def cmd_task() -> None:
    pass


@click.command()
@click.option("--weeks", required=False, type=int, default=None)
def cmd_task_historic(weeks: int | None) -> None:
    """
    Runs the historic exports for number of weeks

    Args:
        weeks (int | None): number of weeks to run
    """
    export_historic_intervals(limit=weeks)


main.add_command(cmd_data_cli, name="data")
main.add_command(cmd_crawl_cli, name="crawl")
main.add_command(cmd_db, name="db")
main.add_command(cmd_import, name="import")
main.add_command(cmd_export, name="export")
main.add_command(cmd_task, name="task")

cmd_import.add_command(cmd_import_facilities, name="facilities")
cmd_import.add_command(cmd_import_fueltechs, name="fueltechs")
cmd_import.add_command(cmd_import_bom_stations, name="bom")


cmd_db.add_command(cmd_db_init, name="init")
cmd_db.add_command(cmd_db_fixtures, name="fixtures")


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
