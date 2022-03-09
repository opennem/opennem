"""OpenNEM Network Flows

Creates an aggregate table with network flows (imports/exports), emissions and market_value


Changelog

* 2-MAR - fix blank values and cleanup
* 9-MAR - new version optimized and merged

"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd

from opennem.db import get_database_engine
from opennem.db.models.opennem import AggregateNetworkFlows
from opennem.pipelines.bulk_insert import build_insert_query
from opennem.pipelines.csv import generate_csv_from_records
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_complete_day_for_network

logger = logging.getLogger("opennem.workers.flows")


def load_interconnector_intervals(date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """Load interconnector flows for a date range"""
    engine = get_database_engine()
    network = NetworkNEM

    query = """
        select
            time_bucket_gapfill('1h', fs.trading_interval) as trading_interval,
            f.interconnector_region_from,
            f.interconnector_region_to,
            sum(fs.eoi_quantity) as energy
        from facility_scada fs
        left join facility f
            on fs.facility_code = f.code
        where
            fs.trading_interval >= '{date_start}T00:00:00+10:00'
            and fs.trading_interval < '{date_end}T00:00:00+10:10'
            and f.interconnector is True
            and f.network_id = 'NEM'
        group by 1, 2, 3
        order by
            1 asc;

    """.format(
        date_start=date_start.date(), date_end=date_end.date()
    )

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    logger.debug(query)

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
            sum(t.energy) as energy,
            sum(t.market_value) as market_value,
            sum(t.emissions) as emissions
        from (select
                time_bucket('1 hour', fs.trading_interval) as trading_interval,
                f.network_region as network_region,
                round(coalesce(sum(fs.eoi_quantity), 0), 2) as energy,
                round(coalesce(sum(fs.eoi_quantity), 0) * coalesce(max(bsn.price), 0), 2) as market_value,
                round(coalesce(sum(fs.eoi_quantity), 0) * coalesce(max(f.emissions_factor_co2), 0), 2) as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            left join balancing_summary bsn on
                bsn.trading_interval - INTERVAL '5 minutes' = fs.trading_interval
                and bsn.network_id = n.network_price
                and bsn.network_region = f.network_region
                and f.network_id = 'NEM'
            where
                fs.is_forecast is False and
                f.interconnector = False and
                f.network_id = 'NEM'
            group by
                1, f.code, 2
        )
        as t
        where
            t.trading_interval >= '{date_start}T00:00:00+10:00' and
            t.trading_interval < '{date_end}T00:00:00+10:10'
        group by 1, 2
        order by 1 asc;
    """.format(
        date_start=date_start.date(), date_end=date_end.date()
    )

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    logger.debug(query)

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    df_gen["price"] = df_gen["market_value"] / df_gen["energy"]
    df_gen["emission_factor"] = df_gen["emissions"] / df_gen["energy"]

    return df_gen


def merge_interconnector_and_energy_data(
    df_energy: pd.DataFrame, df_inter: pd.DataFrame
) -> pd.DataFrame:
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

    df_merged_inverted["energy"] *= -1

    f = pd.concat([df_merged, df_merged_inverted])

    f["energy_exports"] = f.apply(lambda x: x.energy if x.energy and x.energy > 0 else 0, axis=1)
    f["energy_imports"] = f.apply(
        lambda x: abs(x.energy) if x.energy and x.energy < 0 else 0, axis=1
    )

    f["emission_exports"] = f.apply(
        lambda x: x.energy * x.emission_factor_to if x.energy and x.energy > 0 else 0, axis=1
    )
    f["emission_imports"] = f.apply(
        lambda x: abs(x.energy * x.emission_factor) if x.energy and x.energy < 0 else 0, axis=1
    )

    energy_flows = pd.DataFrame(
        {
            "energy_imports": f.groupby(
                ["trading_interval", "interconnector_region_from"]
            ).energy_imports.sum(),
            "energy_exports": f.groupby(
                ["trading_interval", "interconnector_region_from"]
            ).energy_exports.sum(),
            "emissions_imports": f.groupby(
                ["trading_interval", "interconnector_region_from"]
            ).emission_imports.sum(),
            "emissions_exports": f.groupby(
                ["trading_interval", "interconnector_region_from"]
            ).emission_exports.sum(),
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

    df_energy = load_energy_emission_mv_intervals(date_start=day, date_end=day_next)

    df_inter = load_interconnector_intervals(date_start=day, date_end=day_next)

    df_flows = merge_interconnector_and_energy_data(df_energy=df_energy, df_inter=df_inter)

    return df_flows


def insert_flows(flow_results: pd.DataFrame) -> int:
    """Takes a list of generation values and calculates energies and bulk-inserts
    into the database"""

    flow_results.reset_index(inplace=True)

    # Add metadata
    flow_results["created_by"] = "opennem.worker.emissions"
    flow_results["created_at"] = ""
    flow_results["updated_at"] = datetime.now()
    flow_results["market_value_imports"] = 0.0
    flow_results["market_value_exports"] = 0.0

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

    if len(records_to_store) < 1:
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
        logger.error("Error inserting records: {}".format(e))
        return 0

    logger.info("Inserted {} records".format(len(records_to_store)))

    return len(records_to_store)


def run_and_store_emission_flows(day: datetime) -> None:
    """Runs and stores emission flows into the aggregate table"""

    try:
        emissions_day = calc_flow_for_day(day)
    except Exception as e:
        logger.error("Flow storage error: {}".format(e))
        return None

    if emissions_day.empty:
        logger.warning("No results for {}".format(day))
        return None

    records_to_store: List[Dict] = emissions_day.to_dict("records")

    logger.debug("Got {} records".format(len(records_to_store)))

    insert_flows(emissions_day)


def run_emission_update_day(
    days: int = 1, day: Optional[datetime] = None, offset_days: int = 1
) -> None:
    """Run emission calcs for number of days"""
    # This is Sydney time as the data is published in local time

    if not day:
        day = get_last_complete_day_for_network(NetworkNEM) - timedelta(days=offset_days)

    current_day = day
    date_min = day - timedelta(days=days)

    while current_day >= date_min:
        logger.info("Running emission update for {}".format(current_day))

        run_and_store_emission_flows(current_day)

        current_day -= timedelta(days=1)


# debug entry point
if __name__ == "__main__":
    logger.info("starting")
    run_emission_update_day(days=60, offset_days=1)
