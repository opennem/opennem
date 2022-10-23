#!/usr/bin/env python
""" Test interconnector data """
import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from itertools import groupby
from pathlib import Path
from pprint import pprint
from textwrap import dedent, indent
from typing import Dict

import pandas as pd
import pydantic

from opennem.api.stats.schema import ValidNumber, load_opennem_dataset_from_url
from opennem.controllers.flows import get_network_interconnector_intervals
from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import AEMOTableSet, parse_aemo_file, parse_aemo_url
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized
from opennem.core.time import get_interval
from opennem.db import get_database_engine
from opennem.queries.flows import get_interconnector_intervals_query
from opennem.schema.dates import DatetimeRange, TimeSeries
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.utils.chart import Plot, PlotIntegerValues, PlotSeries, PlotValues, chart_line
from opennem.utils.dates import date_series, get_last_complete_day_for_network
from opennem.utils.interval import get_human_interval
from opennem.workers.emissions import (
    calc_flows_for_range,
    load_interconnector_intervals,
    merge_interconnector_and_energy_data,
)
from tests.workers.flows import get_flow_fixture_dataframe

logger = logging.getLogger("opennem.flows")

SRC_2019 = "/var/folders/v7/qpcbq9jx04gf6bgcsdy4tvy80000gn/T/opennem_0fagth98/PUBLIC_DVD_DISPATCHINTERCONNECTORRES_201901010000.CSV"
SRC_2022 = "/var/folders/v7/qpcbq9jx04gf6bgcsdy4tvy80000gn/T//opennem_t207p2yl/PUBLIC_DVD_DISPATCHINTERCONNECTORRES_202201010000.CSV"


def compare_and_chart_datasets(subject, comparator) -> None:
    """Compare and chart two datasets normalizing dates"""

    return None


def part_date(ts: pd.Timestamp | datetime) -> datetime:
    """Convert pandas timestamp to parted datetime"""
    dt = ts if isinstance(ts, (date, datetime)) else ts.to_pydatetime()
    dt = dt.replace(year=2022)
    return dt


def compare_old_and_new_interconnectors(save_plot: bool = True, show: bool = False) -> None:
    table_name = "interconnectorres"

    old = parse_aemo_file(Path(SRC_2019)).get_table(table_name).to_frame()
    new = parse_aemo_file(Path(SRC_2022)).get_table(table_name).to_frame()

    interconnector_old = old[old.interconnectorid == "NSW1-QLD1"]
    interconnector_new = new[new.interconnectorid == "NSW1-QLD1"]

    start_date = datetime.fromisoformat("2019-01-01T00:00:00+10:00")
    end_date = datetime.fromisoformat("2019-01-08T00:00:00+10:00")

    interconnector_old = interconnector_old[interconnector_old.settlementdate.between(start_date, end_date)]

    start_date = start_date.replace(year=2022)
    end_date = end_date.replace(year=2022)

    interconnector_new = interconnector_new[interconnector_new.settlementdate.between(start_date, end_date)]

    plot_series = []
    records = {}

    for idata in [interconnector_new, interconnector_old]:

        for record in idata.to_dict("records"):
            dt = part_date(record["settlementdate"])
            if dt not in records:
                records[dt] = {"time_interval": dt, "meteredmwflow_2019": 0, "meteredmwflow_2022": 0}

            if idata.iloc[0].settlementdate.year == 2022:
                records[dt]["meteredmwflow_2022"] = record["meteredmwflow"]
            else:
                records[dt]["meteredmwflow_2019"] = record["meteredmwflow"]

        # values = [
        #     PlotValues(interval=part_date(record["settlementdate"]), value=record["meteredmwflow"])
        #     for record in idata.to_dict("records")
        # ]

        # plot_series.append(
        #     PlotSeries(
        #         values=values,
        #         color="r" if idata is interconnector_new else "b",
        #         label="New" if idata is interconnector_new else "Old",
        #     )
        # )

    # p = Plot(series=plot_series, title="Data comparison", legend=True)

    # destination_file = "interconnector_plot.png" if save_plot else None

    # chart_line(plot=p, show=show, destination_file=destination_file)

    # pprint(records.values())

    with open("interconnector_comp.csv", "w") as fh:
        csvwriter = csv.DictWriter(fh, fieldnames=list(records.values())[0].keys())
        csvwriter.writerows(list(records.values()))

    return plot_series


if __name__ == "__main__":
    ps = compare_old_and_new_interconnectors()
    pprint(ps)
