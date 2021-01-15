import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, Generator
from zipfile import ZipFile

import scrapy

from opennem.pipelines.bulk_insert import BulkInsertPipeline
from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.nem import ExtractCSV
from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.utils.dates import get_date_component, month_series
from opennem.utils.handlers import _handle_zip, chain_streams
from opennem.utils.mime import decode_bytes, mime_from_content, mime_from_url

logger = logging.getLogger(__name__)

MMS_URL = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/{year}/MMSDM_{year}_{month}/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_{table}_{year}{month}010000.zip"


class MMSArchiveBulkSpider(scrapy.Spider):
    name = "au.mms.archive.dispatch_scada"

    tables = ["DISPATCH_UNIT_SCADA"]

    pipelines = set(
        [
            ExtractCSV,
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        # start_month = datetime(2011, 10, 1)
        # end_month = datetime(2011, 10, 1)

        start_month = datetime(2020, 1, 1)
        end_month = datetime(2009, 7, 1)

        for date in month_series(start_month, end_month):
            for table in self.tables:
                url_params = {
                    "month": get_date_component("%m", dt=date),
                    "year": get_date_component("%Y", dt=date),
                    "table": table.upper(),
                }

                req_url = MMS_URL.format(**url_params)

                yield scrapy.Request(req_url)

    def parse(self, response) -> Generator[Dict, None, None]:
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

        if not content:
            logger.info("No content from scrapy request")
            return None

        content = decode_bytes(content)

        item = {}
        item["content"] = content
        item["extension"] = ".csv"
        item["mime_type"] = file_mime

        yield item


class MMSArchivePriceSpider(MMSArchiveBulkSpider):
    name = "au.mms.archive.dispatch_price"

    tables = ["DISPATCHPRICE"]

    pipelines = set(
        [
            ExtractCSV,
            NemwebUnitScadaOpenNEMStorePipeline,
        ]
    )


# class MMSArchiveP5InterconnectorSolutionSpider(MMSArchiveBulkSpider):
#     name = "au.mms.archive.p5_interconnector_solution"

#     tables = ["P5MIN_INTERCONNECTORSOLN"]

#     pipelines = set(
#         [
#             ExtractCSV,
#             NemwebUnitScadaOpenNEMStorePipeline,
#         ]
#     )


class MMSArchiveRooftopActualSpider(MMSArchiveBulkSpider):
    name = "au.mms.archive.rooftop_actual"

    tables = ["ROOFTOP_PV_ACTUAL"]

    pipelines = set(
        [
            ExtractCSV,
            NemwebUnitScadaOpenNEMStorePipeline,
        ]
    )
