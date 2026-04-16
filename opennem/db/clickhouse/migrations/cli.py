"""
CLI commands for ClickHouse migrations.

Registered as `opennem ch` via Typer.
"""

import logging

import typer
from rich.console import Console
from rich.table import Table

logger = logging.getLogger("opennem.db.clickhouse.migrations.cli")
console = Console()

ch_app = typer.Typer(help="ClickHouse migration management")


@ch_app.command("up")
def ch_up(
    to: int | None = typer.Option(None, "--to", help="Apply up to this version number"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show pending without applying"),
) -> None:
    """Apply all pending ClickHouse migrations."""
    from opennem.db.clickhouse.client import get_clickhouse_client
    from opennem.db.clickhouse.migrations import MigrationRunner

    client = get_clickhouse_client()
    runner = MigrationRunner(client)

    if dry_run:
        pending = runner.pending()
        if not pending:
            console.print("[green]No pending migrations[/green]")
            return
        console.print(f"[yellow]{len(pending)} pending migration(s):[/yellow]")
        for m in pending:
            console.print(f"  {m.version:04d} {m.name}: {m.description}")
        return

    try:
        applied = runner.up(target=to)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

    if applied:
        console.print(f"[green]Applied {len(applied)} migration(s): {applied}[/green]")
    else:
        console.print("[green]Already up to date[/green]")


@ch_app.command("down")
def ch_down(
    count: int = typer.Option(1, "--count", "-n", help="Number of migrations to rollback"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Rollback the last N ClickHouse migrations."""
    from opennem.db.clickhouse.client import get_clickhouse_client
    from opennem.db.clickhouse.migrations import MigrationRunner

    client = get_clickhouse_client()
    runner = MigrationRunner(client)

    applied = runner.applied()
    if not applied:
        console.print("[yellow]No migrations to rollback[/yellow]")
        return

    to_rollback = sorted(applied, key=lambda a: a.version, reverse=True)[:count]
    if not yes:
        names = ", ".join(f"{a.version:04d}_{a.name}" for a in to_rollback)
        confirm = typer.confirm(f"Rollback {len(to_rollback)} migration(s): {names}?")
        if not confirm:
            raise typer.Abort()

    try:
        rolled_back = runner.down(count=count)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

    console.print(f"[green]Rolled back {len(rolled_back)} migration(s): {rolled_back}[/green]")


@ch_app.command("status")
def ch_status() -> None:
    """Show migration status."""
    from opennem.db.clickhouse.client import get_clickhouse_client
    from opennem.db.clickhouse.migrations import MigrationRunner

    client = get_clickhouse_client()
    runner = MigrationRunner(client)

    rows = runner.status()
    if not rows:
        console.print("[yellow]No migrations found[/yellow]")
        return

    table = Table(title="ClickHouse Migrations")
    table.add_column("Version", justify="right")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Applied At")

    pending_count = 0
    for row in rows:
        if row["applied"]:
            status = "[green]applied[/green]"
            applied_at = str(row["applied_at"]) if row["applied_at"] else ""
        else:
            status = "[yellow]pending[/yellow]"
            applied_at = ""
            pending_count += 1

        table.add_row(
            f"{row['version']:04d}",
            row["name"],
            status,
            applied_at,
        )

    console.print(table)

    if pending_count:
        console.print(f"\n[yellow]{pending_count} pending — run `opennem ch up` to apply[/yellow]")
        raise typer.Exit(1) from None


@ch_app.command("create")
def ch_create(
    description: str = typer.Argument(..., help="Short description for the migration"),
) -> None:
    """Scaffold a new migration file."""
    from opennem.db.clickhouse.migrations import MigrationRunner

    # Runner doesn't need a real client for scaffolding
    runner = MigrationRunner.__new__(MigrationRunner)
    filepath = runner.create(description)
    console.print(f"[green]Created: {filepath}[/green]")
