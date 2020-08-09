import click
from scrapy.utils.python import garbage_collect

from opennem.diff.facility_diff import run_diff
from opennem.utils import logging

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


main.add_command(crawl)
main.add_command(diff)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)
    finally:
        garbage_collect()
