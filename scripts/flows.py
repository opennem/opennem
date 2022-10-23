#!/usr/bin/env python
""" Script to test OpenNEM flows """
import csv
import logging
from collections import namedtuple
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from itertools import groupby
from pathlib import Path
from pprint import pprint
from textwrap import dedent, indent
from typing import Dict

import pandas as pd
import pydantic
from datetime_truncate import truncate as date_trunc

from opennem.api.stats.schema import ValidNumber, load_opennem_dataset_from_url
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

    for year in [2022, 2019]:
        data[year] = {}

        date_start = datetime.fromisoformat(f"{year}-08-01T00:00:00+10:00")
        date_end = datetime.fromisoformat(f"{year}-09-01T00:00:00+10:00")

        # interconnector data
        # df_inter = get_flow_fixture_dataframe(f"interconnector_intervals_{year}_new.csv")
        df_inter = load_interconnector_intervals(date_start, date_end, network=NetworkNEM)

        # energy data
        df_gen = get_flow_fixture_dataframe(f"energy_set_{year}.csv")
        df_gen["price"] = df_gen["market_value"] / df_gen["generated"]
        df_gen["emission_factor"] = df_gen["emissions"] / df_gen["generated"]

        # emission data
        edf = merge_interconnector_and_energy_data(
            df_energy=df_gen, df_inter=df_inter, scale=NetworkNEM.intervals_per_hour
        ).reset_index()

        # assign objects
        data[year]["interconnector"] = df_inter
        data[year]["energy"] = df_gen
        data[year]["emissions"] = edf

    return data


def part_date(ts: pd.Timestamp | datetime) -> datetime:
    """Convert pandas timestamp to parted datetime"""
    dt = ts if isinstance(ts, (date, datetime)) else ts.to_pydatetime()
    dt = dt.replace(year=2022)
    return dt


def group_values_by_day(df: pd.DataFrame, field_name: str, bucket_size: str) -> list[Dict]:
    """Group values on trading_interval by day"""
    records = df.to_dict("records")

    records_grouped = {}

    for k, v in groupby(records, key=lambda x: date_trunc(x["trading_interval"].to_pydatetime(), bucket_size)):
        if k not in records_grouped:
            records_grouped[k] = 0

        records_grouped[k] += sum(i[field_name] for i in list(v))

    return records_grouped


def run_fixture_test(
    set_name: str = "emissions",
    field_name: str = "energy_imports",
    filter_field: str = "network_region",
    show: bool = False,
    save_plot: bool = False,
    sum_total: bool = False,
    bucket_size: str = "day",
) -> list[PlotSeries]:
    """ """
    data = plot_emissions_from_fixtures()

    plot_series = []

    colors = {2019: "blue", 2022: "red"}

    for year in [2022, 2019]:
        edf = data[year][set_name]
        edf = edf.reset_index()
        series = edf[edf[filter_field] == "NSW1"]

        # write out the entire series
        if not sum_total:
            values = [
                PlotIntegerValues(interval=part_date(r["trading_interval"]), value=r[field_name])
                for r in series.to_dict("records")
            ]

        # if we sum_total then group by bucket_size
        if sum_total:
            values = [
                PlotIntegerValues(interval=part_date(interval) if not bucket_size == "month" else interval, value=value)
                for interval, value in group_values_by_day(series, field_name, bucket_size=bucket_size).items()
            ]

        label = f"{year} {set_name} {field_name} by {bucket_size}" if sum_total else f"{year} {set_name} {field_name}"

        plot_series.append(
            PlotSeries(
                values=values,
                label=label,
                color=colors.get(year, "grey"),
            )
        )

    p = Plot(series=plot_series, title="Data comparison", legend=True)

    is_sum = f"_sum_{bucket_size}" if sum_total else ""
    destination_file = f"notebooks/flows/{set_name}_{field_name}{is_sum}.png" if save_plot else None

    chart_line(plot=p, show=show, destination_file=destination_file)

    return plot_series


def compare_to_net_intervals() -> None:
    """Compare values to net intervals"""
    URL = "https://data.opennem.org.au/v3/stats/au/NEM/NSW1/energy/all.json"

    net_all = load_opennem_dataset_from_url(URL)

    id = "au.nem.nsw1.fuel_tech.imports.energy"

    ds = net_all.get_id(id)

    if not ds or not ds.history:
        raise Exception("No id {id}")

    value_2015 = ds.history.get_date(datetime.fromisoformat("2015-08-01T00:00:00+10:00").date())
    value_2022 = ds.history.get_date(datetime.fromisoformat("2022-08-01T00:00:00+10:00").date())

    print(value_2015, value_2022)

    data = plot_emissions_from_fixtures()
    print(
        data[2015]["emissions"]["energy_imports"].sum() / 1000, data[2022]["emissions"]["energy_imports"].sum() / 1000
    )


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
    chart_line(plot=p, show=True, destination_file="test.png")


def save_charts() -> None:
    run_fixture_test("energy", "generated", save_plot=True)
    run_fixture_test("energy", "price", save_plot=True)
    run_fixture_test("energy", "emission_factor", save_plot=True)

    run_fixture_test("interconnector", "generated", "interconnector_region_from", save_plot=True)

    run_fixture_test("emissions", "energy_imports", save_plot=True)
    # run_fixture_test("emissions", "energy_exports", save_plot=True)
    # run_fixture_test("emissions", "energy_imports", save_plot=True, sum_total=True)
    # run_fixture_test("emissions", "energy_exports", save_plot=True, sum_total=True)

    # run_fixture_test("emissions", "energy_exports", save_plot=True, sum_total=True, bucket_size="month")

    # run_fixture_test("emissions", "emissions_imports", save_plot=True)
    # run_fixture_test("emissions", "emissions_exports", save_plot=True)
    # run_fixture_test("emissions", "emissions_imports", save_plot=True, sum_total=True)
    # run_fixture_test("emissions", "emissions_exports", save_plot=True, sum_total=True)

    # run_fixture_test("emissions", "emission_factor_imports", save_plot=True)
    # run_fixture_test("emissions", "emission_factor_exports", save_plot=True)


if __name__ == "__main__":
    # get_aemo_raw_values()
    save_charts()
    # compare_to_net_intervals()
