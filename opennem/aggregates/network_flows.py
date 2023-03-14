"""OpenNEM Network Flows

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

Changelog

* 2-MAR - fix blank values and cleanup
* 9-MAR - new version optimized and merged
* 15-MAR - alter bucket times
* 21-MAR - various bug fixes for older dates
* Nov - Update to run per-interval so the result can be used in power data

"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from opennem.core.profiler import ProfilerLevel, ProfilerRetentionTime, profile_task
from opennem.db import get_database_engine
from opennem.db.bulk_insert_csv import build_insert_query, generate_csv_from_records
from opennem.db.models.opennem import AggregateNetworkFlows
from opennem.queries.flows import get_interconnector_intervals_query
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.settings import settings
from opennem.utils.dates import get_last_complete_day_for_network, get_last_completed_interval_for_network, is_aware

logger = logging.getLogger("opennem.aggregates.flows")


class FlowWorkerException(Exception):
    pass


def load_interconnector_intervals(date_start: datetime, date_end: datetime, network: NetworkSchema | None = None) -> pd.DataFrame:
    """Load interconnector flows for a date range"""
    engine = get_database_engine()

    # default to NEM
    if not network:
        network = NetworkNEM

    if date_start >= date_end:
        raise FlowWorkerException("load_interconnector_intervals: date_start is more recent than date_end")

    query = get_interconnector_intervals_query(date_start=date_start, date_end=date_end, network=network)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    return df_gen


def load_energy_emission_mv_intervals(date_start: datetime, date_end: datetime, network: NetworkSchema) -> pd.DataFrame:
    """Fetch all emission, market value and emission intervals by network region"""

    engine = get_database_engine()

    if not is_aware(date_start):
        date_start = date_start.astimezone(tz=network.get_fixed_offset())

    if not is_aware(date_end):
        date_end = date_end.astimezone(tz=network.get_fixed_offset())

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
                coalesce(sum(fs.generated) * max(bsn.price), 0) as market_value,
                coalesce(sum(fs.generated) * max(f.emissions_factor_co2), 0) as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            left join (
                select
                    bs.trading_interval as trading_interval,
                    bs.network_id,
                    bs.network_region,
                    bs.price as price
                from balancing_summary bs
                    where bs.network_id='{network_id}'
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
            t.trading_interval >= '{date_start}' and
            t.trading_interval < '{date_end}'
        group by 1, 2
        order by 1 asc, 2;
    """.format(
        date_start=date_start, date_end=date_end, network_id=network.code
    )

    logger.debug(query)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    df_gen["price"] = df_gen["market_value"] / df_gen["generated"]
    df_gen["emission_factor"] = df_gen["emissions"] / df_gen["generated"]

    return df_gen


def calculate_flow_for_interval(df_energy_and_emissions: pd.DataFrame, df_interconnector: pd.DataFrame) -> pd.DataFrame:
    """Calculate the flow for a given interval

    df_energy_and_emissions:
        generation and emissions data for each network region
            - energy (MWh)
            - emissions (tCO2)
    df_interconnector:
        interconnector data for each regional flow direction energy that is
            - energy (MWh)

    returns
        a dataframe for each region with the following columns
            - emissions imported (tCO2)
            - emissions exported (tCO2)

    """
    pass


