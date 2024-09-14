#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "psycopg2",
#     "python-dotenv",
# ]
# ///
"""Export database schema and sample data into markdown documentation

Run with:

$ uv run export_schema.py

Command line args and options:

-d, --database: Database connection string
-o, --output: Output file path
-e, --env-var: Environment variable name for database URL
--env-file: Path to the .env file
--skip-sample-data: Comma-separated list of tables to skip sample data for

"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, TextIO

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add this near the top of the file, after the imports

_SYSTEM_TABLES = {
    # PostGIS tables
    "geography_columns",
    "geometry_columns",
    "spatial_ref_sys",
    "raster_columns",
    "raster_overviews",
    # PostgreSQL system tables
    "pg_stat_statements",
    "pg_stat_statements_info",
    # pgcrypto extension
    "pgp_armor_headers",
    # Other common extension tables
    "hstore_old_ext",
    "sql_features",
    "sql_implementation_info",
    "sql_languages",
    "sql_packages",
    "sql_parts",
    "sql_sizing",
    "sql_sizing_profiles",
    # Add any other system tables or extension tables you want to exclude
}


def get_database_connection(
    connection_string: str | None = None, env_var: str = "DB_URL", env_file: str = ".env"
) -> psycopg2.extensions.connection:
    """
    Establish a database connection using the provided connection string or environment variable.

    Args:
        connection_string (Optional[str]): Database connection string.
        env_var (str): Name of the environment variable to use for the connection string.
        env_file (str): Path to the .env file.

    Returns:
        psycopg2.extensions.connection: Database connection object.

    Raises:
        ValueError: If the connection string is not provided and cannot be found in environment variables.
        ConnectionError: If the connection to the database fails.
    """
    if not connection_string:
        load_dotenv(dotenv_path=env_file)
        connection_string = os.getenv(env_var)

    if not connection_string:
        raise ValueError(f"Database connection string not provided and {env_var} environment variable not set")

    connection_string = connection_string.strip().replace("+asyncpg", "")

    if connection_string.startswith("postgres://"):
        print("Replacing postgres with postgresql in connection string schema")
        connection_string = connection_string.replace("postgres://", "postgresql://")

    if not connection_string.startswith("postgresql://"):
        raise ValueError("Invalid connection string. Must be a PostgreSQL connection string.")

    try:
        conn = psycopg2.connect(connection_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(f"Failed to connect to the database: {e}") from e


def get_database_info(cursor: psycopg2.extensions.cursor) -> tuple[str, str]:
    """
    Get the name and version of the current database.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.

    Returns:
        Tuple[str, str]: Database name and version.
    """
    cursor.execute("SELECT current_database(), version();")
    db_info = cursor.fetchone()
    return db_info if db_info else ("Unknown", "Unknown")


def get_enabled_plugins(cursor: psycopg2.extensions.cursor) -> list[tuple[str, str]]:
    """
    Get a list of enabled PostgreSQL plugins and their versions.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.

    Returns:
        List[Tuple[str, str]]: List of tuples containing plugin name and version.
    """
    cursor.execute("""
        SELECT name, installed_version
        FROM pg_available_extensions
        WHERE installed_version IS NOT NULL
        ORDER BY name;
    """)
    return cursor.fetchall()


def get_tables(cursor: psycopg2.extensions.cursor, schemas: list[str]) -> list[tuple[str, str]]:
    """
    Get a list of table names in the specified schemas, excluding system tables.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schemas (List[str]): List of schema names to query.

    Returns:
        List[Tuple[str, str]]: List of tuples containing schema name and table name.
    """
    placeholders = ",".join(["%s"] * len(schemas))
    cursor.execute(
        f"""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ({placeholders})
        AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name;
    """,
        schemas,
    )
    tables = cursor.fetchall()
    return [(schema, table) for schema, table in tables if table.lower() not in _SYSTEM_TABLES]


def get_create_table_statement(cursor: psycopg2.extensions.cursor, schema: str, table: str) -> str | None:
    """
    Get the CREATE TABLE statement for a given table in a specific schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schema (str): Name of the schema.
        table (str): Name of the table.

    Returns:
        Optional[str]: CREATE TABLE statement if found, None otherwise.
    """
    query = """
        SELECT
            'CREATE TABLE ' || quote_ident(t.table_schema) || '.' || quote_ident(t.table_name) || E'\n(\n' ||
            string_agg(
                '    ' || quote_ident(c.column_name) || ' ' || c.data_type ||
                CASE WHEN c.character_maximum_length IS NOT NULL
                     THEN '(' || c.character_maximum_length || ')'
                     ELSE ''
                END ||
                CASE WHEN c.is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END,
                E',\n'
                ORDER BY c.ordinal_position
            ) || E'\n);\n'
        FROM information_schema.tables t
        JOIN information_schema.columns c ON c.table_schema = t.table_schema AND c.table_name = t.table_name
        WHERE t.table_schema = %s AND t.table_name = %s
        GROUP BY t.table_schema, t.table_name;
    """
    cursor.execute(query, (schema, table))
    result = cursor.fetchone()
    return result[0] if result else None


def get_constraints(cursor: psycopg2.extensions.cursor, schema: str, table: str) -> list[tuple[str]]:
    """
    Get a list of constraints for a given table in a specific schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schema (str): Name of the schema.
        table (str): Name of the table.

    Returns:
        List[Tuple[str]]: List of constraint definitions.
    """
    query = """
        SELECT pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = %s AND n.nspname = %s
    """
    cursor.execute(query, (table, schema))
    return cursor.fetchall()


def get_indexes(cursor: psycopg2.extensions.cursor, schema: str, table: str) -> list[tuple[str]]:
    """
    Get a list of indexes for a given table in a specific schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schema (str): Name of the schema.
        table (str): Name of the table.

    Returns:
        List[Tuple[str]]: List of index definitions.
    """
    query = """
        SELECT indexdef
        FROM pg_indexes
        WHERE tablename = %s AND schemaname = %s
    """
    cursor.execute(query, (table, schema))
    return cursor.fetchall()


def get_sample_data(cursor: psycopg2.extensions.cursor, schema: str, table: str) -> list[tuple]:
    """
    Get a sample of data from a given table in a specific schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schema (str): Name of the schema.
        table (str): Name of the table.

    Returns:
        List[Tuple]: List of sample data rows.
    """
    query = (
        f"SELECT * FROM {psycopg2.extensions.quote_ident(schema, cursor)}."
        f"{psycopg2.extensions.quote_ident(table, cursor)}"
        " ORDER BY RANDOM() LIMIT 5"
    )
    cursor.execute(query)
    return cursor.fetchall()


def get_column_names(cursor: psycopg2.extensions.cursor, schema: str, table: str) -> list[str]:
    """
    Get a list of column names for a given table in a specific schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schema (str): Name of the schema.
        table (str): Name of the table.

    Returns:
        List[str]: List of column names.
    """
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """
    cursor.execute(query, (schema, table))
    return [col[0] for col in cursor.fetchall()]


