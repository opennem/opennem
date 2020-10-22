import csv
import logging
from io import StringIO

from sqlalchemy.sql.schema import Table

from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def generate_csv_from_records(table: Table, records, column_names=None):
    csv_buffer = StringIO()

    if not column_names:
        column_names = [c.name for c in table.__table__.columns.values()]

    csvwriter = csv.DictWriter(csv_buffer, fieldnames=column_names)

    # for field_name in records[0].keys():
    #     if field_name not in column_names:
    #         raise Exception("Column name not found: {}".format(field_name))

    # @TODO put the columns in the correct order ..

    for record in records:
        csvwriter.writerow(record)

    csv_buffer.seek(0)
    return csv_buffer


class RecordsToCSVPipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if not isinstance(item, dict):
            logger.error("Invalid item passed to CSV pipeline: %s", item)
            return item

        if "table_schema" not in item:
            logger.error("No table model passed to csv generator")
            logger.error(item)
            return item

        table = item["table_schema"]

        if "records" not in item:
            logger.error("No records to generate csv from")
            return item

        records = item["records"]

        csv_content = generate_csv_from_records(table, records)

        item["csv"] = csv_content

        return item
