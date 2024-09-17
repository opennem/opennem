"""
Creates a data table from a list of dicts using rich tables
"""

import re
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table


def _format_column_name(name: str) -> str:
    """Convert snake_case or camelCase to Title Case"""
    # Split on underscores or capital letters
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", name)
    return " ".join(word.capitalize() for word in words)


def _format_value(value: Any) -> str:
    """Format value based on its type"""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def datatable_print(data: list[dict[str, Any]]) -> Table:
    """
    Create a rich table from a list of dicts and print it.

    Args:
        data (list[dict[str, Any]]): List of dictionaries containing the data.

    Returns:
        Table: A rich Table object.
    """
    if not data:
        return Table()

    table = Table(show_header=True, header_style="bold magenta")

    # Add column headers
    for key in data[0].keys():
        table.add_column(_format_column_name(key))

    # Add rows
    for row in data:
        table.add_row(*[_format_value(value) for value in row.values()])

    # Print the table
    console = Console()
    console.print(table)

    return table
