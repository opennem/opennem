"""
OpenNEM Parser for Australian CPI Data

Source: https://www.rba.gov.au/statistics/tables/xls/g01hist.xls?v=2020-12-24-16-59-11

"""

import logging
from datetime import datetime

import xlrd
from pydantic import ValidationError

from opennem.schema.stats import AUCpiData, StatDatabase, StatsSet, StatTypes
from opennem.utils.httpx import http

logger = logging.getLogger("opennem.stats.au.api")

AU_CPI_URL = "https://www.rba.gov.au/statistics/tables/xls/g01hist.xls"


async def fetch_au_cpi() -> list[AUCpiData]:
    """Gets australian CPI figures and parses into JSON"""
    r = await http.get(AU_CPI_URL)

    if not r.is_success:
        raise Exception(f"Problem grabbing CPI source: {r.status_code}")

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
            logger.info(f"Invalid CPI data: {e}")
            continue

        if cpi_record:
            records.append(cpi_record)

    return records


def au_cpi_to_statset(records: list[AUCpiData]) -> StatsSet:
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


async def stat_au_cpi() -> StatsSet:
    records = await fetch_au_cpi()
    return au_cpi_to_statset(records)


if __name__ == "__main__":
    import asyncio

    r = asyncio.run(stat_au_cpi())
    print(r)
