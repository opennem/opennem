"""
Take records generated from previous pipeline steps (usually a list of
dicts) and prep them into CSV in the shape of the database table
schema so they can be used with bulk_insert

"""
import csv
import logging
from io import StringIO
from typing import Dict, List, Optional, Union

from scrapy import Spider
from sqlalchemy.sql.schema import Table

from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def pad_column_null(records: List[Dict], column_name: str) -> List[Dict]:
    """Adds missing column name into the list of table records"""
    a = []

    for i in records:
        a.append({column_name: "", **i})

    return a


def generate_csv_from_records(
    table: Union[Table, FacilityScada, BalancingSummary],
    records: List[Dict],
    column_names: Optional[List[str]] = None,
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
                    "Column name from records not found in table: {}. Have {}".format(
                        field_name, ", ".join(table_column_names)
                    )
                )

        for column_name in table_column_names:
            if column_name not in record_field_names:
                raise Exception("Missing value for column {}".format(column_name))

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


class RecordsToCSVPipeline(object):
    """
    Pipeline that adapts the CSV generator and bulk inserter

    """

    @check_spider_pipeline
    def process_item(
        self, item: Union[List[Dict], Dict], spider: Optional[Spider] = None
    ) -> List[Dict]:

        # if it's a single item put it in a list
        if not isinstance(item, list):
            item = [item]

        for record_set in item:
            if not isinstance(record_set, dict):
                logger.error("Invalid record_set passed to CSV pipeline: %s", record_set)
                return record_set

            if "table_schema" not in record_set:
                logger.error("No table model passed to csv generator")
                logger.error(record_set)
                return item

            table = record_set["table_schema"]

            if "records" not in record_set:
                logger.error("No records to generate csv from")
                return item

            records = record_set["records"]

            csv_content = generate_csv_from_records(table, records)

            record_set["csv"] = csv_content

        return item
