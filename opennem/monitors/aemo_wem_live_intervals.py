import csv
import logging
from datetime import datetime

from opennem.pipelines.nem.opennem import unit_scada_generate_facility_scada
from opennem.schema.network import NetworkWEM
from opennem.settings.scrapy import USER_AGENT
from opennem.utils.http import http

logger = logging.getLogger(__name__)

LIVE_FACILITIES = "https://aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv"

REQ_HEADERS = {
    "User-Agent": USER_AGENT,
}


def get_aemo_wem_live_facility_intervals_recent_date() -> datetime:
    req = http.get(LIVE_FACILITIES, headers=REQ_HEADERS)

    if req.status_code != 200:
        logger.error(
            "WEM live facility intervals returning non 200: {} {}".format(
                LIVE_FACILITIES, req.status_code
            )
        )

    csv_content = req.content
    csvreader = csv.DictReader(csv_content.decode("utf-8").split("\n"))

    if not csvreader.fieldnames or len(csvreader.fieldnames) < 1:
        logger.error(
            "WEM live facility intervals returning bad CSV: {}".format(
                LIVE_FACILITIES
            )
        )

    records = unit_scada_generate_facility_scada(
        records=csvreader,
        interval_field="PERIOD",
        facility_code_field="FACILITY_CODE",
        power_field="ACTUAL_MW",
        network=NetworkWEM,
    )

    max_date = max([i["trading_interval"] for i in records])

    return max_date
