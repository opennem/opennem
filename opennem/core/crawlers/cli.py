""" Crawl commands cli """
import logging

import click

logger = logging.getLogger("opennem.cli")


@click.group()
def cmd_crawl_cli() -> None:
    pass


@click.command()
def crawl_cli_run() -> None:
    logger.info("run crawl")


cmd_crawl_cli.add_command(crawl_cli_run, name="run")
