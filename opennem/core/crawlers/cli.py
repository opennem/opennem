""" Crawl commands cli """
import logging

import click
from rich.table import Table

from opennem import console
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
    console.log("[blue]Listing crawlers[/blue]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Crawler")
    table.add_column("Last Crawled")
    table.add_column("Last Processed")

    crawler_meta = crawlers_get_crawl_metadata()

    for c in crawler_meta:
        table.add_row(c.name, str(c.last_processed), str(c.last_crawled))

    console.print(table)


cmd_crawl_cli.add_command(crawl_cli_run, name="run")
cmd_crawl_cli.add_command(crawl_cli_list, name="list")
