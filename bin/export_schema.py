#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "psycopg2",
#     "python-dotenv",
# ]
# ///
"""Export database schema and sample data"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, TextIO

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


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


def get_tables(cursor: psycopg2.extensions.cursor) -> list[str]:
    """
    Get a list of table names in the public schema.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.

    Returns:
        List[str]: List of table names.
    """
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    return [row[0] for row in cursor.fetchall()]


def get_create_table_statement(cursor: psycopg2.extensions.cursor, table: str) -> str | None:
    """
    Get the CREATE TABLE statement for a given table.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        table (str): Name of the table.

    Returns:
        Optional[str]: CREATE TABLE statement if found, None otherwise.
    """
    cursor.execute(f"""
        SELECT
            'CREATE TABLE ' || relname || E'\n(\n' ||
            array_to_string(
                array_agg(
                    '    ' || column_name || ' ' ||  type || ' '|| not_null
                )
                , E',\n'
            ) || E'\n);\n'
        FROM (
            SELECT
                c.relname, a.attname AS column_name,
                pg_catalog.format_type(a.atttypid, a.atttypmod) as type,
                CASE
                    WHEN a.attnotnull THEN 'NOT NULL'
                    ELSE 'NULL'
                END as not_null
            FROM pg_class c,
                pg_attribute a,
                pg_type t
            WHERE c.relname = '{table}'
                AND a.attnum > 0
                AND a.attrelid = c.oid
                AND a.atttypid = t.oid
            ORDER BY a.attnum
        ) AS tabledefinition
        GROUP BY relname;
    """)
    result = cursor.fetchone()
    return result[0] if result else None


def get_constraints(cursor: psycopg2.extensions.cursor, table: str) -> list[tuple[str]]:
    """
    Get a list of constraints for a given table.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        table (str): Name of the table.

    Returns:
        List[Tuple[str]]: List of constraint definitions.
    """
    cursor.execute(f"""
        SELECT pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE conrelid = '{table}'::regclass AND n.nspname = 'public'
    """)
    return cursor.fetchall()


def get_indexes(cursor: psycopg2.extensions.cursor, table: str) -> list[tuple[str]]:
    """
    Get a list of indexes for a given table.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        table (str): Name of the table.

    Returns:
        List[Tuple[str]]: List of index definitions.
    """
    cursor.execute(f"""
        SELECT indexdef
        FROM pg_indexes
        WHERE tablename = '{table}' AND schemaname = 'public'
    """)
    return cursor.fetchall()


def get_sample_data(cursor: psycopg2.extensions.cursor, table: str) -> list[tuple]:
    """
    Get a sample of data from a given table.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        table (str): Name of the table.

    Returns:
        List[Tuple]: List of sample data rows.
    """
    cursor.execute(f"SELECT * FROM {table} ORDER BY RANDOM() LIMIT 5;")
    return cursor.fetchall()


def get_column_names(cursor: psycopg2.extensions.cursor, table: str) -> list[str]:
    """
    Get a list of column names for a given table.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        table (str): Name of the table.

    Returns:
        List[str]: List of column names.
    """
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position;")
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


def get_row_count(cursor: psycopg2.extensions.cursor, table: str) -> int:
    """
    Get the number of rows in a given table.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        table (str): Name of the table.

    Returns:
        int: Number of rows in the table.
    """
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    result = cursor.fetchone()
    return result[0] if result else 0


def get_table_fields(cursor: psycopg2.extensions.cursor, table: str) -> list[tuple[str, str, int | None, str]]:
    """
    Get a list of fields and their properties for a given table.

    Args:
        cursor (psycopg2.extensions.cursor): Database cursor object.
        table (str): Name of the table.

    Returns:
        List[Tuple[str, str, Optional[int], str]]: List of tuples containing field name, data type, max length, and nullability.
    """
    cursor.execute(f"""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table}'
        ORDER BY ordinal_position;
    """)
    return cursor.fetchall()


def export_schema(
    output: TextIO = sys.stdout, connection_string: str | None = None, env_var: str = "DB_URL", env_file: str = ".env"
) -> None:
    """
    Export database schema and sample data to the specified output.

    Args:
        output (TextIO): Output stream to write the schema and data.
        connection_string (Optional[str]): Database connection string.
        env_var (str): Name of the environment variable to use for the connection string.
        env_file (str): Path to the .env file.

    Raises:
        Exception: If an error occurs during the export process.
    """
    try:
        conn = get_database_connection(connection_string, env_var, env_file)
        cursor = conn.cursor()

        db_name, db_version = get_database_info(cursor)
        plugins = get_enabled_plugins(cursor)
        tables = get_tables(cursor)

        output.write("# Database Schema\n\n")
        output.write(f"Database: {db_name}\n")
        output.write(f"PostgreSQL version: {db_version}\n\n")

        output.write("## Enabled PostgreSQL Plugins\n\n")
        output.write("| Plugin Name | Version |\n")
        output.write("|-------------|--------|\n")
        for plugin in plugins:
            output.write(f"| {plugin[0]} | {plugin[1]} |\n")
        output.write("\n")

        for table in tables:
            output.write(f"## Table: {table}\n\n")

            # Add row count
            row_count = get_row_count(cursor, table)
            output.write(f"Total rows: {row_count}\n\n")

            # Add table of fields and their types
            fields = get_table_fields(cursor, table)
            output.write("### Fields\n\n")
            output.write("| Field Name | Data Type | Max Length | Nullable |\n")
            output.write("|------------|-----------|------------|----------|\n")
            for field in fields:
                name, data_type, max_length, nullable = field
                max_length = str(max_length) if max_length is not None else "N/A"
                nullable = "Yes" if nullable == "YES" else "No"
                output.write(f"| {name} | {data_type} | {max_length} | {nullable} |\n")
            output.write("\n")

            create_table = get_create_table_statement(cursor, table)
            if create_table:
                output.write("### Create Table Statement\n\n")
                output.write("```sql\n")
                output.write(create_table)
                output.write("\n```\n\n")
            else:
                output.write(f"No CREATE TABLE statement found for {table}\n\n")

            constraints = get_constraints(cursor, table)
            if constraints:
                output.write("### Constraints\n\n")
                for constraint in constraints:
                    output.write(f"- {constraint[0]}\n")
                output.write("\n")

            indexes = get_indexes(cursor, table)
            if indexes:
                output.write("### Indexes\n\n")
                for index in indexes:
                    output.write(f"- {index[0]}\n")
                output.write("\n")

            sample_data = get_sample_data(cursor, table)
            if sample_data:
                output.write("### Sample Data\n\n")
                output.write("```\n")
                columns = get_column_names(cursor, table)
                output.write(" | ".join(columns) + "\n")
                output.write("-" * (len(columns) * 15) + "\n")
                for row in sample_data:
                    output.write(" | ".join(trim_field(cell) for cell in row) + "\n")
                output.write("```\n\n")

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
    args = parser.parse_args()

    try:
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with output_file.open("w") as f:
                export_schema(f, args.database, args.env_var, args.env_file)
            print(f"Schema and sample data exported to {output_file}")
        else:
            export_schema(connection_string=args.database, env_var=args.env_var, env_file=args.env_file)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