def merge_interconnector_and_energy_data(df_energy: pd.DataFrame, df_inter: pd.DataFrame, scale: int) -> pd.DataFrame:
    """Merge the dataframes and break down into simple frame

    params:
        df_energy: energy data
        df_inter: interconnector data

    """

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

    f["energy_exports"] = f.apply(lambda x: x.generated if x.generated and x.generated >= 0 else 0, axis=1)
    f["energy_imports"] = f.apply(lambda x: x.generated if x.generated and x.generated <= 0 else 0, axis=1)

    # f["emission_exports"] = f.apply(
    #     lambda x: x.energy_exports * x.emission_factor_to if x.generated and x.generated >= 0 else 0,
    #     axis=1,
    # )
    # f["emission_imports"] = f.apply(
    #     lambda x: x.energy_imports * x.emission_factor if x.generated and x.generated <= 0 else 0,
    #     axis=1,
    # )

    # @NOTE bad hack for issue 144 TAS1 specific
    # https://github.com/opennem/opennem/issues/144
    f["emission_exports"] = f.apply(
        lambda x: x.energy_exports * x.emission_factor
        if x.generated and x.generated >= 0 and x.network_region == "TAS1"
        else x.energy_imports * x.emission_factor_to,
        axis=1,
    )
    f["emission_imports"] = f.apply(
        lambda x: x.energy_imports * x.emission_factor_to
        if x.generated and x.generated <= 0 and x.network_region == "TAS1"
        else x.energy_imports * x.emission_factor,
        axis=1,
    )

    f["market_value_exports"] = f.apply(lambda x: x.generated * x.price_to if x.generated and x.generated >= 0 else 0, axis=1)
    f["market_value_imports"] = f.apply(lambda x: x.generated * x.price if x.generated and x.generated <= 0 else 0, axis=1)

    energy_flows = pd.DataFrame(
        {
            "energy_imports": f.groupby(["trading_interval", "interconnector_region_from"]).energy_imports.sum() / scale,
            "energy_exports": f.groupby(["trading_interval", "interconnector_region_from"]).energy_exports.sum() / scale,
            "emissions_imports": f.groupby(["trading_interval", "interconnector_region_from"]).emission_imports.sum() / scale,
            "emissions_exports": f.groupby(["trading_interval", "interconnector_region_from"]).emission_exports.sum() / scale,
            "market_value_imports": f.groupby(["trading_interval", "interconnector_region_from"]).market_value_imports.sum()
            / scale,
            "market_value_exports": f.groupby(["trading_interval", "interconnector_region_from"]).market_value_exports.sum()
            / scale,
        }
    )

    # include factors
    energy_flows["emission_factor_imports"] = energy_flows["emissions_imports"] / energy_flows["energy_imports"]
    energy_flows["emission_factor_exports"] = energy_flows["emissions_exports"] / energy_flows["energy_exports"]

    energy_flows["network_id"] = "NEM"

    energy_flows.reset_index(inplace=True)
    energy_flows.rename(columns={"interconnector_region_from": "network_region"}, inplace=True)
    energy_flows.set_index(["trading_interval", "network_id", "network_region"], inplace=True)

    return energy_flows


def calc_flow_for_day(day: datetime, network: NetworkSchema) -> pd.DataFrame:
    """For a particular day calculate all flow values"""
    day_next = day + timedelta(days=1)
    df_inter = load_interconnector_intervals(date_start=day, date_end=day_next, network=network)

    df_energy = load_energy_emission_mv_intervals(date_start=day, date_end=day_next, network=network)

    return merge_interconnector_and_energy_data(df_energy=df_energy, df_inter=df_inter, scale=int(network.intervals_per_hour))


def calc_flows_for_range(date_start: datetime, date_end: datetime, network: NetworkSchema) -> pd.DataFrame:
    """For a particular day calculate all flow values"""

    df_inter = load_interconnector_intervals(date_start=date_start, date_end=date_end, network=network)

    df_energy = load_energy_emission_mv_intervals(date_start=date_start, date_end=date_end, network=network)

    return merge_interconnector_and_energy_data(df_energy=df_energy, df_inter=df_inter, scale=int(network.intervals_per_hour))


def insert_flows(flow_results: pd.DataFrame) -> int:
    """Takes a list of generation values and calculates energies and bulk-inserts
    into the database"""

    datetime_now = datetime.now()

    flow_results.reset_index(inplace=True)

    # Add metadata
    flow_results["created_by"] = "opennem.worker.emissions"
    flow_results["created_at"] = datetime_now
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

    records_to_store: list[dict] = flow_results.to_dict("records")

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
            "updated_at",
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
        logger.debug(sql_query)
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
        emissions_day = calc_flow_for_day(day, network=NetworkNEM)
    except Exception as e:
        logger.exception(f"Flow storage error: {e}")
        raise Exception("flow storage error")

    if emissions_day.empty:
        logger.warning(f"No results for {day}")
        raise Exception("No results")

    records_to_store: list[dict] = emissions_day.to_dict("records")

    logger.debug(f"Got {len(records_to_store)} records")

    insert_flows(emissions_day)


