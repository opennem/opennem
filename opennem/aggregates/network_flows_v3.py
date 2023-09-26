"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

"""

import logging
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from opennem.core.flow_solver import (
    solve_flow_emissions_with_pandas,
)
from opennem.core.profiler import ProfilerLevel, ProfilerRetentionTime, profile_task
from opennem.db import get_database_engine, get_scoped_session
from opennem.db.models.opennem import AggregateNetworkFlows
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.aggregates.flows_v3")


class FlowWorkerException(Exception):
    pass


class FlowsValidationError(Exception):
    pass


def load_interconnector_intervals(
    network: NetworkSchema, interval_start: datetime, interval_end: datetime | None = None
) -> pd.DataFrame:
    """Load interconnector flows for an interval.

    Returns
        pd.DataFrame: DataFrame containing interconnector flows for an interval.


    Example return dataframe:

        trading_interval    interconnector_region_from interconnector_region_to  generated     energy
        2023-04-09 10:15:00                       NSW1                     QLD1 -669.90010 -55.825008
        2023-04-09 10:15:00                       TAS1                     VIC1 -399.80002 -33.316668
        2023-04-09 10:15:00                       VIC1                     NSW1 -261.80997 -21.817498
        2023-04-09 10:15:00                       VIC1                      SA1  412.31787  34.359822
    """
    engine = get_database_engine()

    if not interval_end:
        interval_end = interval_start

    query = """
        select
            fs.trading_interval at time zone '{timezone}' as trading_interval,
            f.interconnector_region_from,
            f.interconnector_region_to,
            coalesce(sum(fs.generated), 0) as generated,
            coalesce(sum(fs.generated) / 12, 0) as energy
        from facility_scada fs
        left join facility f
            on fs.facility_code = f.code
        where
            fs.trading_interval >= '{date_start}'
            and fs.trading_interval <= '{date_end}'
            and f.interconnector is True
            and f.network_id = '{network_id}'
        group by 1, 2, 3
        order by
            1 asc;

    """.format(
        date_start=interval_start,
        date_end=interval_end,
        timezone=network.timezone_database,
        network_id=network.code,
    )

    logger.debug(query)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    # convert index to local timezone
    df_gen.index.tz_localize(network.get_fixed_offset(), ambiguous="infer")

    df_gen.reset_index(inplace=True)

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    return df_gen


def load_energy_and_emissions_for_intervals(
    network: NetworkSchema, interval_start: datetime, interval_end: datetime | None = None
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

    Example return dataframe:


        trading_interval    network_id network_region      energy   emissions  emissions_intensity
        2023-04-09 10:20:00        NEM           NSW1  468.105472  226.549976             0.483972
        2023-04-09 10:20:00        NEM           QLD1  459.590348  295.124417             0.642147
        2023-04-09 10:20:00        NEM            SA1   36.929530    9.063695             0.245432
        2023-04-09 10:20:00        NEM           TAS1   71.088342    0.000000             0.000000
        2023-04-09 10:20:00        NEM           VIC1  387.120670  236.121274             0.609942
    """

    engine = get_database_engine()

    if not interval_end:
        interval_end = interval_start

    query = """
        select
            generated_intervals.trading_interval,
            '{network_id}' as network_id,
            generated_intervals.network_region,
            sum(generated_intervals.generated) as generated,
            sum(generated_intervals.energy) as energy,
            sum(generated_intervals.emissions) as emissions,
            case when sum(generated_intervals.emissions) > 0
                then sum(generated_intervals.emissions) / sum(generated_intervals.energy)
                else 0
            end as emissions_intensity
        from
        (
            select
                fs.trading_interval at time zone 'AEST' as trading_interval,
                f.network_id,
                f.network_region,
                fs.facility_code,
                sum(fs.generated) as generated,
                sum(fs.generated) / 12 as energy,
                sum(fs.generated) / 12 * f.emissions_factor_co2 as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            where
                fs.trading_interval >= '{interval_start}'
                and fs.trading_interval <= '{interval_end}'
                and f.network_id IN ('{network_id}', 'AEMO_ROOFTOP', 'OPENNEM_ROOFTOP_BACKFILL')
                and f.fueltech_id not in ('battery_charging')
                and f.interconnector is False
                and fs.generated > 0
            group by fs.trading_interval, fs.facility_code, f.emissions_factor_co2, f.network_region, f.network_id
        ) as generated_intervals
        group by 1, 2, 3
        order by 1 asc;
    """.format(
        interval_start=interval_start, interval_end=interval_end, network_id=network.code
    )

    logger.debug(query)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    # convert index to local timezone
    df_gen.index.tz_localize(network.get_fixed_offset(), ambiguous="infer")

    df_gen.reset_index(inplace=True)

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    return df_gen


