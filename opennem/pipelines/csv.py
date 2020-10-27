import csv
import logging
from io import StringIO
from typing import List

from sqlalchemy.sql.schema import Table

from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def generate_csv_from_records(table: Table, records, column_names=None):
    if len(records) < 1:
        raise Exception("No records")

    csv_buffer = StringIO()

    table_column_names = [c.name for c in table.__table__.columns.values()]

    if isinstance(records, list):
        first_record = records[0]

        record_field_names = list(first_record.keys())

        for field_name in record_field_names:
            if field_name not in table_column_names:
                raise Exception("Column name not found: {}".format(field_name))

        for column_name in table_column_names:
            if column_name not in record_field_names:
                raise Exception(
                    "Missing value for column {}".format(column_name)
                )

        column_names = record_field_names

    if not column_names:
        column_names = table_column_names

    csvwriter = csv.DictWriter(csv_buffer, fieldnames=column_names)
    csvwriter.writeheader()

    # @TODO put the columns in the correct order ..

    for record in records:
        csvwriter.writerow(record)

    csv_buffer.seek(0)
    return csv_buffer


class RecordsToCSVPipeline(object):
    @check_spider_pipeline
    def process_item(self, item: List[dict], spider=None):
        if not isinstance(item, list):
            item = [item]

        for record_set in item:
            if not isinstance(record_set, dict):
                logger.error(
                    "Invalid record_set passed to CSV pipeline: %s", record_set
                )
                return record_set

            if "table_schema" not in record_set:
                logger.error("No table model passed to csv generator")
                logger.error(record_set)
                return record_set

            table = record_set["table_schema"]

            if "records" not in record_set:
                logger.error("No records to generate csv from")
                return record_set

            records = record_set["records"]

            csv_content = generate_csv_from_records(table, records)

            record_set["csv"] = csv_content

        return item
