import logging
from datetime import datetime
from io import StringIO
from typing import List, Union

# from sqlalchemy.exc import StatementError
from sqlalchemy.sql.schema import Column, Table

from opennem.db import get_database_engine
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

BULK_INSERT_QUERY = """
    CREATE TEMP TABLE __tmp_{table_name}_{tmp_table_name}
    (LIKE {table_name} INCLUDING DEFAULTS)
    ON COMMIT DROP;

    COPY __tmp_{table_name}_{tmp_table_name} FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');

    INSERT INTO {table_name}
        SELECT *
        FROM __tmp_{table_name}_{tmp_table_name}
    ON CONFLICT {on_conflict}
"""

BULK_INSERT_CONFLICT_UPDATE = """
    ({pk_columns}) DO UPDATE set {update_values}
"""


def build_insert_query(
    table: Table, update_cols: List[Union[str, Column]] = None,
) -> str:
    """
        Builds the bulk insert query
    """
    on_conflict = "DO NOTHING"

    def get_column_name(column: Union[str, Column]) -> str:
        if hasattr(column, "name"):
            return column.name
        if isinstance(column, str):
            return column.strip()
        return ""

    update_col_names = []

    if update_cols:
        update_col_names = [get_column_name(c) for c in update_cols]

    update_col_names = list(filter(lambda c: c, update_col_names))

    primary_key_columns = [
        c.name for c in table.__table__.primary_key.columns.values()
    ]

    if len(update_col_names):
        on_conflict = BULK_INSERT_CONFLICT_UPDATE.format(
            pk_columns=",".join(primary_key_columns),
            update_values=", ".join(
                [f"{n} = EXCLUDED.{n}" for n in update_col_names]
            ),
        )

    query = BULK_INSERT_QUERY.format(
        table_name=table.__table__.name,
        on_conflict=on_conflict,
        tmp_table_name=datetime.strftime(datetime.now(), "%Y%m%d%H%M%S"),
    )

    return query


class BulkInsertPipeline(object):
    @check_spider_pipeline
    def process_item(self, item: List[dict], spider):
        num_records = 0
        conn = get_database_engine().raw_connection()

        for single_item in item:
            if "csv" not in single_item:
                logger.error("No csv record passed to bulk inserter")
                return 0

            csv_content: StringIO = single_item["csv"]

            if "table_schema" not in single_item:
                logger.error("No table model passed to bulk inserter")
                return item

            table: Table = single_item["table_schema"]

            update_fields = None

            if "update_fields" in single_item:
                update_fields: List[str] = single_item["update_fields"]

            sql_query = build_insert_query(table, update_fields)

            try:
                cursor = conn.cursor()
                cursor.copy_expert(sql_query, csv_content)
                conn.commit()
            except Exception as generic_error:
                generic_error.hide_parameters = True
                logger.error(generic_error)

            try:
                num_records += len(csv_content.getvalue().split("\n")) - 1
            except Exception:
                pass

        return {"num_records": num_records}
