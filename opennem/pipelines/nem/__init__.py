import csv
import logging
import zipfile

from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class TableRecordSplitter(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        if "tables" not in item:
            logger.error(item)
            raise Exception("No tables passed to pipeline")

        tables = item["tables"]
        table = tables.pop()

        records = table["records"]

        for record in records:
            yield record


class UnzipSingleFilePipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider):

        if "body_stream" not in item:
            return item

        rs = item["body_stream"]
        content = ""

        with zipfile.ZipFile(rs) as zf:
            zip_files = zf.namelist()

            if len(zip_files) == 1:
                content = zf.open(zip_files[0])
                return {"file_handle": content, **item}

            if len(zip_files) != 1:
                raise Exception(
                    "Zero or more than one file in zip file. Have {}".format(
                        len(zip_files)
                    )
                )


class ReadStringHandle(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        if "file_handle" not in item:
            return item

        fh = item["file_handle"]

        content = fh.read()

        if type(content) is bytes:
            content = content.decode("utf-8")

        return {"content": content, **item}


class ExtractCSV(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        if not item:
            logger.error("No item to parse")
            return None

        if "content" not in item:
            logger.error("No content in item to parse")
            return item

        content = item["content"]
        del item["content"]

        item["tables"] = {}
        table = {"name": None}

        content_split = content.splitlines()

        datacsv = csv.reader(content_split)

        for row in datacsv:
            if not row or type(row) is not list or len(row) < 1:
                continue

            record_type = row[0]

            if record_type == "C":
                # @TODO csv meta stored in table
                if table["name"] is not None:
                    table_name = table["name"]

                    if table_name in item["tables"]:
                        item["tables"][table_name]["records"] += table[
                            "records"
                        ]
                    else:
                        item["tables"][table_name] = table

            elif record_type == "I":
                if table["name"] is not None:
                    table_name = table["name"]

                    if table_name in item["tables"]:
                        item["tables"][table_name]["records"] += table[
                            "records"
                        ]
                    else:
                        item["tables"][table_name] = table

                table = {}
                table["name"] = "{}_{}".format(row[1], row[2])
                table["fields"] = fields = row[4:]
                table["records"] = []

            elif record_type == "D":
                values = row[4:]
                record = dict(zip(table["fields"], values))

                table["records"].append(record)

        return item


class DatabaseStore(object):
    def __init__(self):
        engine = db_connect()
        self.session = sessionmaker(bind=engine)
