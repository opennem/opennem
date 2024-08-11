# type: ignore
"""
OpenNEM Bulk Insert Pipeline

Bulk inserts records using temporary tables and CSV imports with copy_from

"""

import csv
import logging
from datetime import datetime
from io import StringIO
from typing import Any, TypeVar

import asyncpg
from asyncpg.pool import Pool
from sqlalchemy.sql.schema import Column, Table

from opennem import settings
from opennem.db.models.opennem import BalancingSummary, FacilityScada

logger = logging.getLogger("opennem.db.bulk_insert_csv")

ORMTableType = TypeVar("ORMTableType", bound=Table)

# At the module level, create a connection pool
pool: Pool | None = None

_BULK_INSERT_QUERY = """
    CREATE TEMP TABLE __tmp_{table_name}_{tmp_table_name}
    (LIKE {table_schema}{table_name} INCLUDING DEFAULTS)
    ON COMMIT DROP;

    COPY __tmp_{table_name}_{tmp_table_name}
        FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');

    INSERT INTO {table_schema}{table_name}
        SELECT *
        FROM __tmp_{table_name}_{tmp_table_name}
    ON CONFLICT {on_conflict}
"""

_BULK_INSERT_CONFLICT_UPDATE = """
    ({pk_columns}) DO UPDATE set {update_values}
"""


def build_insert_query(
    table: Table,
    update_cols: list[str | Column] = None,
) -> tuple[str, list[str]]:
    """
    Builds the bulk insert query
    """
    on_conflict = "DO NOTHING"

    def get_column_name(column: str | Column) -> str:
        if isinstance(column, Column) and hasattr(column, "name"):
            return column.name
        if isinstance(column, str):
            return column.strip()
        return ""

    update_col_names = []

    if update_cols:
        update_col_names = [get_column_name(c) for c in update_cols]

    update_col_names = list(filter(lambda c: c, update_col_names))

    primary_key_columns = [c.name for c in table.__table__.primary_key.columns.values()]  # type: ignore

    if len(update_col_names):
        on_conflict = _BULK_INSERT_CONFLICT_UPDATE.format(
            pk_columns=",".join(primary_key_columns),
            update_values=", ".join([f"{n} = EXCLUDED.{n}" for n in update_col_names]),
        )

    # Table schema
    table_schema: str = ""
    _ts: str = ""

    if hasattr(table, "__table_args__"):
        if isinstance(table.__table_args__, dict) and "schema" in table.__table_args__:  # type: ignore
            _ts = table.__table_args__["schema"]  # type: ignore

        # for table args that are a list of args find the schema def
        if isinstance(table.__table_args__, tuple):  # type: ignore
            for i in table.__table_args__:  # type: ignore
                if isinstance(i, dict) and "schema" in i:  # type: ignore
                    _ts = i["schema"]  # type: ignore

        if not _ts:
            logger.warning(f"Table schema not found for table: {table.__table__.name}")  # type: ignore
        else:
            table_schema = f"{_ts}."

    # Temporary table name uniq
    tmp_table_name: str = ""

    tmp_table_name = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")

    if _ts:
        tmp_table_name = f"{_ts}_{tmp_table_name}"

    query = _BULK_INSERT_QUERY.format(
        table_name=table.__table__.name,  # type: ignore
        table_schema=table_schema,
        on_conflict=on_conflict,
        tmp_table_name=tmp_table_name,
    )

    return f"__tmp_{table.__table__.name}_{tmp_table_name}", query.split(";")


def _generate_bulkinsert_csv_from_records(
    table: ORMTableType,
    records: list[dict],
    column_names: list[str] | None = None,
) -> StringIO:
    """
    Take a list of dict records and a table schema and generate a csv
    buffer to be used in bulk_insert

    """
    if len(records) < 1:
        raise Exception("No records")

    csv_buffer = StringIO()

    table_column_names = [c.name for c in table.__table__.columns.values()]  # type: ignore

    # sanity check the records we received to make sure
    # they match the table schema
    if isinstance(records, list):
        first_record = records[0]

        record_field_names = list(first_record.keys())

        for field_name in record_field_names:
            if field_name not in table_column_names:
                raise Exception(
                    "Column name from records not found in table: {}. Have {}".format(field_name, ", ".join(table_column_names))
                )

        for column_name in table_column_names:
            if column_name not in record_field_names:
                raise Exception(f"Missing value for column {column_name}")

        column_names = record_field_names
        # column_names = table_column_names

    # if missing_columns:
    #     for missing_col in missing_columns:
    #         records = pad_column_null(records, missing_col)

    if not column_names:
        column_names = table_column_names

    csvwriter = csv.DictWriter(csv_buffer, fieldnames=column_names)
    csvwriter.writeheader()

    # @TODO put the columns in the correct order ..
    # @NOTE do we need to ?!
    for record in records:
        if not record:
            continue

        try:
            csvwriter.writerow(record)
        except Exception:
            logger.error(f"Error writing row in bulk insert: {record}")

    # rewind it back to the start
    csv_buffer.seek(0)

    return csv_buffer


