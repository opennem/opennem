"""BOM history spider. Imports historic highs/lows from the BOM website.

"""
from datetime import datetime
from typing import Any, Dict, Generator, Optional

import scrapy
from scrapy.http import TextResponse

from opennem.core.normalizers import clean_float, is_number
from opennem.pipelines.bom import StoreBomHistoryObservation
from opennem.spiders.bom.utils import get_archive_page_for_station_code, get_stations_priority

from .utils import BOM_REQUEST_HEADERS


class BOMHistorySpider(scrapy.Spider):
    name = "bom.history"

    allowed_domains = ["bom.gov.au"]

    # pipelines = set([StoreBomHistoryObservation])

    station_id: Optional[str] = None

    random_user_agent: bool = True

    latest_month: bool = True

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        priority_stations = get_stations_priority()[:1]

        _headers = BOM_REQUEST_HEADERS.copy()

        months = []

        if self.latest_month:
            months = [datetime.now().date()]

        for station in priority_stations:
            for month in months:
                req_url = get_archive_page_for_station_code(station.web_code, month)
                yield scrapy.Request(
                    req_url,
                    meta={"code": station.code, "month": month},
                    headers=_headers
                )  # type: ignore

    def parse(self, response: TextResponse) -> Generator[Dict[str, Any], None, None]:
        code = None
        month = None

        if "month" not in response.meta:
            yield None

        month = response.meta["month"]

        if "code" in response.meta:
            code = response.meta["code"]

        elif hasattr(self, "station_id") and self.station_id:
            code = self.station_id

        if not code:
            raise Exception("No station id for this scrape can't join")

        records = []

        for trow in response.css("#columns tbody tr"):
            first_value_sel = trow.css("th::text")

            if not first_value_sel:
                continue

            first_col_val = first_value_sel[0].get()

            if not is_number(first_col_val):
                continue

            day_of_month = int(first_col_val)

            records.append({
                "observation_date": month.replace(day=day_of_month),
                "code": code,
                "temp_min": clean_float(trow.css("td.xb::text").get()),
                "temp_max": clean_float(trow.css("td.c")[1].css("::text").get())
            })

        yield {"records": records}
