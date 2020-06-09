import logging

import click
from scrapy.utils.python import garbage_collect

logger = logging.getLogger(__name__)


@click.command()
def main():
    click.echo("cli @todo")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupted")
    except Exception as e:
        logger.error(e)
    finally:
        garbage_collect()