def calculate_total_import_and_export_per_region_for_interval(interconnector_data: pd.DataFrame) -> pd.DataFrame:
    """Calculates total import and export energy for a region using the interconnector dataframe

    Args:
        interconnector_data (pd.DataFrame): interconnector dataframe from load_interconnector_intervals

    Returns:
        pd.DataFrame: total imports and export for each region for each interval

    Example return dataframe:

    network_id  network_region  energy_imports  energy_exports
    NEM         NSW1                      82.5             0.0
                QLD1                       0.0            55.0
                SA1                       22.0             0.0
                TAS1                       0.0            11.0
                VIC1                      11.0            49.5
    """

    dx = (
        interconnector_data.groupby(["trading_interval", "interconnector_region_from", "interconnector_region_to"])
        .energy.sum()
        .reset_index()
    )

    # invert regions
    dy = dx.rename(
        columns={
            "interconnector_region_from": "interconnector_region_to",
            "interconnector_region_to": "interconnector_region_from",
            "level_1": "network_region",
        }
    )

    # set indexes
    dy.set_index(["trading_interval", "interconnector_region_to", "interconnector_region_from"], inplace=True)
    dx.set_index(["trading_interval", "interconnector_region_to", "interconnector_region_from"], inplace=True)

    dy["energy"] *= -1

    dx.loc[dx.energy < 0, "energy"] = 0
    dy.loc[dy.energy < 0, "energy"] = 0

    f = pd.concat([dx, dy])

    energy_flows = pd.DataFrame(
        {
            "energy_imports": f.groupby(["trading_interval", "interconnector_region_to"]).energy.sum(),
            "energy_exports": f.groupby(["trading_interval", "interconnector_region_from"]).energy.sum(),
            "generated_imports": f.groupby(["trading_interval", "interconnector_region_to"]).energy.sum() * 12,
            "generated_exports": f.groupby(["trading_interval", "interconnector_region_from"]).energy.sum() * 12,
        }
    )

    # imports sum should equal exports sum always
    if round(energy_flows.energy_exports.sum(), 0) - round(energy_flows.energy_imports.sum(), 0) > 1:
        raise FlowWorkerException(
            f"Energy import and export totals do not match: {energy_flows.energy_exports.sum()} and {energy_flows.energy_imports.sum()}"
        )

    energy_flows["network_id"] = "NEM"

    energy_flows.reset_index(inplace=True)
    energy_flows.rename(columns={"index": "network_region"}, inplace=True)
    # energy_flows.set_index(["network_id", "network_region"], inplace=True)

    return energy_flows


def invert_interconnectors_invert_all_flows(interconnector_data: pd.DataFrame) -> pd.DataFrame:
    """Inverts the flows per interconnector to show net values"""
    original_set = interconnector_data.copy()

    inverted_set = interconnector_data.copy().rename(
        columns={
            "interconnector_region_from": "interconnector_region_to",
            "interconnector_region_to": "interconnector_region_from",
        }
    )

    inverted_set["generated"] *= -1
    inverted_set["energy"] *= -1

    original_set.loc[original_set.energy <= 0, "generated"] = 0
    inverted_set.loc[inverted_set.energy <= 0, "generated"] = 0
    original_set.loc[original_set.energy <= 0, "energy"] = 0
    inverted_set.loc[inverted_set.energy <= 0, "energy"] = 0

    result = pd.concat([original_set, inverted_set])

    # result = result.sort_values("interconnector_region_from")

    return result


def calculate_demand_region_for_interval(energy_and_emissions: pd.DataFrame, imports_and_export: pd.DataFrame) -> pd.DataFrame:
    """
    Takes energy and emissions and imports and exports and calculates demand for each region and adds it to a merged
    total dataframe
    """
    imports_and_export.rename({"level_1": "network_region"}, axis=1, inplace=True)

    df_with_demand = energy_and_emissions.merge(
        imports_and_export, how="left", on=["trading_interval", "network_id", "network_region"]
    )
    df_with_demand["demand"] = df_with_demand["energy"]
    # - df_with_demand["energy_exports"]

    # add emissions intensity for debugging
    df_with_demand["emissions_intensity"] = df_with_demand["emissions"] / df_with_demand["demand"]

    return df_with_demand


