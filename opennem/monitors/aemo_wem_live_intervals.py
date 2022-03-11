import csv
import logging
from datetime import datetime

from opennem.controllers.nem import unit_scada_generate_facility_scada
from opennem.schema.network import NetworkWEM
from opennem.utils.http import http
from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger(__name__)

LIVE_FACILITIES = "https://aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv"

REQ_HEADERS = {
    "User-Agent": get_random_agent(),
}


def get_aemo_wem_live_facility_intervals_recent_date() -> datetime:
    """Returns the latest interval date from the WEM live feed. Used in monitors."""
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
        logger.error("WEM live facility intervals returning bad CSV: {}".format(LIVE_FACILITIES))

    records = unit_scada_generate_facility_scada(
        records=csvreader,
        interval_field="PERIOD",
        facility_code_field="FACILITY_CODE",
        power_field="ACTUAL_MW",
        network=NetworkWEM,
    )

    trading_intervals = [i["trading_interval"] for i in records]

    if not trading_intervals:
        raise Exception("Error parsing AEMO WEM live facility intervals")

    max_date = max(trading_intervals)

    return max_date
