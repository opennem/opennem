# from opennem.utils.log_config
import logging
import os

import click
from scrapy.utils.python import garbage_collect

from opennem.diff.facility_diff import run_diff
from opennem.importer.all import run_all
from opennem.importer.mms import mms_export
from opennem.importer.opennem import opennem_export, opennem_import

logger = logging.getLogger("opennem.cli")

DEBUG = bool(os.getenv("DEBUG", default=False))

if DEBUG:
    logger.setLevel(logging.DEBUG)


@click.group()
def main():
    pass


@click.command()
def crawl():
    logger.info("crawl @TODO")


@click.command()
def diff():
    run_diff()


@click.group()
def cmd_import():
    pass


@click.group()
def cmd_export():
    pass


@click.command()
def cmd_import_opennem():
    opennem_import()


@click.command()
def cmd_import_mms():
    mms_export()


@click.command()
def cmd_import_all():
    run_all()


@click.command()
def cmd_export_opennem():
    opennem_export()


@click.command()
def cmd_export_all():
    run_all()


main.add_command(crawl)
main.add_command(diff)
main.add_command(cmd_import, name="import")

cmd_import.add_command(cmd_import_opennem, name="opennem")
cmd_import.add_command(cmd_import_mms, name="mms")
cmd_import.add_command(cmd_import_all, name="all")

cmd_export.add_command(cmd_export_opennem, name="opennem")
cmd_export.add_command(cmd_export_all, name="all")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)

        if DEBUG:
            from pprint import pprint
            import traceback

            traceback.print_exc()

            # pprint(e)
    finally:
        garbage_collect()
