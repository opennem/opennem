# import json
from typing import Any, Dict, Generator

import scrapy

from opennem.pipelines.nem.summary import NemwebSummaryPipeline


class NemSummarySpider(scrapy.Spider):
    name = "au.nem.summary"
    start_urls = ["https://www.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY"]

    pipelines_extra = set(
        [
            NemwebSummaryPipeline,
        ]
    )

    def parse(self, response: Any) -> Generator[Dict, None, None]:
        # json_resp = None

        # try:
        #     json_resp = json.loads(response.text)
        # except ValueError:
        #     pass

        yield {"content": response.json()}
