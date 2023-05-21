"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from opennem.core.flow_solver import solve_flows_for_interval
from opennem.db import get_database_engine
from opennem.db.bulk_insert_csv import build_insert_query, generate_csv_from_records
from opennem.db.models.opennem import AggregateNetworkFlows
from opennem.queries.flows import get_interconnector_intervals_query
from opennem.schema.network import NetworkNEM, NetworkSchema

logger = logging.getLogger("opennem.aggregates.flows_v3")


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


def load_energy_and_emissions_for_intervals(
    interval_start: datetime, interval_end: datetime, network: NetworkSchema
) -> pd.DataFrame:
    """
    Fetch all energy and emissions for each network region for a network.

    Non-inclusive of interval_end.

    Args:
        interval_start (datetime): Start of the interval.
        interval_end (datetime): End of the interval.
        network (NetworkSchema): Network schema object.

    Returns:
        pd.DataFrame: DataFrame containing energy and emissions data for each network region.
            Columns:
                - trading_interval (datetime): Trading interval.
                - network_id (str): Network ID.
                - network_region (str): Network region.
                - energy (float): Sum of energy.
                - emissions (float): Sum of emissions.
                - emission_intensity (float): Emission intensity.

    Raises:
        FlowWorkerException: If no results are obtained from load_interconnector_intervals.

    @TODO remove pandas dependency
    """

    engine = get_database_engine()

    query = """
        select
            generated_intervals.trading_interval,
            generated_intervals.network_id,
            generated_intervals.network_region,
            sum(generated_intervals.energy) as energy,
            sum(generated_intervals.emissions) as emissions,
            case when sum(generated_intervals.emissions) > 0
                then sum(generated_intervals.emissions) / sum(generated_intervals.energy)
                else 0
            end as emission_intensity
        from
        (
            select
                fs.trading_interval at time zone 'AEST' as trading_interval,
                f.network_id,
                f.network_region,
                fs.facility_code,
                sum(sum(fs.generated)) over (partition by fs.facility_code order by fs.trading_interval asc) / 2 / 12 as energy,
                case when f.emissions_factor_co2 > 0
                    then sum(sum(fs.generated)) over (partition by fs.facility_code order by fs.trading_interval asc) / 2 / 12  * f.emissions_factor_co2
                    else 0
                end as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            where
                fs.trading_interval >= '{interval_start}'
                and fs.trading_interval <= '{interval_end}'
                and f.network_id IN ('{network_id}')
                and f.interconnector is False
                and fs.generated > 0
            group by fs.trading_interval, fs.facility_code, f.emissions_factor_co2, f.network_region, f.network_id
        ) as generated_intervals
        where
            generated_intervals.trading_interval = '{interval_end}'
        group by 1, 2, 3
        order by 1 asc;
    """.format(
        interval_start=interval_start, interval_end=interval_end, network_id=network.code
    )

    logger.debug(query)

    df_gen = pd.read_sql(query, con=engine)

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    df_gen["price"] = df_gen["market_value"] / df_gen["generated"]
    df_gen["emission_factor"] = df_gen["emissions"] / df_gen["generated"]

    return df_gen


def calculate_total_import_and_export_per_region_for_interval(interconnector_data: pd.DataFrame) -> pd.DataFrame:
    """Calculates total import and export energy for a region using the interconnector dataframe

    Args:
        interconnector_data (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: total imports and export for each region for each interval

    Example return dataframe:

                                energy_imports  energy_exports
    network_id  network_region
    NEM         NSW1                      82.5             0.0
                QLD1                       0.0            55.0
                SA1                       22.0             0.0
                TAS1                       0.0            11.0
                VIC1                      11.0            49.5
    """

    dx = interconnector_data.groupby(["interconnector_region_from", "interconnector_region_to"]).energy.sum().reset_index()

    # invert regions
    dy = dx.rename(
        columns={
            "interconnector_region_from": "interconnector_region_to",
            "interconnector_region_to": "interconnector_region_from",
        }
    )

    # set indexes
    dy.set_index(["interconnector_region_to", "interconnector_region_from"], inplace=True)
    dx.set_index(["interconnector_region_to", "interconnector_region_from"], inplace=True)

    dy["energy"] *= -1

    dx.loc[dx.energy < 0, "energy"] = 0
    dy.loc[dy.energy < 0, "energy"] = 0

    f = pd.concat([dx, dy])

    energy_flows = pd.DataFrame(
        {
            "energy_imports": f.groupby("interconnector_region_to").energy.sum(),
            "energy_exports": f.groupby("interconnector_region_from").energy.sum(),
        }
    )

    energy_flows["network_id"] = "NEM"

    energy_flows.reset_index(inplace=True)
    energy_flows.rename(columns={"index": "network_region"}, inplace=True)
    energy_flows.set_index(["network_id", "network_region"], inplace=True)

    return energy_flows


def calculate_demand_region_for_interval() -> pd.DataFrame:
    """ """
    pass


def insert_flows(flow_results: pd.DataFrame) -> int:
    """Takes a list of generation values and calculates energies and bulk-inserts
    into the database"""

    datetime_now = datetime.now()

    flow_results.reset_index(inplace=True)

    # Add metadata
    flow_results["created_by"] = "opennem.worker.network_flows_v3"
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


def run_aggregate_flow_for_interval(interval: datetime, network: NetworkSchema) -> None:
    """This method runs the aggregate for an interval and for a network using flow solver

    Args:
        interval (datetime): _description_
        network (NetworkSchema): _description_
    """

    energy_and_emissions = load_energy_and_emissions_for_intervals(
        interval_start=interval, interval_end=interval + timedelta(minutes=5), network=network
    )

    interconnector_data = load_interconnector_intervals(
        date_start=interval, date_end=interval + timedelta(minutes=5), network=network
    )

    flows_and_emissions = solve_flows_for_interval(
        energy_and_emissions=energy_and_emissions,
        interconnector=interconnector_data,
    )

    insert_flows(flows_and_emissions)


if __name__ == "__main__":
    pass
