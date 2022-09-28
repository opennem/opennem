"""OpenNEM Network Flows

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

Changelog

* 2-MAR - fix blank values and cleanup
* 9-MAR - new version optimized and merged
* 15-MAR - alter bucket times
* 21-MAR - various bug fixes for older dates

"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from opennem import settings
from opennem.db import get_database_engine
from opennem.db.bulk_insert_csv import build_insert_query, generate_csv_from_records
from opennem.db.models.opennem import AggregateNetworkFlows
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_last_complete_day_for_network, get_today_nem

logger = logging.getLogger("opennem.workers.flows")


class FlowWorkerException(Exception):
    pass


def load_interconnector_intervals(
    date_start: datetime, date_end: datetime, network: NetworkSchema | None = None
) -> pd.DataFrame:
    """Load interconnector flows for a date range"""
    engine = get_database_engine()

    # default to NEM
    if not network:
        network = NetworkNEM

    if date_start >= date_end:
        raise FlowWorkerException("load_interconnector_intervals: date_start is more recent than date_end")

    query = """
        select
            time_bucket_gapfill('5min', fs.trading_interval) as trading_interval,
            f.interconnector_region_from,
            f.interconnector_region_to,
            coalesce(sum(fs.generated), 0) as generated
        from facility_scada fs
        left join facility f
            on fs.facility_code = f.code
        where
            fs.trading_interval >= '{date_start}T00:00:00{offset}'
            and fs.trading_interval < '{date_end}T00:00:00{offset}'
            and f.interconnector is True
            and f.network_id = '{network_id}'
        group by 1, 2, 3
        order by
            1 asc;

    """.format(
        date_start=date_start.date(),
        date_end=date_end.date(),
        offset=network.get_offset_string(),
        network_id=network.code,
    )

    logger.debug(query)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    return df_gen


def load_energy_emission_mv_intervals(date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """Fetch all emission, market value and emission intervals by network region"""

    engine = get_database_engine()
    network = NetworkNEM

    query = """
        select
            t.trading_interval,
            t.network_region,
            sum(t.power) as generated,
            sum(t.market_value) as market_value,
            sum(t.emissions) as emissions
        from
        (
            select
                fs.trading_interval as trading_interval,
                f.network_region as network_region,
                sum(fs.generated) as power,
                sum(fs.generated) * max(bsn.price) as market_value,
                sum(fs.generated) * max(f.emissions_factor_co2) as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            left join (
                select
                    time_bucket_gapfill('5 min', bs.trading_interval) as trading_interval,
                    bs.network_id,
                    bs.network_region,
                    locf(bs.price) as price
                from balancing_summary bs
                    where bs.network_id='NE{network_id}M'
            ) as  bsn on
                bsn.trading_interval = fs.trading_interval
                and bsn.network_id = n.network_price
                and bsn.network_region = f.network_region
                and f.network_id = '{network_id}'
            where
                fs.is_forecast is False and
                f.interconnector = False and
                f.network_id = '{network_id}' and
                fs.generated > 0
            group by
                1, f.code, 2
        ) as t
        where
            t.trading_interval >= '{date_start}T00:00:00{offset}' and
            t.trading_interval < '{date_end}T00:00:00{offset}'
        group by 1, 2
        order by 1 asc, 2;
    """.format(
        date_start=date_start.date(),
        date_end=date_end.date(),
        network_id=network.code,
        offset=network.get_offset_string(),
    )

    logger.debug(query)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    df_gen["price"] = df_gen["market_value"] / df_gen["generated"]
    df_gen["emission_factor"] = df_gen["emissions"] / df_gen["generated"]

    return df_gen


def merge_interconnector_and_energy_data(df_energy: pd.DataFrame, df_inter: pd.DataFrame) -> pd.DataFrame:
    """Merge the dataframes and break down into simple frame"""

    region_from = pd.merge(
        df_inter,
        df_energy,
        how="left",
        left_on=["trading_interval", "interconnector_region_from"],
        right_on=["trading_interval", "network_region"],
        suffixes=("", "_from"),
    )

    df_merged = pd.merge(
        region_from,
        df_energy,
        how="left",
        left_on=["trading_interval", "interconnector_region_to"],
        right_on=["trading_interval", "network_region"],
        suffixes=("", "_to"),
    )

    df_merged_inverted = df_merged.rename(
        columns={
            "interconnector_region_from": "interconnector_region_to",
            "interconnector_region_to": "interconnector_region_from",
        }
    )

    df_merged_inverted["generated"] *= -1

    f = pd.concat([df_merged, df_merged_inverted])

    f["energy_exports"] = f.apply(lambda x: x.generated if x.generated and x.generated > 0 else 0, axis=1)
    f["energy_imports"] = f.apply(lambda x: abs(x.generated) if x.generated and x.generated < 0 else 0, axis=1)

    f["emission_exports"] = f.apply(
        lambda x: x.generated * x.emission_factor_to if x.generated and x.generated > 0 else 0,
        axis=1,
    )
    f["emission_imports"] = f.apply(
        lambda x: abs(x.generated * x.emission_factor) if x.generated and x.generated < 0 else 0,
        axis=1,
    )

    f["market_value_exports"] = f.apply(
        lambda x: x.generated * x.price_to if x.generated and x.generated > 0 else 0, axis=1
    )

    f["market_value_imports"] = f.apply(
        lambda x: abs(x.generated * x.price) if x.generated and x.generated < 0 else 0, axis=1
    )

    energy_flows = pd.DataFrame(
        {
            "energy_imports": f.groupby(["trading_interval", "interconnector_region_from"]).energy_imports.sum() / 12,
            "energy_exports": f.groupby(["trading_interval", "interconnector_region_from"]).energy_exports.sum() / 12,
            "emissions_imports": f.groupby(["trading_interval", "interconnector_region_from"]).emission_imports.sum()
            / 12,
            "emissions_exports": f.groupby(["trading_interval", "interconnector_region_from"]).emission_exports.sum()
            / 12,
            "market_value_imports": f.groupby(
                ["trading_interval", "interconnector_region_from"]
            ).market_value_imports.sum()
            / 12,
            "market_value_exports": f.groupby(
                ["trading_interval", "interconnector_region_from"]
            ).market_value_exports.sum()
            / 12,
        }
    )

    energy_flows["network_id"] = "NEM"

    energy_flows.reset_index(inplace=True)
    energy_flows.rename(columns={"interconnector_region_from": "network_region"}, inplace=True)
    energy_flows.set_index(["trading_interval", "network_id", "network_region"], inplace=True)

    return energy_flows


def calc_flow_for_day(day: datetime) -> pd.DataFrame:
    """For a particular day calculate all flow values"""
    day_next = day + timedelta(days=1)

    df_inter = load_interconnector_intervals(date_start=day, date_end=day_next)

    df_energy = load_energy_emission_mv_intervals(date_start=day, date_end=day_next)

    return merge_interconnector_and_energy_data(df_energy=df_energy, df_inter=df_inter)


def calc_flows_for_range(date_start: datetime, date_end: datetime, network: NetworkSchema) -> pd.DataFrame:
    """For a particular day calculate all flow values"""

    df_inter = load_interconnector_intervals(date_start=date_start, date_end=date_end, network=network)

    df_energy = load_energy_emission_mv_intervals(date_start=date_start, date_end=date_end, network=network)

    return merge_interconnector_and_energy_data(df_energy=df_energy, df_inter=df_inter)


def insert_flows(flow_results: pd.DataFrame) -> int:
    """Takes a list of generation values and calculates energies and bulk-inserts
    into the database"""

    datetime_now = datetime.now()

    flow_results.reset_index(inplace=True)

    # Add metadata
    flow_results["created_by"] = "opennem.worker.emissions"
    flow_results["created_at"] = ""
    flow_results["updated_at"] = datetime_now

    # # reorder columns
    columns = [
        "trading_interval",
        "network_id",
        "network_region",
        "energy_imports",
        "energy_exports",
        "emissions_imports",
        "emissions_exports",
        "market_value_imports",
        "market_value_exports",
        "created_by",
        "created_at",
        "updated_at",
    ]
    flow_results = flow_results[columns]

    records_to_store: List[Dict] = flow_results.to_dict("records")

    if not records_to_store:
        logger.error("No records returned from energy sum")
        return 0

    # Build SQL + CSV and bulk-insert
    sql_query = build_insert_query(
        AggregateNetworkFlows,  # type: ignore
        [
            "energy_imports",
            "energy_exports",
            "emissions_imports",
            "emissions_exports",
            "market_value_imports",
            "market_value_exports",
        ],
    )
    conn = get_database_engine().raw_connection()
    cursor = conn.cursor()

    csv_content = generate_csv_from_records(
        AggregateNetworkFlows,  # type: ignore
        records_to_store,
        column_names=list(records_to_store[0].keys()),
    )

    try:
        cursor.copy_expert(sql_query, csv_content)
        conn.commit()
    except Exception as e:
        logger.error(f"Error inserting records: {e}")
        return 0

    logger.info(f"Inserted {len(records_to_store)} records")

    return len(records_to_store)


def run_and_store_emission_flows(day: datetime) -> None:
    """Runs and stores emission flows into the aggregate table"""

    try:
        emissions_day = calc_flow_for_day(day)
    except Exception as e:
        logger.error(f"Flow storage error: {e}")
        return None

    if emissions_day.empty:
        logger.warning(f"No results for {day}")
        return None

    records_to_store: List[Dict] = emissions_day.to_dict("records")

    logger.debug(f"Got {len(records_to_store)} records")

    insert_flows(emissions_day)


def run_and_store_flows_for_range(
    date_start: datetime, date_end: datetime, network: NetworkSchema | None = None
) -> None:
    """Runs and stores emission flows into the aggregate table"""

    if not network:
        network = NetworkNEM

    try:
        emissions_day = calc_flows_for_range(date_start, date_end, network=network)
    except Exception as e:
        logger.error(f"Flow storage error: {e}")
        return None

    if emissions_day.empty:
        logger.warning(f"No results for {date_start} => {date_end}")
        return None

    records_to_store: List[Dict] = emissions_day.to_dict("records")

    logger.debug(f"Got {len(records_to_store)} records")

    insert_flows(emissions_day)


def run_emission_update_day(days: int = 1, day: Optional[datetime] = None, offset_days: int = 1) -> None:
    """Run emission calcs for number of days"""
    # This is Sydney time as the data is published in local time

    if not day:
        day = get_last_complete_day_for_network(NetworkNEM)

    current_day = day

    if offset_days > 1:
        current_day -= timedelta(days=offset_days)

    date_min = day - timedelta(days=days)

    run_and_store_flows_for_range(date_min, current_day)


def run_flow_updates_for_date_range(date_start: datetime, date_end: datetime) -> None:
    """Run emission calcs for a range of daytes"""
    current_day = date_start

    while current_day >= date_end:
        logger.info(f"Running emission update for {current_day}")

        run_and_store_emission_flows(current_day)

        current_day -= timedelta(days=1)


def run_flow_updates_all_per_year(year_start: int, years: int = 1, network: NetworkSchema | None = None) -> None:
    """Run emission flow updates by year"""

    # default to NEM for now with no param
    if not network:
        network = NetworkNEM

    for year in range(year_start, year_start - years, -1):
        date_start = datetime.fromisoformat(f"{year}-01-01T00:00:00+10:00")
        date_end = datetime.fromisoformat(f"{year}-12-31T00:00:00+10:00") + timedelta(days=1)

        today_nem = get_today_nem()

        if date_end > today_nem:
            date_end = today_nem + timedelta(days=1)

        if network.data_first_seen and year == network.data_first_seen.year:
            date_start = network.data_first_seen

        if network.data_first_seen and year < network.data_first_seen.year:
            logger.info(f"Skipping year {year} since it is earler than earliest date {network.data_first_seen}")
            continue

        if network.data_first_seen and date_start < network.data_first_seen:
            date_start = network.data_first_seen

        logger.info(f"Running flow_updates_per_year for {year} ({date_start} => {date_end})")

        if not settings.dry_run:
            run_and_store_flows_for_range(
                date_start,
                date_end,
            )


def run_flow_updates_all_for_network(network: NetworkSchema) -> None:
    """Run the entire emissions flow for a network"""
    current_year = datetime.now().year

    if not network.data_first_seen:
        raise FlowWorkerException(f"No data first seen for network {network.code}")

    for year in range(current_year, network.data_first_seen.year - 1, -1):
        run_flow_updates_all_per_year(year, network=network)


# debug entry point
if __name__ == "__main__":
    logger.info("starting")
    run_flow_updates_all_for_network(network=NetworkNEM)
    # run_emission_update_day(days=12)
    # run_flow_updates_all_per_year(datetime.now().year, 1)
