"""Crawl commands cli"""

import logging

import asyncclick as click
from rich.table import Table

from opennem import console
from opennem.core.crawlers.crawler import crawlers_flush_metadata, crawlers_get_crawl_metadata
from opennem.crawl import get_crawl_set, run_crawl
from opennem.utils.timesince import timesince

logger = logging.getLogger("opennem.cli")


@click.group()
def cmd_crawl_cli() -> None:
    pass


@click.command()
@click.argument("name")
@click.option("--all", default=False, is_flag=True, help="Run all")
@click.option("--limit", default=None, type=int, help="Limit to N most recent records")
async def crawl_cli_run(name: str, all: bool = False, limit: int | None = None) -> None:
    console.log(f"Run crawlers matching: {name}")

    crawlers = await get_crawl_set()

    try:
        crawlers_filtered = crawlers.get_crawlers_by_match(name, only_active=False)
    except Exception as e:
        console.log(f"[red]Could not find crawlers for {name}[/red]: {e}")
        return None

    if not crawlers_filtered:
        console.log(f"No crawlers found matchin [red]{name}[/red]")
        return None

    console.log(f"[green]Running {len(crawlers_filtered)} crawlers[/green]")

    for c in crawlers_filtered:
        console.log(
            f"Running crawler {c.name} (Version: {c.version})\n\tlast_crawled: {c.last_crawled}\n\tlast_processed: "
            f"{c.last_processed}\n\tserver_latest: {c.server_latest}"
        )
        try:
            await run_crawl(c, latest=not all, limit=limit)
        except Exception as e:
            console.log(f"[red]Error running crawler[/red]: {e}")


@click.command()
@click.option("--days", default=None, help="Only flush days")
@click.option("--crawler", default=None, help="Crawler name to flush")
def crawl_cli_flush(days: int | None = None, crawler: str | None = None) -> None:
    console.log("[blue]Flushing crawlers[/blue]")
    crawlers_flush_metadata(days=days, crawler_name=crawler)


@click.command()
def crawl_cli_list() -> None:
    console.log("[blue]Listing crawlers[/blue]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Crawler")
    table.add_column("Version")
    table.add_column("Last Crawled")
    table.add_column("Last Processed")
    table.add_column("Server Latest")

    # crawler_meta = anyio.run(func=crawlers_get_crawl_metadata)
    crawler_meta = crawlers_get_crawl_metadata()

    for c in crawler_meta:
        table.add_row(
            c.name,
            str(c.version),
            f"{c.last_crawled} ({timesince(c.last_crawled)})",
            f"{c.last_processed} ({timesince(c.last_processed)})",
            f"{c.server_latest} ({timesince(c.server_latest)})",
        )

    console.print(table)


cmd_crawl_cli.add_command(crawl_cli_run, name="run")
cmd_crawl_cli.add_command(crawl_cli_list, name="list")
cmd_crawl_cli.add_command(crawl_cli_flush, name="flush")
