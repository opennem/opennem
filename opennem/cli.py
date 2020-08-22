import click
from scrapy.utils.python import garbage_collect

from opennem.diff.facility_diff import run_diff
from opennem.importer.opennem import run_opennem_import
from opennem.utils.log_config import logging

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


@click.command()
def cmd_import():
    run_opennem_import()


main.add_command(crawl)
main.add_command(diff)
main.add_command(cmd_import, name="import")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)
    finally:
        garbage_collect()
