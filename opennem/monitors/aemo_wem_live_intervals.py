import csv
from datetime import datetime

import requests

from opennem.pipelines.nem.opennem import unit_scada_generate_facility_scada
from opennem.schema.network import NetworkWEM
from opennem.settings.scrapy import USER_AGENT

LIVE_FACILITIES = "https://aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv"

REQ_HEADERS = {
    "User-Agent": USER_AGENT,
}


def get_aemo_wem_live_facility_intervals_recent_date() -> datetime:
    csv_content = requests.get(LIVE_FACILITIES, headers=REQ_HEADERS).content

    csvreader = csv.DictReader(csv_content.decode("utf-8").split("\n"))

    records = unit_scada_generate_facility_scada(
        records=csvreader,
        interval_field="PERIOD",
        facility_code_field="FACILITY_CODE",
        power_field="ACTUAL_MW",
        network=NetworkWEM,
    )

    max_date = max([i["trading_interval"] for i in records])

    return max_date