def trim_field(value: Any, max_length: int = 200) -> str:
    """
    Trim a field value to a maximum length and append an ellipsis if truncated.

    Args:
        value (Any): Field value.
        max_length (int): Maximum length of the field value.

    Returns:
        str: Trimmed field value.
    """
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length] + "..."
    return str_value


def get_row_count(cursor: psycopg2.extensions.cursor, schema: str, table: str) -> int:
    """
    Get the number of rows in a given table in a specific schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schema (str): Name of the schema.
        table (str): Name of the table.

    Returns:
        int: Number of rows in the table.
    """
    cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table};")
    result = cursor.fetchone()
    return result[0] if result else 0


def get_table_fields(cursor: psycopg2.extensions.cursor, schema: str, table: str) -> list[tuple[str, str, int | None, str]]:
    """
    Get a list of fields and their properties for a given table in a specific schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        schema (str): Name of the schema.
        table (str): Name of the table.

    Returns:
        List[Tuple[str, str, Optional[int], str]]: List of tuples containing field name, data type, max length, and nullability.
    """
    cursor.execute(f"""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_schema = '{schema}' AND table_name = '{table}'
        ORDER BY ordinal_position;
    """)
    return cursor.fetchall()


def escape_markdown(text: str) -> str:
    """
    Escape special characters in markdown.

    Args:
        text (str): The text to escape.

    Returns:
        str: The escaped text.
    """
    # Escape characters that have special meaning in markdown
    escape_chars = r"([|\\`*_{}\[\]()#+\-.!])"
    return re.sub(escape_chars, r"\\\1", str(text))


