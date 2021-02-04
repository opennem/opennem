import logging

import click
from scrapy.utils.python import garbage_collect

from opennem.db.load_fixtures import load_bom_stations_json, load_fixtures
from opennem.db.tasks import refresh_views
from opennem.db.views.init import init_views_cli
from opennem.importer.all import run_all
from opennem.importer.db import import_facilities
from opennem.importer.db import init as db_init
from opennem.importer.emissions import import_emissions_map
from opennem.importer.mms import mms_export
from opennem.importer.opennem import opennem_export, opennem_import
from opennem.settings import settings

logger = logging.getLogger("opennem.cli")


@click.group()
def main() -> None:
    pass


@click.command()
def crawl() -> None:
    logger.info("crawl @TODO")


@click.group()
def cmd_db() -> None:
    pass


@click.command()
def cmd_db_init() -> None:
    db_init()


@click.command()
def cmd_db_fixturer() -> None:
    load_fixtures()


@click.command()
def cmd_db_refresh() -> None:
    refresh_views()


@click.command()
@click.option("--purge", is_flag=True, help="Purge unmapped views")
def cmd_db_views(purge: bool) -> None:
    init_views_cli(purge=purge)


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
    import_facilities()


@click.command()
def cmd_import_mms() -> None:
    mms_export()


@click.command()
def cmd_import_all() -> None:
    run_all()


@click.command()
def cmd_import_emissions() -> None:
    import_emissions_map("emission_factors.csv")


@click.command()
def cmd_export_opennem() -> None:
    opennem_export()


@click.command()
def cmd_export_all() -> None:
    run_all()


@click.group()
def cmd_weather() -> None:
    pass


@click.command()
def cmd_weather_init() -> None:
    load_bom_stations_json()


main.add_command(crawl)
main.add_command(cmd_db, name="db")
main.add_command(cmd_import, name="import")
main.add_command(cmd_export, name="export")
main.add_command(cmd_weather, name="weather")

cmd_import.add_command(cmd_import_opennem, name="opennem")
cmd_import.add_command(cmd_import_mms, name="mms")
cmd_import.add_command(cmd_import_all, name="all")
cmd_import.add_command(cmd_import_emissions, name="emissions")
cmd_import.add_command(cmd_import_facilities, name="facilities")

cmd_export.add_command(cmd_export_opennem, name="opennem")
cmd_export.add_command(cmd_export_all, name="all")

cmd_db.add_command(cmd_db_init, name="init")
cmd_db.add_command(cmd_db_fixturer, name="load_fixtures")
cmd_db.add_command(cmd_db_refresh, name="refresh")
cmd_db.add_command(cmd_db_views, name="views")

cmd_weather.add_command(cmd_weather_init, name="init")

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

    finally:
        garbage_collect()
