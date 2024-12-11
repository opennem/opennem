"""Crawl commands CLI

This module provides CLI commands for managing OpenNEM crawlers using Typer.
"""

import asyncio
import logging
from functools import wraps

import typer
from rich.table import Table

from opennem import console
from opennem.core.crawlers.crawler import crawlers_flush_metadata, crawlers_get_crawl_metadata
from opennem.crawl import get_crawl_set, run_crawl
from opennem.utils.timesince import timesince

logger = logging.getLogger("opennem.cli")

crawl_app = typer.Typer(help="Crawler management commands")


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@crawl_app.command("run")
@coro
async def crawl_run(
    name: str = typer.Argument(..., help="Crawler name pattern to match"),
    all: bool = typer.Option(False, help="Run all crawlers"),
    limit: int | None = typer.Option(None, help="Limit to N most recent records"),
    reverse: bool = typer.Option(False, help="Reverse the order of the crawlers"),
) -> None:
    """Run crawlers matching the given pattern."""
    console.log(f"Run crawlers matching: {name}")

    try:
        crawlers = await get_crawl_set()
        crawlers_filtered = crawlers.get_crawlers_by_match(name, only_active=False)
    except Exception as e:
        console.log(f"[red]Could not find crawlers for {name}[/red]: {e}")
        raise typer.Exit(1) from e

    if not crawlers_filtered:
        console.log(f"No crawlers found matching [red]{name}[/red]")
        raise typer.Exit(1)

    console.log(f"[green]Running {len(crawlers_filtered)} crawlers[/green]")

    for c in crawlers_filtered:
        console.log(
            f"Running crawler {c.name} (Version: {c.version})\n"
            f"\tlast_crawled: {c.last_crawled}\n"
            f"\tlast_processed: {c.last_processed}\n"
            f"\tserver_latest: {c.server_latest}"
        )
        try:
            await run_crawl(c, latest=not all, limit=limit, reverse=reverse)
        except Exception as e:
            console.log(f"[red]Error running crawler[/red]: {e}")
            raise typer.Exit(1) from e


@crawl_app.command("flush")
def crawl_flush(
    days: int | None = typer.Option(None, help="Only flush days"),
    crawler: str | None = typer.Option(None, help="Crawler name to flush"),
) -> None:
    """Flush crawler metadata."""
    console.log("[blue]Flushing crawlers[/blue]")
    try:
        crawlers_flush_metadata(days=days, crawler_name=crawler)
        console.log("[green]Successfully flushed crawler metadata[/green]")
    except Exception as e:
        console.log(f"[red]Error flushing crawler metadata[/red]: {e}")
        raise typer.Exit(1) from e


@crawl_app.command("list")
def crawl_list() -> None:
    """List all available crawlers and their status."""
    console.log("[blue]Listing crawlers[/blue]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Crawler")
    table.add_column("Version")
    table.add_column("Last Crawled")
    table.add_column("Last Processed")
    table.add_column("Server Latest")

    try:
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
    except Exception as e:
        console.log(f"[red]Error listing crawlers[/red]: {e}")
        raise typer.Exit(1) from e
