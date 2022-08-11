#!/usr/bin/env python
""" Script to test OpenNEM price vs VWP """
import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from textwrap import dedent, indent

import matplotlib.pyplot as plt
import pandas as pd
import pydantic

from opennem.controllers.nem import store_aemo_tableset
from opennem.core.parsers.aemo.mms import AEMOTableSet, parse_aemo_url
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized
from opennem.db import get_database_engine
from opennem.schema.network import NetworkSchema
from opennem.utils.dates import date_series

logger = logging.getLogger("opennem.vwp")

V2_VWP_FIXTURE_PATH = Path(__file__).parent / "vic_daily_vwp_2022_10.csv"

TABLESET_PATH = Path(__file__).parent / "aemo_demand_price_data_tableset.json"

COMPARISON_START_DATE = datetime.fromisoformat("2022-01-01T00:00:00")

COMPARISON_END_DATE = datetime.fromisoformat("2022-01-31:00:00")


@dataclass
class VWPBucket:
    interval: date
    value: float


def read_vwp_data_fixture() -> list[VWPBucket]:
    records: list[VWPBucket] = []

    with open(V2_VWP_FIXTURE_PATH) as fh:
        csvreader = csv.DictReader(fh)
        for record in csvreader:
            model = VWPBucket(interval=datetime.strptime(record.get("interval"), "%Y-%m-%d"), value=record.get("value"))

            records.append(model)

    logger.debug(f"Got {len(records)} fixture values")

    return records


# network: NetworkSchema, network_region: str | None, date_from: datetime, date_to: datetime
def get_vwp_query() -> str:
    """Gets a vwp query"""

    __query = """
        select
            date_trunc('day', fs.trading_interval at time zone n.timezone_database) as trading_day,
            fs.network_id,
            fs.network_region,
            sum(fs.energy) as energy,
            sum(fs.market_value) as market_value,
            sum(fs.market_value) / sum(fs.energy) as price
        from (
            select
                time_bucket_gapfill('5 minutes', bs.trading_interval) as trading_interval,
                bs.network_id,
                bs.network_region,
                (sum(bs.demand_total) / 12000) as energy,
                (sum(bs.demand_total) / 12000) * max(bs.price_dispatch) as market_value
            from balancing_summary bs
            where
                bs.network_id = 'NEM'
                and bs.network_region = 'VIC1'
                and bs.trading_interval >= '{date_start}'
                and bs.trading_interval <= '{date_end}'
            group by
                1, 2, 3
        ) as fs
        left join network n on fs.network_id = n.code
        group by
            1, 2, 3
        order by 1 asc;
    """

    return dedent(__query.format(date_start=COMPARISON_START_DATE, date_end=COMPARISON_END_DATE))


def get_server_vwp() -> list[VWPBucket]:
    """Gets the VWP"""
    engine = get_database_engine()
    query = get_vwp_query()

    with engine.begin() as conn:
        logger.info(query)
        results = list(conn.execute(query))

    result_models = [VWPBucket(interval=i[0], value=i[5]) for i in results]

    logger.debug(f"Got {len(result_models)} results from server")

    return result_models


def compare_vwp() -> list[VWPBucket]:
    fixture_values = read_vwp_data_fixture()
    server_values = get_server_vwp()

    delta_models: list[VWPBucket] = []

    matching_intervals = 0

    for fixture_val in fixture_values:
        server_val = list(filter(lambda x: x.interval == fixture_val.interval, server_values))

        if not server_val:
            logger.error(f"Could not find {fixture_val.interval} in server values")
            continue

        server_interval = server_val.pop()

        if server_interval.value != fixture_val.value:
            logger.error(
                f"{fixture_val.interval}: {fixture_val.value} does not match {server_interval.value} {server_interval.interval}"
            )
        else:
            matching_intervals += 1

        delta_model = VWPBucket(
            interval=fixture_val.interval, value=float(fixture_val.value) - float(server_interval.value or 0)
        )

        delta_models.append(delta_model)

    logger.info(f"Got {matching_intervals:=}")

    return delta_models


def plot_deltas(deltas: list[VWPBucket], destination_file: str = "vwp_deltas.png") -> None:
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


def get_aemo_raw_values(persist: bool = True) -> AEMOTableSet:
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
        # older
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220206_20220212.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220213_20220219.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220220_20220226.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220227_20220305.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220306_20220312.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220213_20220219.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220220_20220226.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220227_20220305.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220306_20220312.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220313_20220319.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220320_20220326.zip",
        # "https://nemweb.com.au/Reports/Archive/TradingIS_Reports/PUBLIC_TRADINGIS_20220327_20220402.zip",
    ]

    # urls += trading_is_urls

    ts = AEMOTableSet()

    # This will iterate through the URLs, parse them and add them to the AEMOTableSet
    for u in trading_is_urls:
        ts = parse_aemo_url_optimized(u, table_set=ts, persist_to_db=False, values_only=True)

    if not persist:
        return ts

    with open(TABLESET_PATH, "w") as fh:
        fh.write(ts.json(indent=4))

    logger.info(f"Wrote table_set to file {TABLESET_PATH}")

    return ts


def get_aemo_tableset() -> AEMOTableSet:
    """Reads the stored tableset fixture path and returns an AEMOTableSet"""
    ts = pydantic.parse_file_as(path=str(TABLESET_PATH), type_=AEMOTableSet)
    return ts


if __name__ == "__main__":
    get_aemo_raw_values()

    ts = get_aemo_tableset()

    csv_path = Path(__file__).parent.parent / "notebooks" / "data"

    for table in ts.tables:
        print(f"Have table {table.full_name}")
        table.to_csv(str(csv_path / f"{table.full_name}.csv"))

    # delta_models = compare_vwp()
    # plot_deltas(delta_models)

    # ts = pydantic.parse_file_as(path=str(fn), type_=AEMOTableSet)
    # ts = read_aemo_dispatchis()
    # print(ts.tables)
