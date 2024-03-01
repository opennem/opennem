"""Crawl commands cli"""

import logging

import click

from opennem import console

logger = logging.getLogger("opennem.cli")


@click.group()
def cmd_data_cli() -> None:
    pass


@click.command()
@click.argument("name")
def data_run_rel(name: str) -> None:
    console.print(f"Run importer aemo source matching: {name}")


cmd_data_cli.add_command(data_run_rel, name="run")
