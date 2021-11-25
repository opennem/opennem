"""OpenNEM Network Flows Worker

Creates an aggregate table with network flows (imports/exports), emissions and market_value

@TODO There are still some hard-coded methods her specific to NEM that should be refactored
out
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import numpy as np
import pandas as pd
import pytz

from opennem.db import get_database_engine
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_complete_day_for_network
from opennem.utils.http import http

logger = logging.getLogger("opennem.workers.emission_flows")

engine = get_database_engine()


def load_interconnector_intervals(date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """Load interconnectors for a date range"""

    query = """
        select
            fs.trading_interval at time zone 'AEST' as trading_interval,
            coalesce(fs.generated, 0) as generated,
            f.interconnector_region_to,
            f.interconnector_region_from
        from facility_scada fs
        left join facility f on f.code = fs.facility_code
        where
            f.interconnector is True
            and fs.trading_interval >= '{date_start}'
            and fs.trading_interval < '{date_end}'
    """.format(
        date_start=date_start, date_end=date_end
    )

    df_gen = pd.read_sql(query, con=engine, index_col="trading_interval")

    return df_gen


def load_energy_intervals(date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """Fetch all emissions for all stations"""

    query = """
        select
            fs.trading_interval at time zone 'AEST' as trading_interval,
            f.network_id,
            f.network_region,
            f.fueltech_id,
            fs.facility_code as fs_duid,
            f.code as duid,
            fs.generated as power,
            fs.eoi_quantity as energy,
            coalesce(fs.eoi_quantity * f.emissions_factor_co2, 0) as emissions
        from facility_scada fs
        left join facility f on fs.facility_code = f.code
        where
            fs.trading_interval >= '{date_start}T00:00:00+10:00'
            and fs.trading_interval < '{date_end}T00:00:00+10:00'
            and fs.eoi_quantity is not null
            and f.interconnector is False
        order by 1 asc;
    """.format(
        date_start=date_start.date(), date_end=date_end.date()
    )

    df_gen = pd.read_sql(query, con=engine)

    return df_gen


def interconnector_dict(interconnector_di: pd.DataFrame) -> pd.DataFrame:
    dx = (
        interconnector_di.groupby(["interconnector_region_from", "interconnector_region_to"])
        .generated.sum()
        .reset_index()
    )
    dy = dx.rename(
        columns={
            "interconnector_region_from": "interconnector_region_to",
            "interconnector_region_to": "interconnector_region_from",
        }
    )
    dy["generated"] *= -1
    df = dx.append(dy)
    df.loc[df.generated < 0, "generated"] = 0

    return df.set_index(["interconnector_region_from", "interconnector_region_to"]).to_dict()[
        "generated"
    ]


def power(df_emissions, df_ic) -> Dict:
    df_emissions = df_emissions.reset_index()
    power_dict = dict(df_emissions.groupby(df_emissions.network_region).energy.sum())
    power_dict.update(interconnector_dict(df_ic))
    return power_dict


def simple_exports(emissions_di, power_dict, from_regionid, to_regionid):
    dx = emissions_di[emissions_di.network_region == from_regionid]
    ic_flow = power_dict[from_regionid, to_regionid]
    return ic_flow / dx.energy.sum() * dx.emissions.sum()


def demand(power_dict: Dict) -> Dict:
    d = {}

    if "NSW1" not in power_dict:
        raise Exception("Missing generation info")

    d["NSW1"] = (
        power_dict["NSW1"]
        + power_dict[("QLD1", "NSW1")]
        + power_dict[("VIC1", "NSW1")]
        - power_dict[("NSW1", "VIC1")]
        - power_dict[("NSW1", "QLD1")]
    )
    d["QLD1"] = power_dict["QLD1"] + power_dict[("NSW1", "QLD1")] - power_dict[("QLD1", "NSW1")]
    d["SA1"] = power_dict["SA1"] + power_dict[("VIC1", "SA1")] - power_dict[("SA1", "VIC1")]
    d["TAS1"] = power_dict["TAS1"] + power_dict[("VIC1", "TAS1")] - power_dict[("TAS1", "VIC1")]
    d["VIC1"] = (
        power_dict["VIC1"]
        + power_dict[("NSW1", "VIC1")]
        + power_dict[("SA1", "VIC1")]
        + power_dict[("TAS1", "VIC1")]
        - power_dict[("VIC1", "NSW1")]
        - power_dict[("VIC1", "TAS1")]
        - power_dict[("VIC1", "SA1")]
    )
    return d


def fill_row(a, row, pairs, _var_dict) -> None:
    for _var, value in pairs:
        a[row][_var_dict[_var]] = value


def fill_constant(a, _var, value, _var_dict) -> None:
    idx = _var_dict[_var]
    a[idx] = value


def solve_flows(emissions_di, interconnector_di) -> pd.DataFrame:
    #
    power_dict = power(emissions_di, interconnector_di)
    emissions_dict = emissions(emissions_di, power_dict)

    try:
        demand_dict = demand(power_dict)
    except Exception as e:
        print("Error: {}".format(e))
        return None

    a = np.zeros((10, 10))
    _var_dict = dict(zip(["s", "q", "t", "n", "v", "v-n", "n-q", "n-v", "v-s", "v-t"], range(10)))

    # emissions balance equations
    fill_row(a, 0, [["s", 1], ["v-s", -1]], _var_dict)
    fill_row(a, 1, [["q", 1], ["n-q", -1]], _var_dict)
    fill_row(a, 2, [["t", 1], ["v-t", -1]], _var_dict)
    fill_row(a, 3, [["n", 1], ["v-n", -1], ["n-q", 1], ["n-v", 1]], _var_dict)
    fill_row(a, 4, [["v", 1], ["v-n", 1], ["n-v", -1], ["v-s", 1], ["v-t", 1]], _var_dict)

    # emissions intensity equations
    fill_row(
        a, 5, [["n-q", 1], ["n", -power_dict[("NSW1", "QLD1")] / demand_dict["NSW1"]]], _var_dict
    )
    fill_row(
        a, 6, [["n-v", 1], ["n", -power_dict[("NSW1", "VIC1")] / demand_dict["NSW1"]]], _var_dict
    )
    fill_row(
        a, 7, [["v-t", 1], ["v", -power_dict[("VIC1", "TAS1")] / demand_dict["VIC1"]]], _var_dict
    )
    fill_row(
        a, 8, [["v-s", 1], ["v", -power_dict[("VIC1", "SA1")] / demand_dict["VIC1"]]], _var_dict
    )
    fill_row(
        a, 9, [["v-n", 1], ["v", -power_dict[("VIC1", "NSW1")] / demand_dict["VIC1"]]], _var_dict
    )

    # constants
    b = np.zeros((10, 1))
    fill_constant(b, "s", emissions_dict["SA1"] - emissions_dict[("SA1", "VIC1")], _var_dict)
    fill_constant(b, "q", emissions_dict["QLD1"] - emissions_dict[("QLD1", "NSW1")], _var_dict)
    fill_constant(b, "t", emissions_dict["TAS1"] - emissions_dict[("TAS1", "VIC1")], _var_dict)
    fill_constant(b, "n", emissions_dict["NSW1"] + emissions_dict[("QLD1", "NSW1")], _var_dict)
    fill_constant(
        b,
        "v",
        emissions_dict["VIC1"]
        + emissions_dict[("SA1", "VIC1")]
        + emissions_dict[("TAS1", "VIC1")],
        _var_dict,
    )

    # get result
    result = np.linalg.solve(a, b)

    # transform into emission flows
    emission_flows = {}
    emission_flows["NSW1", "QLD1"] = result[6][0]
    emission_flows["VIC1", "NSW1"] = result[5][0]
    emission_flows["NSW1", "VIC1"] = result[7][0]
    emission_flows["VIC1", "SA1"] = result[8][0]
    emission_flows["VIC1", "TAS1"] = result[9][0]
    emission_flows["QLD1", "NSW1"] = emissions_dict["QLD1", "NSW1"]
    emission_flows["TAS1", "VIC1"] = emissions_dict["TAS1", "VIC1"]
    emission_flows["SA1", "VIC1"] = emissions_dict["SA1", "VIC1"]

    # shape into dataframe
    df = pd.DataFrame.from_dict(emission_flows, orient="index")
    df.columns = ["EMISSIONS"]
    df.reset_index(inplace=True)

    return df


def calc_emissions(df_emissions: pd.DataFrame) -> pd.DataFrame:
    df_gen_em = df_emissions.groupby(["trading_interval", "network_region", "fueltech_id"])[
        ["energy", "emissions"]
    ].sum()
    df_gen_em.reset_index(inplace=True)

    return df_gen_em


def calculate_emission_flows(df_gen: pd.DataFrame, df_ic: pd.DataFrame) -> Dict:

    dx_emissions = calc_emissions(df_gen)
    dx_ic = df_ic

    results = {}
    dt = df_gen.trading_interval.iloc[0]
    while dt <= df_gen.trading_interval.iloc[-1]:
        emissions_di = dx_emissions[dx_emissions.trading_interval == dt]
        interconnector_di = dx_ic[dx_ic.index == dt]

        results[dt] = solve_flows(emissions_di, interconnector_di)
        dt += timedelta(minutes=5)

    return results


def calc_day(day: datetime) -> None:

    day_next = day + timedelta(days=1)

    df_gen = load_energy_intervals(date_start=day, date_end=day_next)

    df_ic = load_interconnector_intervals(date_start=day, date_end=day_next)

    results_dict = calculate_emission_flows(df_gen, df_ic)

    flow_series = pd.concat(results_dict).reset_index()

    flow_series.rename(columns={"level_0": "SETTLEMENTDATE", "index": "REGIONIDS"}, inplace=True)
    flow_series["REGIONID_FROM"] = flow_series.apply(lambda x: x.REGIONIDS[0], axis=1)
    flow_series["REGIONID_TO"] = flow_series.apply(lambda x: x.REGIONIDS[1], axis=1)

    return flow_series

    # flow_series[["SETTLEMENTDATE", "REGIONID_FROM", "REGIONID_TO", "EMISSIONS"]].to_csv(
    #     "~/emissions/series/{0}.csv".format(day), index=None
    # )

    # build the final data frame with both imports and exports
    daily_flow = pd.DataFrame(
        {
            "EXPORTS": flow_series.groupby("REGIONID_FROM").EMISSIONS.sum(),
            "IMPORTS": flow_series.groupby("REGIONID_TO").EMISSIONS.sum(),
        }
    )
    daily_flow.index.name = "REGIONID"
    daily_flow["DATE"] = day
    return daily_flow


def emissions(df_emissions, power_dict):
    df_emissions = df_emissions.reset_index()
    emissions_dict = dict(df_emissions.groupby(df_emissions.network_region).emissions.sum())
    # simple_flows = [[2, 1], [3, 5], [4, 5]]
    simple_flows = [["QLD1", "NSW1"], ["SA1", "VIC1"], ["TAS1", "VIC1"]]
    for from_regionid, to_regionid in simple_flows:
        emissions_dict[(from_regionid, to_regionid)] = simple_exports(
            df_emissions, power_dict, from_regionid, to_regionid
        )
    return emissions_dict


def run_emission_update_day(
    days: int = 1,
    day: Optional[datetime] = None,
) -> None:
    """Run emission calcs for number of days"""
    # This is Sydney time as the data is published in local time

    if not day:
        day = get_last_complete_day_for_network(NetworkNEM)

    current_day = day
    date_min = day - timedelta(days=days)

    while current_day >= date_min:
        logger.info("Running emission update for {}".format(current_day))

        calc_day(
            current_day,
        )

        current_day -= timedelta(days=days)


def _test_case() -> None:
    test_date = datetime.fromisoformat("2021-10-01T00:00:00")
    calc_day(test_date)


if __name__ == "__main__":
    logger.info("starting")
    _test_case()
    # run_emission_update_day(7)
