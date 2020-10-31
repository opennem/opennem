import json
from datetime import datetime
from itertools import groupby
from urllib.parse import ParseResult

import requests

from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.pipelines.apvi.data import STATE_POSTCODE_PREFIXES
from opennem.schema.network import NetworkNEM
from opennem.spiders.apvi.data import (
    APVI_DATA_URI,
    APVI_DATE_QUERY_FORMAT,
    TODAY,
)
from opennem.utils.dates import date_series, parse_date

APVI_BASE = ""

SWIS_CODES = ["65", "64", "63", "62", "61", "60"]


def main():

    json_data_ungrouped = []

    for req_date in date_series(TODAY, length=2, reverse=True):
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

                interval_time = parse_date(
                    record["ts"], dayfirst=False, yearfirst=True,
                )

                interval_time = interval_time.astimezone(
                    NetworkNEM.get_timezone()
                )

                generated_state = sum(
                    [
                        float(v) / 100 * postcode_capacity[k]
                        for k, v in record.items()
                        if k.startswith(prefix)
                        and v
                        and k in postcode_capacity
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

    for date_grouped_str, v in groupby(
        json_data_ungrouped, lambda k: str(k["trading_interval"].date())
    ):
        if date_grouped_str not in json_grouped_date:
            json_grouped_date[date_grouped_str] = []

        json_grouped_date[date_grouped_str] += list(v)

    json_grouped_summed = {}

    for grouped_date, trading_day in json_grouped_date.items():
        json_grouped_summed = {}

        for k, v in trading_day.items():
            if k in ["trading_interval"]:
                continue
            json_grouped_summed[grouped_date]

    # value_dict = list(v).pop()
    # del value_dict["trading_interval"]

    # if not value_dict:
    #     continue

    # print(date_grouped_str)
    # pprint(value_dict)

    # json_grouped_date[date_grouped_str] = {
    #     dk: round(json_grouped_date[date_grouped_str][dk] + dv, 2)
    #     for dk, dv in value_dict.items()
    #     # if dk not in ["date", "trading_interval"]
    # }

    json_serialized = json.dumps(
        json_grouped_date, indent=4, cls=OpenNEMJSONEncoder
    )

    print(json_serialized)


if __name__ == "__main__":
    main()
