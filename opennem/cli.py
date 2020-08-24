# from opennem.utils.log_config
import logging

import click
from scrapy.utils.python import garbage_collect

from opennem.diff.facility_diff import run_diff
from opennem.importer.mms import run_import_mms
from opennem.importer.opennem import run_opennem_import

logger = logging.getLogger("opennem.cli")
logger.setLevel(logging.DEBUG)


@click.group()
def main():
    pass


@click.command()
def crawl():
    logger.info("crawl")


@click.command()
def diff():
    run_diff()


@click.group()
def cmd_import():
    pass


@click.command()
def cmd_import_opennem():
    run_opennem_import()


@click.command()
def cmd_import_mms():
    run_import_mms()


main.add_command(crawl)
main.add_command(diff)
main.add_command(cmd_import, name="import")

cmd_import.add_command(cmd_import_opennem, name="opennem")
cmd_import.add_command(cmd_import_mms, name="mms")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)
    finally:
        garbage_collect()
