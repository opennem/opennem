"""
Do some sanity checking on all outputs to make sure they're not shifting ¯\_(ツ)_/¯

We get the latest month x times a day and just store the results. Make sure they're consitent.
If they're not, raise hell.
"""

import io
import logging
from csv import DictReader, DictWriter
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import requests

from opennem.api.stats.loader import load_statset
from opennem.core.fueltechs import get_fueltechs
from opennem.exporter.aws import write_to_s3

logger = logging.getLogger("opennem.monitors.set_outputs")

V3_ALL_URL = "https://data.opennem.org.au/v3/stats/au/NEM/energy/all.json"
OUTPUT_THE_CHECK_CSV_PATH = "checks/all_output_checks.csv"


CSV_OUTPUT_COLUMNS = ["run_dt", "check_network", "check_date"] + [i.code for i in get_fueltechs()]


def get_last_month() -> date:
    """return first day of last month"""
    first_of_this_month = date.today().replace(day=1)
    lastMonth = first_of_this_month - timedelta(days=1)
    return date(lastMonth.year, lastMonth.month, 1)


def _get_current_csv_content() -> Optional[str]:
    # @TODO abstract out dev.
    check_url = "https://data.dev.opennem.org.au/checks/all_output_checks.csv"
    r = requests.get(check_url)

    if not r.ok:
        return None

    return r.content.decode("utf-8")


def _get_current_records() -> List[Dict]:
    """Gets the current csv storing all out history"""
    current_csv = _get_current_csv_content()

    if not current_csv:
        return []

    try:
        csv_input = DictReader(current_csv.splitlines(), fieldnames=CSV_OUTPUT_COLUMNS)
        current_records = list(csv_input)
        return current_records
    except Exception as e:
        logger.error("Error getting current CSV: {}".format(e))
        return []


def run_set_output_check() -> None:
    """get the latest all json, pop out the energy values for the last month"""
    r = requests.get(V3_ALL_URL)
    v3 = load_statset(r.json())

    if not v3:
        raise Exception("Failed to get v3 all data")

    check_date = get_last_month()

    logger.info("Checking {}".format(check_date))

    check_result = {
        "run_dt": str(datetime.now()),
        "check_network": "NEM",
        "check_date": str(check_date),
    }

    for i in v3.data:
        if not i.id:
            continue

        if not i.id.endswith("energy"):
            continue

        d = i.history.get_date(check_date)

        if i.fuel_tech and d:
            check_result[i.fuel_tech] = d

    current_records = _get_current_records()

    logger.info("Have {} current records".format(len(current_records)))

    current_records.append(check_result)

    # write to csv string
    output = io.StringIO()
    csv_output = DictWriter(output, fieldnames=CSV_OUTPUT_COLUMNS)
    csv_output.writeheader()
    csv_output.writerows(current_records)

    write_to_s3(output.getvalue(), OUTPUT_THE_CHECK_CSV_PATH, "text/csv")


# debug entry point
if __name__ == "__main__":
    run_set_output_check()