def persist_network_flows_and_emissions_for_interval(flow_results: pd.DataFrame, network: NetworkSchema = NetworkNEM) -> int:
    """persists the records to at_network_flows"""
    session = get_scoped_session()
    engine = get_database_engine()

    records_to_store = flow_results.to_dict(orient="records")

    for rec in records_to_store:
        rec["network_id"] = network.code
        rec["trading_interval"] = rec["trading_interval"].replace(tzinfo=network.get_fixed_offset())

    # insert
    stmt = insert(AggregateNetworkFlows).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "network_region"],
        set_={
            "energy_imports": stmt.excluded.energy_imports,
            "energy_exports": stmt.excluded.energy_exports,
            "emissions_exports": stmt.excluded.emissions_exports,
            "emissions_imports": stmt.excluded.emissions_imports,
            "market_value_exports": stmt.excluded.market_value_exports,
            "market_value_imports": stmt.excluded.market_value_imports,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error inserting records")
        raise e
    finally:
        session.rollback()
        session.close()
        engine.dispose()

    return len(records_to_store)


def persist_network_flows_and_emissions_for_interval_as_dataframe(flow_results: pd.DataFrame) -> int | None:
    """persists the records to at_network_flows"""
    engine = get_database_engine()

    return flow_results.to_sql("at_network_flows_v3", engine, if_exists="append", index=False, method="multi", chunksize=5000)


@profile_task(
    send_slack=False,
    message_fmt="Running flow v3 for {interval_number} intervals",
    level=ProfilerLevel.INFO,
    retention_period=ProfilerRetentionTime.FOREVER,
)
def run_flows_for_last_intervals(interval_number: int, network: NetworkSchema = NetworkNEM) -> None:
    """ " Run flow processor for last x interval starting from now"""

    logger.info(f"Running flows for last {interval_number} intervals")

    end_interval = get_last_completed_interval_for_network(network=network)
    start_interval = end_interval - timedelta(minutes=network.intervals_per_hour / 60 * interval_number)

    if interval_number == 1:
        start_interval = end_interval

    run_aggregate_flow_for_interval_v3(
        interval_start=start_interval, interval_end=end_interval, network=network, validate_results=False
    )


@profile_task(
    send_slack=False,
    message_fmt="Running flow v3 for {days} days",
    level=ProfilerLevel.INFO,
    retention_period=ProfilerRetentionTime.MONTH,
)
def run_flows_for_last_days(days: int, network: NetworkSchema = NetworkNEM) -> None:
    """ " Run flow processor for last x interval starting from now"""

    logger.info(f"Running flows for last {days}")

    interval_end = get_last_completed_interval_for_network(network=NetworkNEM)
    interval_start = interval_end - timedelta(days=days)
    run_aggregate_flow_for_interval_v3(
        network=network,
        interval_start=interval_start,
        interval_end=interval_end,
    )


def run_flows_by_month() -> None:
    """Run the entire archive"""
    period_end = get_last_completed_interval_for_network(network=NetworkNEM).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    period_start = datetime.fromisoformat("2009-06-01T00:00:00+10:00")
    period_end = datetime.fromisoformat("2009-08-01T00:00:00+10:00")
    # period_start = datetime.fromisoformat("2017-04-01T00:00:00+10:00")
    from opennem.utils.dates import month_series

    for month in month_series(period_start, period_end, reverse=False):
        next_month = month.replace(day=28) + timedelta(days=4)
        res = next_month - timedelta(days=next_month.day) + timedelta(days=1) - timedelta(seconds=1)

        print(f"Running for {month} to {res}")
        run_aggregate_flow_for_interval_v3(
            network=NetworkNEM,
            interval_start=month,
            interval_end=res,
        )


def validate_network_flows(flow_records: pd.DataFrame, raise_exception: bool = True) -> None:
    """Validate network flows and sanity checking"""
    # 1. Check values are positive
    validate_fields = ["energy_exports", "energy_imports", "emissions_exports", "emissions_imports"]

    for field in validate_fields:
        bad_values = flow_records.query(f"{field} < 0")

        if not bad_values.empty:
            for rec in bad_values.to_dict(orient="records"):
                raise FlowsValidationError(f"Bad value: {rec['trading_interval']} {rec['network_region']} {field} {rec[field]}")

    # 2. Check emission factors
    flow_records_validation = flow_records.copy()

    flow_records_validation.loc[flow_records_validation["energy_exports"] > 0, "exports_emission_factor"] = (
        flow_records_validation["emissions_exports"] / flow_records_validation["energy_exports"]
    )
    flow_records_validation.loc[flow_records_validation["energy_imports"] > 0, "imports_emission_factor"] = (
        flow_records_validation["emissions_imports"] / flow_records_validation["energy_imports"]
    )

    bad_factors_exports = flow_records_validation.query("exports_emission_factor > 1.7 or exports_emission_factor < 0")
    bad_factors_imports = flow_records_validation.query("imports_emission_factor > 1.7 or imports_emission_factor < 0")

    if not bad_factors_exports.empty:
        for rec in bad_factors_exports.to_dict(orient="records"):
            bad_factor_message = (
                f"Bad exports emission factor: {rec['trading_interval']} {rec['network_region']} {rec['exports_emission_factor']}"
            )
            logger.error(bad_factor_message)

            if raise_exception:
                raise FlowsValidationError(bad_factor_message)

    if not bad_factors_imports.empty:
        for rec in bad_factors_imports.to_dict(orient="records"):
            bad_factor_message = (
                f"Bad imports emission factor: {rec['trading_interval']} {rec['network_region']} {rec['imports_emission_factor']}"
            )
            logger.error(bad_factor_message)

            if raise_exception:
                raise FlowsValidationError(bad_factor_message)

    return None


@profile_task(
    send_slack=True,
    message_fmt="Running aggregate flow v3 for interval {interval_start} for {network.code}",
    level=ProfilerLevel.INFO,
    retention_period=ProfilerRetentionTime.FOREVER,
)
def run_aggregate_flow_for_interval_v3(
    network: NetworkSchema, interval_start: datetime, interval_end: datetime | None = None, validate_results: bool = False
) -> int | None:
    """This method runs the aggregate for an interval and for a network using flow solver
    This is version 3 of the method and sits behind the settings.network_flows_v3 feature flag
    """
    # 0. support single interval
    if not interval_end:
        interval_end = interval_start

    # 1. get
    try:
        energy_and_emissions = load_energy_and_emissions_for_intervals(
            network=network, interval_start=interval_start, interval_end=interval_end
        )
    except Exception as e:
        logger.error(e)
        return 0

    # 2. get interconnector data and calculate region imports/exports net
    try:
        interconnector_data = load_interconnector_intervals(
            network=network, interval_start=interval_start, interval_end=interval_end
        )
    except Exception as e:
        logger.error(e)
        return 0

    interconnector_data_net = invert_interconnectors_invert_all_flows(interconnector_data)

    region_imports_and_exports = calculate_total_import_and_export_per_region_for_interval(
        interconnector_data=interconnector_data
    )

    # 3. calculate demand for each region and add it to the dataframe
    region_net_demand = calculate_demand_region_for_interval(
        energy_and_emissions=energy_and_emissions, imports_and_export=region_imports_and_exports
    )

    # 5. Solve.
    # Replace the original solve_flow_emissions_for_interval with the new pandas-based function
    network_flow_records = solve_flow_emissions_with_pandas(interconnector_data_net, region_net_demand)

    # 7. Validate flows - this will throw errors on bad values
    if validate_results:
        validate_network_flows(flow_records=network_flow_records)

    # 7. Persist to database aggregate table
    inserted_records = persist_network_flows_and_emissions_for_interval(flow_results=network_flow_records)

    logger.info(f"Inserted {inserted_records} records for interval {interval_start} and network {network.code}")

    return inserted_records


# debug entry point
if __name__ == "__main__":
    # run_flows_for_last_days(days=1)
    run_flows_by_month()

    # from_interval = datetime.fromisoformat("2023-02-05T14:50:00+10:00")
    # run_flows_for_last_intervals(interval_number=12 * 24 * 1, network=NetworkNEM)