def run_and_store_flows_for_range(date_start: datetime, date_end: datetime, network: NetworkSchema | None = None) -> int | None:
    """Runs and stores emission flows into the aggregate table"""

    if not network:
        network = NetworkNEM

    try:
        emissions_day = calc_flows_for_range(date_start, date_end, network=network)
    except Exception as e:
        logger.exception(f"Flow storage error: {e}")
        return None

    if emissions_day.empty:
        logger.warning(f"No results for {date_start} => {date_end}")
        return None

    records_to_store: list[dict] = emissions_day.to_dict("records")

    logger.debug(f"Got {len(records_to_store)} records")

    inserted_records = insert_flows(emissions_day)

    return inserted_records


@profile_task(
    send_slack=True,
    level=ProfilerLevel.INFO,
    retention_period=ProfilerRetentionTime.MONTH,
    message_fmt="`{network.code}`: Ran flow update for interval `{interval}`",
)
def run_flow_update_for_interval(
    interval: datetime, network: NetworkSchema | None = None, number_of_intervals: int = 1
) -> int | None:
    """Runs and stores emission flows for a particular interval"""

    if not network:
        network = NetworkNEM

    date_end = interval
    date_start = interval - timedelta(minutes=network.interval_size) * number_of_intervals

    return run_and_store_flows_for_range(date_start, date_end, network=network)


@profile_task(
    send_slack=False,
    message_fmt="Ran emission update for day {day}",
    level=ProfilerLevel.INFO,
    retention_period=ProfilerRetentionTime.FOREVER,
)
def run_emission_update_day(days: int = 1, day: datetime | None = None, offset_days: int = 1) -> None:
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


@profile_task(
    send_slack=True,
    message_fmt="Ran flow updated all for last year",
    level=ProfilerLevel.INFO,
    retention_period=ProfilerRetentionTime.FOREVER,
)
def run_flow_updates_all_per_year(year_start: int, years: int = 1, network: NetworkSchema | None = None) -> None:
    """Run emission flow updates by year"""

    # default to NEM for now with no param
    if not network:
        network = NetworkNEM

    for year in range(year_start, year_start - years, -1):
        date_start = datetime.fromisoformat(f"{year}-01-01T00:00:00+10:00")
        date_end = datetime.fromisoformat(f"{year}-12-31T00:00:00+10:00") + timedelta(days=1)

        today_nem = get_last_completed_interval_for_network(network=network)

        if date_end > today_nem:
            date_end = today_nem

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


def run_flow_updates_all_for_network(network: NetworkSchema, to_year: int | None = None) -> None:
    """Run the entire emissions flow for a network"""
    current_year = datetime.now().year

    if not network.data_first_seen:
        raise FlowWorkerException(f"No data first seen for network {network.code}")

    for year in range(current_year, to_year or network.data_first_seen.year - 1, -1):
        run_flow_updates_all_per_year(year, network=network)


# debug entry point
if __name__ == "__main__":
    logger.info("starting")
    # run_flow_updates_all_for_network(network=NetworkNEM, to_year=2020)
    # run_emission_update_day(days=12)
    # run_flow_updates_all_per_year(2014, 1, network=NetworkNEM)
    # run_flow_update_for_interval(datetime.fromisoformat("2022-11-18T14:40:00+10:00"), network=NetworkNEM)
    run_flow_update_for_interval(
        interval=datetime.fromisoformat("2023-03-07T00:00:00+10:00"), network=NetworkNEM, number_of_intervals=1
    )
