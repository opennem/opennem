#!/usr/bin/env python
""" Script to test OpenNEM price vs VWP """
import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

from sqlalchemy import text as sql

from opennem.db import get_database_engine
from opennem.schema.network import NetworkNEM, NetworkSchema

vwp_data_fixture = Path(__file__).parent / "vic_daily_vwp_2022.csv"

logger = logging.getLogger("openne.vwp")


@dataclass
class VWPBucket:
    interval: date
    value: float


def read_vwp_data_fixture() -> list[VWPBucket]:
    records: list[VWPBucket] = []

    with open(vwp_data_fixture) as fh:
        csvreader = csv.DictReader(fh)
        for record in csvreader:
            model = VWPBucket(interval=datetime.strptime(record.get("interval"), "%Y-%m-%d"), value=record.get("value"))

            records.append(model)

    return records


def get_vwp_query(network: NetworkSchema, network_region: str | None, date_from: datetime, date_to: datetime) -> str:
    """Gets a vwp query"""

    query = """
        select
            date_trunc('day', fs.trading_interval at time zone n.timezone_database) as trading_day,
            fs.network_id,
            fs.network_region,
            round(sum(fs.energy), 2) as energy,
            round(sum(fs.vwp), 2) as vwp,
            round(sum(fs.vwp) / sum(fs.energy), 2) as price
        from (
            select
                time_bucket_gapfill('5 minutes', fs.trading_interval) as trading_interval,
                fs.network_id,
                f.network_region,
                (sum(bs.demand_total) / 12000) as energy,
                (sum(bs.demand_total) / 12000) * max(bs.price) as vwp
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on fs.network_id = n.code
            left join balancing_summary bs on
                bs.trading_interval - INTERVAL '5 minutes' = fs.trading_interval
                and bs.network_id = n.network_price
                and bs.network_region = f.network_region
                and fs.network_id = 'NEM'
            where
                fs.is_forecast is False
                and fs.network_id = 'NEM'
                and bs.network_region = 'VIC1'
                and fs.trading_interval >= '2022-01-01T00:00:00+10:00'
                and fs.trading_interval < '2022-01-10T00:00:00+10:00'
            group by
                1, 2, 3
        ) as fs
        left join network n on fs.network_id = n.code
        group by
            1, 2, 3
        order by 1 asc
    """

    return dedent(query)


def get_vwp() -> None:
    """Gets the VWP"""
    engine = get_database_engine()

    fixture_values = read_vwp_data_fixture()

    print(fixture_values)


if __name__ == "__main__":
    get_vwp()
