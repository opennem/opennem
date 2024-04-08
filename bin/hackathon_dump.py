#!/usr/bin/env python
"""Export data for the hackathon"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import polars as pl

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.hackathon_dump")
logger.setLevel(logging.DEBUG)

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "hackathon_data"

if not OUTPUT_DIR.exists():
    raise Exception(f"Output directory {OUTPUT_DIR} does not exist")


@dataclass
class OpenNEMDataExport:
    query: str
    file_name: str


def get_facility_scada_query(date_start: datetime, date_end: datetime) -> str:
    return f"""
        select
            fs.trading_interval at time zone 'AEST' as trading_interval
            ,fs.facility_code
            ,fs.generated as generated_mw
        from facility_scada fs
        left join facility f on fs.facility_code = f.code
        where
            f.network_region = 'SA1'
            and fs.is_forecast is False
            and f.network_id in ('NEM', 'AEMO_ROOFTOP')
            and fs.trading_interval >= '{date_start}'
            and fs.trading_interval < '{date_end}'
        order by 1, 2
    """.format(date_start=date_start, date_end=date_end)


def get_price_and_demand_data(date_start: datetime, date_end: datetime) -> str:
    return f"""
    select
        bs.trading_interval at time zone 'AEST' as trading_interval
        ,coalesce(bs.price_dispatch, bs.price, NULL) as price
        ,bs.demand
        ,bs.demand_total
    from balancing_summary bs
    where
        bs.network_id = 'NEM'
        and bs.network_region = 'SA1'
        and bs.is_forecast is False
        and bs.trading_interval >= '{date_start}'
        and bs.trading_interval < '{date_end}'
        order by 1;
    """.format(date_start=date_start, date_end=date_end)


def get_weather_data(date_start: datetime, date_end: datetime) -> str:
    return f"""
        select
            observation_time as trading_interval,
            fs.station_id as station_id,
            avg(fs.temp_air) as temp_air,
            min(fs.temp_air) as temp_min,
            max(fs.temp_air) as temp_max
        from bom_observation fs
        where
            fs.station_id = '023000'
            and fs.observation_time >= '{date_start}'
            and fs.observation_time < '{date_end}'
        group by 1, 2
        order by 1;
    """


def get_import_export_data(date_start: datetime, date_end: datetime) -> str:
    return f"""
        select
            fs.trading_interval at time zone 'AEST' as trading_interval
            ,case when sum(fs.generated) >= 0 then
                abs(sum(fs.generated))
            else 0 end as exports
            ,case when sum(fs.generated) < 0 then
                abs(sum(fs.generated) )
            else 0 end as imports
        from facility_scada fs
        left join facility f on f.code = fs.facility_code
        where
            1=1
            and f.interconnector_region_to = 'SA1'
            and f.interconnector is True
            and f.network_id in ('NEM')
            and fs.trading_interval >= '{date_start}'
            and fs.trading_interval < '{date_end}'
        group by 1, f.interconnector_region_to
        order by 1 asc;
    """


def get_pre_dispatch_data(date_start: datetime, date_end: datetime) -> str:
    return """
        select

                fs.trading_interval at time zone 'AEST' as trading_interval
                ,fs.network_id
    """


def run_and_export_query(query: str, filename: str) -> None:
    engine = get_database_engine()

    with engine.connect() as conn:
        df = pl.read_database(query, conn, schema_overrides={})
        logger.debug(f"Loaded data frame for {filename} with {df.shape=}")

        destination_filename = str(OUTPUT_DIR / f"{filename}.parquet")
        df.write_parquet(destination_filename)
        logger.info(f"Wrote to {destination_filename}")


if __name__ == "__main__":
    date_start = datetime.fromisoformat("2021-01-01T00:00:00+10:00")
    # date_start = datetime.fromisoformat("2023-12-01T00:00:00+10:00")
    date_end = datetime.fromisoformat("2024-01-01T00:00:00+10:00")

    EXPORTS = [
        # OpenNEMDataExport(query=get_facility_scada_query(date_start, date_end), file_name="generation_data"),
        # OpenNEMDataExport(query=get_price_and_demand_data(date_start, date_end), file_name="price_and_demand_data"),
        # OpenNEMDataExport(query=get_weather_data(date_start, date_end), file_name="weather_data"),
        OpenNEMDataExport(query=get_import_export_data(date_start, date_end), file_name="flow_data"),
    ]

    for export in EXPORTS:
        logger.info(f"Running and exporting {export.file_name}")
        run_and_export_query(export.query, export.file_name)
