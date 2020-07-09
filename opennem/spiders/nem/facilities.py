from io import BytesIO

import scrapy
from openpyxl import load_workbook


class NemFacilitySpider(scrapy.Spider):
    name = "au.nem.facilities"

    start_urls = [
        "https://aemo.com.au/-/media/files/electricity/nem/planning_and_forecasting/generation_information/nem-generation-information-april-2020.xlsx?la=en"
    ]

    keys = [
        "Region",
        "Status",
        "Name",
        "Owner",
        "TechType",
        "FuelType",
        "DUID",
        "Units",
        "NameCapacity",
        "StorageCapacity",
        "UnitStatus",
        "DispatchType",
        "UseDate",
        "ClosureDateExpected",
        "ClosureDate",
        "SurveyVersion",
        "SurveyEffective",
    ]

    def parse(self, response):
        wb = load_workbook(BytesIO(response.body), data_only=True)

        ws = wb.get_sheet_by_name("ExistingGeneration&NewDevs")

        for row in ws.iter_rows(min_row=3, max_row=13, values_only=True):

            # pick out the columns we want
            # lots of hidden columns in the sheet
            row_collapsed = row[0:8] + (row[11],) + row[13:19] + row[22:]

            yield dict(zip(self.keys, list(row_collapsed)))
