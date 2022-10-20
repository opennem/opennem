#!/usr/bin/env python
""" Script to test OpenNEM flows """
import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from textwrap import dedent, indent
from typing import Dict

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

COMPARISON_START_DATE = datetime.fromisoformat("2022-01-01T00:00:00")

COMPARISON_END_DATE = datetime.fromisoformat("2022-08-01:00:00")


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


from collections import namedtuple


def flow_plot(date_start: datetime, date_end: datetime) -> None:
    """Plot flows"""
    engine = get_database_engine()

    # interconnector_results = get_network_interconnector_intervals(date_start, date_end, network=NetworkNEM)
    ts = TimeSeries(
        network=NetworkNEM,
        interval=get_interval("1d"),
        time_range=DatetimeRange(start=date_start, end=date_end, interval=get_interval("1d")),
    )
    derived_table = get_network_flows_emissions_market_value_query(time_series=ts, network_region_code="NSW1")

    with engine.begin() as conn:
        results = db_extract_result_records(conn, derived_table)

    return results


# TODO Rename this here and in `flow_plot`
def db_extract_result_records(conn, derived_table) -> list[Dict[str, ValidNumber]]:
    result_proxy = conn.execute(derived_table)
    first_result = result_proxy.fetchone()

    ResultRecord = namedtuple("ResultRecord", first_result.keys())
    record = ResultRecord(*first_result)

    results = [record._asdict()]

    for row in result_proxy.fetchall():
        record = ResultRecord(*row)
        results.append(record._asdict())

    return results


def plot_emissions_from_fixtures() -> Dict:
    """ """
    data = {}

    for year in [2022, 2015]:
        data[year] = {}

        # interconnector data
        df_inter = get_flow_fixture_dataframe(f"interconnector_intervals_{year}.csv")

        # energy data
        df_gen = get_flow_fixture_dataframe(f"energy_set_{year}.csv")
        df_gen["price"] = df_gen["market_value"] / df_gen["generated"]
        df_gen["emission_factor"] = df_gen["emissions"] / df_gen["generated"]

        # assign objects
        data[year]["interconnector"] = df_inter
        data[year]["energy"] = df_gen

        edf = merge_interconnector_and_energy_data(
            df_energy=data[year]["energy"], df_inter=data[year]["interconnector"], scale=NetworkNEM.intervals_per_hour
        ).reset_index()

        data[year]["emissions"] = edf

    return data


def part_date(ts: pd.Timestamp) -> datetime:
    """Convert pandas timestamp to parted datetime"""
    dt = ts.to_pydatetime()
    dt = dt.replace(year=2022)
    return dt


def run_fixture_test(
    set_name: str = "emissions", field_name: str = "energy_imports", filter_field: str = "network_region"
) -> None:
    """ """
    data = plot_emissions_from_fixtures()

    plot_series = []

    colors = {2015: "blue", 2022: "red"}

    for year in [2022, 2015]:
        edf = data[year][set_name]
        series = edf[edf[filter_field] == "NSW1"][field_name]
        series = series.reset_index()

        plot_series.append(
            PlotSeries(
                values=[
                    PlotIntegerValues(interval=part_date(r["trading_interval"]), value=r[field_name])
                    for r in series.to_dict("records")
                ],
                label=f"{year} {set_name} {field_name}",
                color=colors.get(year, "grey"),
            )
        )

    p = Plot(series=plot_series, title="Data comparison", legend=True)
    chart_line(plot=p, show=True)


def run_test() -> None:
    date_start = datetime.fromisoformat("2022-08-01T00:00:00+10:00")
    date_end = datetime.fromisoformat("2022-08-30T00:00:00+10:00")

    flows_result = calc_flows_for_range(date_start, date_end, network=NetworkNEM)
    records_new = flows_result[flows_result.index.get_level_values(2) == "NSW1"].reset_index().to_dict("records")

    date_start = date_start.replace(year=2015)
    date_end = date_end.replace(year=2015)

    flows_result = calc_flows_for_range(date_start, date_end, network=NetworkNEM)
    records_old = flows_result[flows_result.index.get_level_values(2) == "NSW1"].reset_index().to_dict("records")
    # records_old = flow_plot(date_start, date_end)

    series = [
        PlotSeries(
            values=[
                PlotIntegerValues(interval=r["trading_interval"].day, value=r["energy_imports"]) for r in records_new
            ],
            label="Imports 2022",
        ),
        PlotSeries(
            values=[
                PlotIntegerValues(interval=r["trading_interval"].day, value=r["energy_imports"]) for r in records_old
            ],
            label="Imports 2015",
            color="g",
        ),
    ]
    p = Plot(series=series, title="Flow comparison", legend=True)
    chart_line(plot=p, show=True)


if __name__ == "__main__":
    # get_aemo_raw_values()
    run_fixture_test("interconnector", "generated", "interconnector_region_from")
    # run_fixture_test("energy", "generated")
