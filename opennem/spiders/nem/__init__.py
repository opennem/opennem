import io
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

import scrapy

from opennem.pipelines.bulk_insert import BulkInsertPipeline
from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.nem import (
    ExtractCSV,
    ReadStringHandle,
    TableRecordSplitter,
    UnzipSingleFilePipeline,
)
from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.utils.dates import month_series
from opennem.utils.handlers import _handle_zip, chain_streams
from opennem.utils.mime import decode_bytes, mime_from_content, mime_from_url


def get_date_component(format_str, dt: datetime = None):
    if dt:
        return dt.strftime(format_str)
    return datetime.now().strftime(format_str)


class NemXLSSpider(scrapy.Spider):

    start_url = ""

    url_params = {
        "day": get_date_component("%d"),
        "month": get_date_component("%m"),
        "year": get_date_component("%Y"),
    }

    def start_requests(self):
        request_url = self.start_url.format(**self.url_params)

        yield scrapy.Request(request_url)

    def parse(self, response):
        yield {"content": response.text}


class NemSingleMMSSpider(scrapy.Spider):

    pipelines = set(
        [
            UnzipSingleFilePipeline,
            ReadStringHandle,
            ExtractCSV,
            TableRecordSplitter,
        ]
    )

    def start_requests(self):
        if not hasattr(self, "url"):
            raise Exception("{} requires url parameter".format(self.__class__))

        yield scrapy.Request(self.url)

    def parse(self, response):
        yield {"body_stream": io.BytesIO(response.body)}


MMS_URL = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/{year}/MMSDM_{year}_{month}/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_{table}_{year}{month}010000.zip"


class MMSArchiveSingleSpider(scrapy.Spider):
    name = "au.mms.archive"

    tables = ["DISPATCH_UNIT_SCADA", "DISPATCH_PRICE"]

    pipelines = set(
        [
            ExtractCSV,
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )

    def start_requests(self):
        start_month = datetime(2019, 10, 1)
        end_month = datetime(2010, 1, 1)
        for date in month_series(start_month, end_month):
            for table in self.tables:
                url_params = {
                    "month": get_date_component("%m", date),
                    "year": get_date_component("%Y", date),
                    "table": table.upper(),
                }

                req_url = MMS_URL.format(**url_params)

                yield scrapy.Request(req_url)

    def parse(self, response):
        content = None

        file_mime = mime_from_content(response.body)

        if not file_mime:
            file_mime = mime_from_url(response.url)

        if file_mime == "application/zip":
            with ZipFile(BytesIO(response.body)) as zf:
                if len(zf.namelist()) == 1:
                    content = zf.open(zf.namelist()[0]).read()

                c = []
                stream_count = 0

                for filename in zf.namelist():
                    if filename.endswith(".zip"):
                        c.append(_handle_zip(zf.open(filename), "r"))
                        stream_count += 1
                    else:
                        c.append(zf.open(filename))

                content = chain_streams(c).read()
        else:
            content = response.body.getvalue()

        content = decode_bytes(content)

        item = {}
        item["content"] = content
        item["extension"] = ".csv"
        item["mime_type"] = file_mime

        yield item