async def get_pool() -> Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(dsn=settings.db_url.replace("+asyncpg", ""))
    return pool


async def bulkinsert_mms_items(
    table: ORMTableType,
    records: list[dict],
    update_fields: list[str | Column[Any]] | None = None,
) -> int:
    if not records:
        return 0

    tmp_table_name, sql_queries = build_insert_query(table=table, update_cols=update_fields)

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                # Execute CREATE TEMP TABLE
                logger.debug(sql_queries[0])
                await conn.execute(sql_queries[0])

                # Get column names and types from the temporary table
                table_info = await conn.fetch(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = '{tmp_table_name.split(".")[-1]}'
                """)

                # Prepare records
                columns = [col["column_name"] for col in table_info]
                column_types = {col["column_name"]: col["data_type"] for col in table_info}

                records_to_insert = []
                for record in records:
                    record_values = []
                    for col in columns:
                        value = record.get(col)
                        if value is None:
                            record_values.append(None)
                        elif column_types[col] == "timestamp without time zone":
                            # Convert string to datetime object if it's not already
                            record_values.append(value if isinstance(value, datetime) else datetime.fromisoformat(str(value)))
                        elif column_types[col] == "numeric":
                            # Ensure numeric values are passed as float or Decimal
                            record_values.append(float(value) if value is not None else None)
                        elif column_types[col] == "boolean":
                            # Convert string to boolean
                            value = str(value).lower()
                            record_values.append(value in ("true", "t", "yes", "y", "1"))
                        else:
                            record_values.append(str(value))
                    records_to_insert.append(record_values)

                # Use copy_records_to_table to bulk insert the records
                logger.debug("Copy records to table")
                result = await conn.copy_records_to_table(
                    tmp_table_name.split(".")[-1],  # Remove schema if present
                    records=records_to_insert,
                    columns=columns,
                )
                logger.debug(f"Copy result: {result}")

                # Execute the INSERT ... ON CONFLICT query
                insert_result = await conn.execute(sql_queries[2])

                num_records = len(records)
                logger.info(f"Bulk inserted {num_records} records: {insert_result}")

                return num_records

            except Exception as generic_error:
                logger.error(f"Error during bulk insert: {generic_error}")
                raise generic_error


def generate_csv_from_records(
    table: Table | FacilityScada | BalancingSummary,
    records: list[dict],
    column_names: list[str] | None = None,
) -> StringIO:
    """
    Take a list of dict records and a table schema and generate a csv
    buffer to be used in bulk_insert

    """
    if len(records) < 1:
        raise Exception("No records")

    csv_buffer = StringIO()

    table_column_names = [c.name for c in table.__table__.columns.values()]  # type: ignore

    # sanity check the records we received to make sure
    # they match the table schema
    if isinstance(records, list):
        first_record = records[0]

        record_field_names = list(first_record.keys())

        for field_name in record_field_names:
            if field_name not in table_column_names:
                raise Exception(
                    "Column name from records not found in table: {}. Have {}".format(field_name, ", ".join(table_column_names))
                )

        for column_name in table_column_names:
            if column_name not in record_field_names:
                raise Exception(f"Missing value for column {column_name}")

        column_names = record_field_names
        # column_names = table_column_names

    # if missing_columns:
    #     for missing_col in missing_columns:
    #         records = pad_column_null(records, missing_col)

    if not column_names:
        column_names = table_column_names

    csvwriter = csv.DictWriter(csv_buffer, fieldnames=column_names)
    csvwriter.writeheader()

    # @TODO put the columns in the correct order ..
    # @NOTE do we need to ?!
    for record in records:
        csvwriter.writerow(record)

    # rewind it back to the start
    csv_buffer.seek(0)

    return csv_buffer
