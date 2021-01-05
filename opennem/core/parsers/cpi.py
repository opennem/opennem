"""
OpenNEM Parser for Australian CPI Data

Source: https://www.rba.gov.au/statistics/tables/xls/g01hist.xls?v=2020-12-24-16-59-11

"""

import logging
from datetime import datetime
from typing import List

import xlrd
from pydantic.error_wrappers import ValidationError

from opennem.schema.stats import AUCpiData, StatDatabase, StatsSet, StatTypes
from opennem.utils.http import http

logger = logging.getLogger("opennem.stats.au.api")

AU_CPI_URL = "https://www.rba.gov.au/statistics/tables/xls/g01hist.xls"


def fetch_au_cpi() -> List[AUCpiData]:
    """Gets australian CPI figures and parses into JSON"""
    r = http.get(AU_CPI_URL)

    if not r.ok:
        raise Exception(
            "Problem grabbing CPI source: {}".format(r.status_code)
        )

    wb = xlrd.open_workbook(file_contents=r.content)

    if "Data" not in wb.sheet_names():
        raise Exception("No Data sheet in CPI workbook")

    wb_data = wb.sheet_by_index(0)
    records = []

    for i in range(11, wb_data.nrows):
        row = wb_data.row_values(i, 0, 2)

        cpi_record = None

        # skip empty values
        if not row[1]:
            continue

        try:
            cpi_record = AUCpiData(quarter_date=row[0], cpi_value=row[1])
        except ValidationError as e:
            logger.info("Invalid CPI data: {}".format(e))
            continue

        if cpi_record:
            records.append(cpi_record)

    return records


def au_cpi_to_statset(records: List[AUCpiData]) -> StatsSet:

    stat_set = [
        StatDatabase(
            stat_date=i.quarter_date,
            stat_type=StatTypes.CPI,
            value=i.cpi_value,
        )
        for i in records
    ]

    s = StatsSet(
        name="au.cpi",
        source_url=AU_CPI_URL,
        fetched_date=datetime.now(),
        stats=stat_set,
    )

    return s


def stat_au_cpi() -> StatsSet:
    records = fetch_au_cpi()
    return au_cpi_to_statset(records)


if __name__ == "__main__":
    r = stat_au_cpi()
