#!/usr/bin/env python
"""
APVI Rooftop Data Read Script
"""
import json
import logging
from datetime import datetime
from itertools import groupby

import requests

from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.pipelines.apvi.data import STATE_POSTCODE_PREFIXES
from opennem.spiders.apvi.data import APVI_DATA_URI, APVI_DATE_QUERY_FORMAT, TODAY
from opennem.utils.dates import date_series

logger = logging.getLogger("opennem.scripts.apvi")

APVI_BASE = ""

SWIS_CODES = ["65", "64", "63", "62", "61", "60"]


def main() -> None:

    json_data_ungrouped = []

    for req_date in date_series(TODAY, length=1, reverse=True):

        logger.info("Getting data for {}".format(req_date))

        records = requests.post(
            APVI_DATA_URI,
            data={"day": req_date.strftime(APVI_DATE_QUERY_FORMAT)},
        ).json()

        postcode_gen = records["postcode"]
        postcode_capacity = records["postcodeCapacity"]

        for record in postcode_gen:
            for state, prefix in STATE_POSTCODE_PREFIXES.items():

                if state not in ["WA"]:
                    continue

                interval_time = datetime.fromisoformat(record["ts"].replace("Z", "+10:00"))

                # interval_time = parse_date(
                #     record["ts"],
                #     dayfirst=False,
                #     yearfirst=True,
                # )

                # interval_time = interval_time.astimezone(NetworkNEM.get_timezone())

                generated_state = sum(
                    [
                        float(v) / 100 * postcode_capacity[k]
                        for k, v in record.items()
                        if k.startswith(prefix) and v and k in postcode_capacity
                    ]
                )

                generated_swis = sum(
                    [
                        float(v) / 100 * postcode_capacity[k]
                        for k, v in record.items()
                        if k[:2] in SWIS_CODES and v and k in postcode_capacity
                    ]
                )

                json_data_ungrouped.append(
                    {
                        "trading_interval": interval_time,
                        "swis": generated_swis,
                        state: generated_state,
                    }
                )

    json_grouped_date = {}

    from pprint import pprint

    pprint(json_data_ungrouped)

    for date_grouped_str, v in groupby(
        json_data_ungrouped, lambda k: str(k["trading_interval"].date())
    ):
        if date_grouped_str not in json_grouped_date:
            json_grouped_date[date_grouped_str] = []

        json_grouped_date[date_grouped_str] += list(v)

    json_grouped_summed = {}

    for grouped_date, trading_day in json_grouped_date.items():
        json_grouped_summed = {}

        if grouped_date not in json_grouped_summed:
            json_grouped_summed[grouped_date] = {}

        # print(json_grouped_summed)

        for trading_interval in trading_day:
            for k, v in trading_interval.items():
                if k in ["trading_interval"]:
                    continue

                if k not in json_grouped_summed[grouped_date]:
                    json_grouped_summed[grouped_date][k] = 0

                json_grouped_summed[grouped_date][k] += v
                json_grouped_summed[grouped_date][k] = round(
                    json_grouped_summed[grouped_date][k], 2
                )

    json_serialized = json.dumps(json_grouped_summed, indent=4, cls=OpenNEMJSONEncoder)

    # print(json_serialized)


if __name__ == "__main__":
    main()
