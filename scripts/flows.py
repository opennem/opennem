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

from opennem.api.stats.schema import ValidNumber
from opennem.controllers.flows import get_network_interconnector_intervals
from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import AEMOTableSet, parse_aemo_url
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized
from opennem.core.time import get_interval
from opennem.db import get_database_engine
from opennem.queries.flows import get_interconnector_intervals_query
from opennem.schema.dates import DatetimeRange, TimeSeries
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.utils.dates import date_series, get_last_complete_day_for_network
from opennem.utils.interval import get_human_interval
from opennem.workers.emissions import load_interconnector_intervals

logger = logging.getLogger("opennem.flows")

COMPARISON_START_DATE = datetime.fromisoformat("2022-01-01T00:00:00")

COMPARISON_END_DATE = datetime.fromisoformat("2022-08-01:00:00")


@dataclass
class PlotSeries:
    interval: datetime
    value: ValidNumber


def plot_flows(flows: list[PlotSeries], destination_file: str = "flows.png") -> None:
    _, ax = plt.subplots()

    x = [i.interval for i in flows]
    y = [i.value for i in flows]

    vic1 = ax.bar(x, y, label="vic1")
    ax.axhline(0, color="grey", linewidth=0.8)
    ax.set_ylabel("value")
    ax.set_title("OpenNEM Flows")
    # ax.bar_label(vic1, label_type="center")

    ax.legend()
    plt.show()
    plt.savefig(destination_file)
    logger.info(f"Saved figure to {destination_file}")


def get_aemo_tableset(tableset_path: Path) -> AEMOTableSet:
    """Reads the stored tableset fixture path and returns an AEMOTableSet"""
    return pydantic.parse_file_as(path=str(tableset_path), type_=AEMOTableSet)


def dump_tableset_csvs() -> None:

    ts = get_aemo_tableset()

    csv_path = Path(__file__).parent.parent / "notebooks" / "data"

    for table in ts.tables:
        print(f"Have table {table.full_name}")
        table.to_csv(str(csv_path / f"{table.full_name}.csv"))


def get_network_flows_emissions_market_value_query(time_series: TimeSeries, network_region_code: str) -> str:
    """ """

    __query = """
        select
            date_trunc('{trunc}', t.trading_interval at time zone '{timezone}') as trading_interval,
            sum(t.imports_energy) / 1000 as imports_energy,
            sum(t.exports_energy) / 1000 as exports_energy,
            abs(sum(t.emissions_imports)) as imports_emissions,
            abs(sum(t.emissions_exports)) as exports_emissions,
            sum(t.market_value_imports) as imports_market_value,
            sum(t.market_value_exports) as exports_market_value
        from (
            select
                time_bucket_gapfill('5 min', t.trading_interval) as trading_interval,
                t.network_id,
                t.network_region,
                coalesce(t.energy_imports, 0) as imports_energy,
                coalesce(t.energy_exports, 0) as exports_energy,
                coalesce(t.emissions_imports, 0) as emissions_imports,
                coalesce(t.emissions_exports, 0) as emissions_exports,
                coalesce(t.market_value_imports, 0) as market_value_imports,
                coalesce(t.market_value_exports, 0) as market_value_exports
            from at_network_flows t
            where
                t.trading_interval < '{date_max}' and
                t.trading_interval >= '{date_min}' and
                t.network_id = '{network_id}' and
                t.network_region = '{network_region_code}'
        ) as t
        group by 1
        order by 1 desc
    """

    return dedent(
        __query.format(
            timezone=time_series.network.timezone_database,
            trunc="day",
            network_id=time_series.network.code,
            date_min=time_series.time_range.start,
            date_max=time_series.time_range.end,
            network_region_code=network_region_code,
        )
    )


def flow_plot() -> None:
    """Plot flows"""
    date_end = get_last_complete_day_for_network(NetworkNEM)
    date_start = date_end - timedelta(days=1)

    # interconnector_results = get_network_interconnector_intervals(date_start, date_end, network=NetworkNEM)
    ts = TimeSeries(
        network=NetworkNEM,
        interval=get_interval("1d"),
        time_range=DatetimeRange(start=date_start, end=date_end, interval=get_interval("1d")),
    )
    derived_table = get_network_flows_emissions_market_value_query(time_series=ts, network_region_code="NSW1")

    print(derived_table)


if __name__ == "__main__":
    # get_aemo_raw_values()
    flow_plot()
