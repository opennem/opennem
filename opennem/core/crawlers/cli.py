""" Crawl commands cli """
import logging

import click

from opennem.core.crawlers.crawler import crawlers_get_crawl_metadata

logger = logging.getLogger("opennem.cli")


@click.group()
def cmd_crawl_cli() -> None:
    pass


@click.command()
def crawl_cli_run() -> None:
    logger.info("run crawl")


@click.command()
def crawl_cli_list() -> None:
    logger.info("Listing crawlers")

    crawler_meta = crawlers_get_crawl_metadata()

    for c in crawler_meta:
        print("{} {} {}".format(c.name, c.last_processed, c.last_crawled))


cmd_crawl_cli.add_command(crawl_cli_run, name="run")
cmd_crawl_cli.add_command(crawl_cli_list, name="list")
