"""OpenNEM CLI interface

Run with either the opennem entry point or:

$ python -m opennem.cli

This module provides the command-line interface for OpenNEM using Typer.
It includes commands for database management, data import/export, and various utilities.
"""

import logging
import traceback

import typer
from rich.console import Console

from opennem import settings
from opennem.core.crawlers.cli import crawl_app
from opennem.db.load_fixtures import load_bom_stations_json, load_fixtures, load_fueltechs
from opennem.exporter.inspect import inspect_opennem_json
from opennem.importer.db import import_all_facilities
from opennem.importer.db import init as db_init
from opennem.utils.async_sync import async_to_sync

# Initialize typer apps
app = typer.Typer(help="OpenNEM CLI tool for managing the OpenNEM platform")
db_app = typer.Typer(help="Database management commands")
import_app = typer.Typer(help="Data import commands")
export_app = typer.Typer(help="Data export commands")
task_app = typer.Typer(help="Task management commands")

# Add sub-applications
app.add_typer(db_app, name="db")
app.add_typer(import_app, name="import")
app.add_typer(export_app, name="export")
app.add_typer(task_app, name="task")
app.add_typer(crawl_app, name="crawl")

# Setup logging
logger = logging.getLogger("opennem.cli")
console = Console()


# Database commands
@db_app.command("init")
def db_init_command() -> None:
    """Initialize the database schema and tables."""
    try:
        typer.run(db_init)
        console.print("[green]Database initialized successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise typer.Exit(1) from e


@db_app.command("fixtures")
def db_fixtures_command() -> None:
    """Load initial data fixtures into the database."""
    try:
        typer.run(load_fixtures)
        console.print("[green]Fixtures loaded successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to load fixtures: {e}")
        raise typer.Exit(1) from e


# Import commands
@import_app.command("facilities")
def import_facilities_command() -> None:
    """Import all facility data into the database."""
    try:
        typer.run(import_all_facilities)
        console.print("[green]Facilities imported successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to import facilities: {e}")
        raise typer.Exit(1) from e


@import_app.command("fueltechs")
def import_fueltechs_command() -> None:
    """Import fuel technology data."""
    try:
        typer.run(load_fueltechs)
        console.print("[green]Fuel technologies imported successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to import fuel technologies: {e}")
        raise typer.Exit(1) from e


@import_app.command("bom")
def import_bom_stations_command() -> None:
    """Import BOM weather station data."""
    try:
        typer.run(load_bom_stations_json)
        console.print("[green]BOM stations imported successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to import BOM stations: {e}")
        raise typer.Exit(1) from e


@import_app.command("rooftop-capacity-history")
@async_to_sync
async def import_rooftop_capacity_history_command() -> None:
    """Import historical rooftop capacity data from APVI into unit_history table."""
    try:
        from opennem.workers.rooftop_capacity_history import import_rooftop_capacity_history

        await import_rooftop_capacity_history()
        console.print("[green]Rooftop capacity history imported successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to import rooftop capacity history: {e}")
        raise typer.Exit(1) from e


@db_app.command("check-rooftop-units")
@async_to_sync
async def check_rooftop_units_command() -> None:
    """Check which rooftop units exist in the database."""
    try:
        from opennem.workers.rooftop_capacity_history import check_rooftop_units

        await check_rooftop_units()
    except Exception as e:
        logger.error(f"Failed to check rooftop units: {e}")
        raise typer.Exit(1) from e


@db_app.command("view-capacity-history")
@async_to_sync
async def view_capacity_history_command() -> None:
    """View summary of imported capacity history data."""
    try:
        from opennem.workers.rooftop_capacity_history import view_capacity_history_summary

        await view_capacity_history_summary()
    except Exception as e:
        logger.error(f"Failed to view capacity history: {e}")
        raise typer.Exit(1) from e


@db_app.command("clean-capacity-history")
@async_to_sync
async def clean_capacity_history_command() -> None:
    """Clean up incorrect high capacity values from unit_history table."""
    try:
        from opennem.workers.rooftop_capacity_history import clean_incorrect_capacity_values

        await clean_incorrect_capacity_values()
        console.print("[green]Capacity history cleaned successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to clean capacity history: {e}")
        raise typer.Exit(1) from e


# Inspect command
@app.command("inspect")
@async_to_sync
async def inspect_command(url: str) -> None:
    """
    Inspect OpenNEM JSON data from a given URL.

    Args:
        url: The URL of the OpenNEM JSON data to inspect
    """
    try:
        await inspect_opennem_json(url)
    except Exception as e:
        logger.error(f"Failed to inspect JSON: {e}")
        raise typer.Exit(1) from e


# Add the crawl command from core.crawlers.cli
# app.command(name="crawl")(cmd_crawl_cli)


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        logger.error("User interrupted")
        raise typer.Exit(130) from None
    except Exception as e:
        logger.error(str(e))
        if settings.debug:
            traceback.print_exc()
        raise typer.Exit(1) from e


if __name__ == "__main__":
    main()
