#!/usr/bin/env python
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pydantic.types import Json

from opennem.core.compat.energy import trading_energy_data
from opennem.core.compat.loader import load_statset_v2
from opennem.core.compat.schema import OpennemDataSetV2
from opennem.core.energy import _energy_aggregate, energy_sum
from opennem.core.parsers.aemo import parse_aemo_urls
from opennem.db import db_connect, get_database_engine
from opennem.pipelines.files import _fallback_download_handler
from opennem.schema.network import NetworkNEM
from opennem.settings import settings
from opennem.utils.http import http
from opennem.utils.numbers import sigfig_compact
from opennem.utils.series import series_are_equal, series_joined
from opennem.workers.energy import get_generated, get_generated_query

engine = db_connect(settings.db_url)
engine_local = db_connect("postgresql://opennem:opennem@127.0.0.1:15433/opennem")


def run() -> None:
    aemo = parse_aemo_urls(
        [
            "http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/PUBLIC_NEXT_DAY_DISPATCH_20210304_0000000337689171.zip",
            "http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/PUBLIC_NEXT_DAY_DISPATCH_20210305_0000000337748278.zip",
            "http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/PUBLIC_NEXT_DAY_DISPATCH_20210306_0000000337800035.zip",
        ]
    )

    meter_data = aemo.get_table("METER_DATA_GEN_DUID")

    if meter_data:
        df = pd.DataFrame(meter_data.records)
        df.INTERVAL_DATETIME = pd.to_datetime(df.INTERVAL_DATETIME)
        # df.INTERVAL_DATETIME = df.INTERVAL_DATETIME.dt.tz_localize("Aus tralia/Brisbane")
        df.to_csv("meter_data_jan.csv")

    dispatch_solution = aemo.get_table("DISPATCH_UNIT_SOLUTION")

    if dispatch_solution:
        df = dispatch_solution.to_frame()
        # df.SETTLEMENTDATE = pd.to_datetime(df.SETTLEMENTDATE)
        # df.INTERVAL_DATETIME = df.INTERVAL_DATETIME.dt.tz_localize("Australia/Brisbane")
        df.to_csv("unit_solution_jan.csv")


if __name__ == "__main__":
    run()
