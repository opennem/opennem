#!/usr/bin/env python
""" Script to test OpenNEM flows """
import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from textwrap import dedent, indent
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
import pydantic

from opennem.controllers.flows import get_network_interconnector_intervals
from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import AEMOTableSet, parse_aemo_url
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized
from opennem.db import get_database_engine
from opennem.queries.flows import get_interconnector_intervals_query
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import date_series, get_last_complete_day_for_network
from opennem.workers.emissions import load_interconnector_intervals

logger = logging.getLogger("opennem.flows")

COMPARISON_START_DATE = datetime.fromisoformat("2022-01-01T00:00:00")

COMPARISON_END_DATE = datetime.fromisoformat("2022-08-01:00:00")


def plot_deltas(deltas: list[Dict], destination_file: str = "flows.png") -> None:
    _, ax = plt.subplots()

    x = [i.interval for i in deltas]
    y = [i.value for i in deltas]

    vic1 = ax.bar(x, y, label="vic1")
    ax.axhline(0, color="grey", linewidth=0.8)
    ax.set_ylabel("delta")
    ax.set_title("OpenNEM VWP Deltas")
    # ax.bar_label(vic1, label_type="center")

    ax.legend()
    plt.show()
    plt.savefig(destination_file)
    logger.info(f"Saved figure to {destination_file}")


def get_aemo_raw_values(persist: bool = False, flowset_path: Path | None = None) -> AEMOTableSet:
    """Get raw aemo values from nemweb"""

    urls: list[str] = []

    for date_series_date in date_series(start=COMPARISON_START_DATE, end=COMPARISON_END_DATE + timedelta(days=1)):
        dfmt = date_series_date.strftime("%Y%m%d")
        urls.append(f"https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/PUBLIC_DISPATCHIS_{dfmt}.zip")

    trading_is_urls = [
        "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20211219_20211225.zip",
        "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20211226_20220101.zip",
        "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220102_20220108.zip",
        "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220109_20220115.zip",
        "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220116_20220122.zip",
        "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220123_20220129.zip",
        "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220130_20220205.zip",
    ]

    # urls += trading_is_urls

    ts = AEMOTableSet()

    # This will iterate through the URLs, parse them and add them to the AEMOTableSet
    for u in trading_is_urls:
        ts = parse_aemo_url_optimized(u, table_set=ts, persist_to_db=False, values_only=True)

    if not persist and not flowset_path:
        return ts

    with open(flowset_path, "w") as fh:
        fh.write(ts.json(indent=4))

    logger.info(f"Wrote table_set to file {flowset_path}")

    return ts


def get_aemo_tableset(tableset_path: Path) -> AEMOTableSet:
    """Reads the stored tableset fixture path and returns an AEMOTableSet"""
    return pydantic.parse_file_as(path=str(tableset_path), type_=AEMOTableSet)


def dump_tableset_csvs() -> None:

    ts = get_aemo_tableset()

    csv_path = Path(__file__).parent.parent / "notebooks" / "data"

    for table in ts.tables:
        print(f"Have table {table.full_name}")
        table.to_csv(str(csv_path / f"{table.full_name}.csv"))


def flow_plot() -> None:
    """Plot flows"""
    date_start = get_last_complete_day_for_network(NetworkNEM)
    date_end = date_start + timedelta(days=1)

    interconnector_results = get_network_interconnector_intervals(date_start, date_end, network=NetworkNEM)

    for result in interconnector_results:
        logger.info(f"Have interconnector result {result}")


if __name__ == "__main__":
    # get_aemo_raw_values()
    flow_plot()
