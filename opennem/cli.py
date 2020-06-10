import logging

import click
from scrapy.utils.python import garbage_collect

logger = logging.getLogger(__name__)


@click.group()
def main():
    click.echo("cli @todo")


@click.command()
def crawl():
    print("crawl")


main.add_command(crawl)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)
    finally:
        garbage_collect()