def export_schema(
    output: TextIO = sys.stdout,
    connection_string: str | None = None,
    env_var: str = "DB_URL",
    env_file: str = ".env",
    schemas: list[str] | None = None,
    skip_sample_data_tables: list[str] | None = None,
) -> None:
    """
    Export database schema and sample data to the specified output.

    Args:
        output (TextIO): Output stream to write the schema and data.
        connection_string (Optional[str]): Database connection string.
        env_var (str): Name of the environment variable to use for the connection string.
        env_file (str): Path to the .env file.
        schemas (List[str]): List of schemas to export.
        skip_sample_data_tables (List[str]): List of tables to skip sample data for.

    Raises:
        Exception: If an error occurs during the export process.
    """
    if schemas is None:
        schemas = ["public"]
    if skip_sample_data_tables is None:
        skip_sample_data_tables = []

    try:
        conn = get_database_connection(connection_string, env_var, env_file)
        cursor = conn.cursor()

        db_name, db_version = get_database_info(cursor)
        plugins = get_enabled_plugins(cursor)
        tables = get_tables(cursor, schemas)

        output.write("# Database Schema\n\n")
        output.write(f"Database: {db_name}\n")
        output.write(f"PostgreSQL version: {db_version}\n")
        output.write(f"Schemas: {', '.join(schemas)}\n\n")

        # Add table of contents
        output.write("## Table of Contents\n\n")
        output.write("| Schema | Table Name | Row Count |\n")
        output.write("|--------|------------|----------|\n")
        for schema, table in tables:
            row_count = get_row_count(cursor, schema, table)
            formatted_row_count = f"{row_count:,}"
            output.write(
                f"| {schema} | [{table}](#{schema.lower()}-{table.lower().replace('_', '-')}) | {formatted_row_count} |\n"
            )
        output.write("\n")

        output.write("## Enabled PostgreSQL Plugins\n\n")
        output.write("| Plugin Name | Version |\n")
        output.write("|-------------|--------|\n")
        for plugin in plugins:
            output.write(f"| {escape_markdown(plugin[0])} | {escape_markdown(plugin[1])} |\n")
        output.write("\n")

        for schema, table in tables:
            output.write(f"## Table: {schema}.{table}\n\n")

            # Add row count with comma-separated formatting
            row_count = get_row_count(cursor, schema, table)
            formatted_row_count = f"{row_count:,}"
            output.write(f"Total rows: {formatted_row_count}\n\n")

            # Add table of fields and their types
            fields = get_table_fields(cursor, schema, table)
            output.write("### Fields\n\n")
            output.write("| Field Name | Data Type | Max Length | Nullable |\n")
            output.write("|------------|-----------|------------|----------|\n")
            for field in fields:
                name, data_type, max_length, nullable = field
                max_length = str(max_length) if max_length is not None else "N/A"
                nullable = "Yes" if nullable == "YES" else "No"
                output.write(f"| {name} | {data_type} | {max_length} | {nullable} |\n")
            output.write("\n")

            create_table = get_create_table_statement(cursor, schema, table)
            if create_table:
                output.write("### Create Table Statement\n\n")
                output.write("```sql\n")
                output.write(create_table)
                output.write("\n```\n\n")
            else:
                output.write(f"No CREATE TABLE statement found for {schema}.{table}\n\n")

            constraints = get_constraints(cursor, schema, table)
            if constraints:
                output.write("### Constraints\n\n")
                for constraint in constraints:
                    output.write(f"- {constraint[0]}\n")
                output.write("\n")

            indexes = get_indexes(cursor, schema, table)
            if indexes:
                output.write("### Indexes\n\n")
                for index in indexes:
                    output.write(f"- {index[0]}\n")
                output.write("\n")

            sample_data = get_sample_data(cursor, schema, table)
            if sample_data and f"{schema}.{table}" not in skip_sample_data_tables:
                output.write("### Sample Data\n\n")
                columns = get_column_names(cursor, schema, table)

                # Write the header
                output.write("| " + " | ".join(escape_markdown(col) for col in columns) + " |\n")

                # Write the separator
                output.write("| " + " | ".join(["---"] * len(columns)) + " |\n")

                # Write the data rows
                for row in sample_data:
                    output.write("| " + " | ".join(escape_markdown(trim_field(cell)) for cell in row) + " |\n")
                output.write("\n")

        cursor.close()
        conn.close()
    except Exception as e:
        output.write(f"Error occurred while exporting schema: {str(e)}\n")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export database schema and sample data")
    parser.add_argument("-d", "--database", help="Database connection string")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-e", "--env-var", default="DB_URL", help="Environment variable name for database URL")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file")
    parser.add_argument("-s", "--schemas", default="public", help="Comma-separated list of schemas to export (default: public)")
    parser.add_argument("--skip-sample-data", help="Comma-separated list of tables to skip sample data for", default="")
    args = parser.parse_args()

    try:
        schemas = [s.strip() for s in args.schemas.split(",")]
        skip_sample_data_tables = [t.strip() for t in args.skip_sample_data.split(",") if t.strip()]
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w") as f:
                export_schema(f, args.database, args.env_var, args.env_file, schemas, skip_sample_data_tables)
            print(f"Schema and sample data exported to {output_file}")
        else:
            export_schema(
                connection_string=args.database,
                env_var=args.env_var,
                env_file=args.env_file,
                schemas=schemas,
                skip_sample_data_tables=skip_sample_data_tables,
            )
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
