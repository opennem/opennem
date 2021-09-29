"""

In a nutshell, it uses numpy to solve a simply simultaneous equation that solves emissions flows
between each region - based on the power flows between each region, and the territorial emissions
of each region.   (I did use it to calculate the territorial emissions at the same time - but gather
you've already got a process for that?).


The current work flow is that it loads emissions factors from the MMS tables, and maps the emissions
factors to the appropriate power station or duid. These are applied to the generation data (the MWh
values calculated by trapezoidal integration) to generator the emissions. The actual flows on the
interconnectors (METEREDMWFLOW ) is also used from the interconnector MMS tables.

Most of the script is just arranging the data in a form for the numpy linalg function = not sure
why I used a dict as data structure. Probably not a good decision - but it was what I started
with / stuck with.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

import numpy as np
import pandas as pd

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.workers.emission_flows")

ENGINE = get_database_engine()


def load_interconnector(date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """Load interconnector power"""

    query = """


    """

    # interconnector fields
    fields = ["METEREDMWFLOW", "INTERVENTION", "FROM_REGIONID", "TO_REGIONID"]
    data = {}

    df = pd.DataFrame(data, fields)

    return df


def calc_emissions(df_emissions):
    # MWH & tonnes (divide 12)
    dx_emissions = df_emissions.groupby(["SETTLEMENTDATE", "REGIONID", "TECHFUEL_ID"])[
        ["MW", "EMISSIONS"]
    ].sum()
    dx_emissions.reset_index(inplace=True)
    return dx_emissions


def calc_flows(df_ic):
    dx_ic = df_ic.copy()
    dx_ic.METEREDMWFLOW = dx_ic.METEREDMWFLOW
    return dx_ic


def isolate_di(dx_emissions, dx_ic, dt):
    emissions_di = dx_emissions[dx_emissions.SETTLEMENTDATE == dt]
    interconnector_di = dx_ic[dx_ic.index == dt]
    return emissions_di, interconnector_di


def simple_exports(emissions_di, power_dict, from_regionid, to_regionid):
    dx = emissions_di[emissions_di.REGIONID == from_regionid]
    ic_flow = power_dict[from_regionid, to_regionid]
    return ic_flow / dx.MW.sum() * dx.EMISSIONS.sum()


def emissions(df_emissions, power_dict):
    emissions_dict = dict(df_emissions.groupby(df_emissions.REGIONID).EMISSIONS.sum())
    simple_flows = [[2, 1], [3, 5], [4, 5]]
    for from_regionid, to_regionid in simple_flows:
        emissions_dict[(from_regionid, to_regionid)] = simple_exports(
            df_emissions, power_dict, from_regionid, to_regionid
        )
    return emissions_dict


def power(df_emissions, df_ic) -> Dict:
    power_dict = dict(df_emissions.groupby(df_emissions.REGIONID).MW.sum())
    power_dict.update(interconnector_dict(df_ic))
    return power_dict


def interconnector_dict(interconnector_di: pd.DataFrame) -> pd.DataFrame:
    dx = (
        interconnector_di.groupby(["FROM_REGIONID", "TO_REGIONID"])
        .METEREDMWFLOW.sum()
        .reset_index()
    )
    dy = dx.rename(columns={"FROM_REGIONID": "TO_REGIONID", "TO_REGIONID": "FROM_REGIONID"})
    dy["METEREDMWFLOW"] *= -1
    df = dx.append(dy)
    df.loc[df.METEREDMWFLOW < 0, "METEREDMWFLOW"] = 0

    return df.set_index(["FROM_REGIONID", "TO_REGIONID"]).to_dict()["METEREDMWFLOW"]


def supply(power_dict: Dict) -> Dict:
    d = {}
    d[1] = power_dict[1] + power_dict[(2, 1)] + power_dict[(5, 1)]
    d[2] = power_dict[2] + power_dict[(1, 2)]
    d[3] = power_dict[3] + power_dict[(5, 3)]
    d[4] = power_dict[4] + power_dict[(5, 4)]
    d[5] = power_dict[5] + power_dict[(1, 5)] + power_dict[(3, 5)] + power_dict[(4, 5)]
    return d


def demand(power_dict: Dict) -> Dict:
    d = {}
    d[1] = (
        power_dict[1]
        + power_dict[(2, 1)]
        + power_dict[(5, 1)]
        - power_dict[(1, 5)]
        - power_dict[(1, 2)]
    )
    d[2] = power_dict[2] + power_dict[(1, 2)] - power_dict[(2, 1)]
    d[3] = power_dict[3] + power_dict[(5, 3)] - power_dict[(3, 5)]
    d[4] = power_dict[4] + power_dict[(5, 4)] - power_dict[(4, 5)]
    d[5] = (
        power_dict[5]
        + power_dict[(1, 5)]
        + power_dict[(3, 5)]
        + power_dict[(4, 5)]
        - power_dict[(5, 1)]
        - power_dict[(5, 4)]
        - power_dict[(5, 3)]
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
    demand_dict = demand(power_dict)

    a = np.zeros((10, 10))
    _var_dict = dict(zip(["s", "q", "t", "n", "v", "v-n", "n-q", "n-v", "v-s", "v-t"], range(10)))

    # emissions balance equations
    fill_row(a, 0, [["s", 1], ["v-s", -1]], _var_dict)
    fill_row(a, 1, [["q", 1], ["n-q", -1]], _var_dict)
    fill_row(a, 2, [["t", 1], ["v-t", -1]], _var_dict)
    fill_row(a, 3, [["n", 1], ["v-n", -1], ["n-q", 1], ["n-v", 1]], _var_dict)
    fill_row(a, 4, [["v", 1], ["v-n", 1], ["n-v", -1], ["v-s", 1], ["v-t", 1]], _var_dict)

    # emissions intensity equations
    fill_row(a, 5, [["n-q", 1], ["n", -power_dict[(1, 2)] / demand_dict[1]]], _var_dict)
    fill_row(a, 6, [["n-v", 1], ["n", -power_dict[(1, 5)] / demand_dict[1]]], _var_dict)
    fill_row(a, 7, [["v-t", 1], ["v", -power_dict[(5, 4)] / demand_dict[5]]], _var_dict)
    fill_row(a, 8, [["v-s", 1], ["v", -power_dict[(5, 3)] / demand_dict[5]]], _var_dict)
    fill_row(a, 9, [["v-n", 1], ["v", -power_dict[(5, 1)] / demand_dict[5]]], _var_dict)

    # constants
    b = np.zeros((10, 1))
    fill_constant(b, "s", emissions_dict[3] - emissions_dict[(3, 5)], _var_dict)
    fill_constant(b, "q", emissions_dict[2] - emissions_dict[(2, 1)], _var_dict)
    fill_constant(b, "t", emissions_dict[4] - emissions_dict[(4, 5)], _var_dict)
    fill_constant(b, "n", emissions_dict[1] + emissions_dict[(2, 1)], _var_dict)
    fill_constant(
        b, "v", emissions_dict[5] + emissions_dict[(3, 5)] + emissions_dict[(4, 5)], _var_dict
    )

    # get result
    result = np.linalg.solve(a, b)

    # transform into emission flows
    emission_flows = {}
    emission_flows[1, 2] = result[6][0]
    emission_flows[5, 1] = result[5][0]
    emission_flows[1, 5] = result[7][0]
    emission_flows[5, 3] = result[8][0]
    emission_flows[5, 4] = result[9][0]
    emission_flows[2, 1] = emissions_dict[2, 1]
    emission_flows[4, 5] = emissions_dict[4, 5]
    emission_flows[3, 5] = emissions_dict[3, 5]

    # shape into dataframe
    df = pd.DataFrame.from_dict(emission_flows, orient="index")
    df.columns = ["EMISSIONS"]
    df.reset_index(inplace=True)

    return df


def calculate_emission_flows(df_gen, df_ic):

    dx_emissions = calc_emissions(df_gen)
    dx_ic = calc_flows(df_ic)
    results = {}
    dt = df_gen.SETTLEMENTDATE.iloc[0]
    while dt <= df_gen.SETTLEMENTDATE.iloc[-1]:
        emissions_di, interconnector_di = isolate_di(dx_emissions, dx_ic, dt)
        results[dt] = solve_flows(emissions_di, interconnector_di)
        dt += timedelta(0, 300)
    return results


def load_factors() -> pd.DataFrame:
    sql = """
        SELECT
            S.STATIONID,
            S.ID,
            GS.GENSETID,
            GU.CO2E_DATA_SOURCE,
            GU.CO2E_ENERGY_SOURCE,
            GU.CO2E_EMISSIONS_FACTOR,
            GU.REGISTEREDCAPACITY
        FROM mms.GENUNITS GU
            INNER JOIN mms.GENSET GS ON GS.ID = GU.GENSETID
            INNER JOIN STATION S ON S.ID = GU.STATIONID
        """
    return pd.read_sql(sql, con=ENGINE)


def load_stations() -> pd.DataFrame:
    # loads unique duids
    sql = """
        SELECT
            DUID,
            STATIONID
        FROM DUDETAILSUMMARY
        GROUP BY DUID"""

    return pd.read_sql(sql, con=ENGINE)


def dispatch_all_int(date_start: datetime, date_end: datetime) -> pd.DataFrame:
    """New"""
    df = pd.DataFrame()

    return df


def map_factors(date_start: datetime, date_end: datetime, unit: str = "MW") -> pd.DataFrame:
    """Fetch all emissions for all stations"""

    query = """



    """

    # load_maps
    df_gen = dispatch_all_int(date_start=date_start, date_end=date_end)

    stations = load_stations()
    factors = load_factors()

    # transform
    station_dict = dict(stations.values)
    factor_dict = dict(factors[["ID", "CO2E_EMISSIONS_FACTOR"]].values)

    # map station id's
    df_gen["SID"] = df_gen.ID.apply(lambda x: station_dict[x])
    df_gen["emissions_factor"] = df_gen.SID.apply(lambda x: factor_dict[x])
    df_gen["EMISSIONS"] = df_gen.emissions_factor * df_gen[unit]

    return df_gen


def calc_day(day: datetime) -> None:

    day_next = day + timedelta(days=1)

    df_gen = map_factors(date_start=day, date_end=day_next)

    df_ic = load_interconnector(date_start=day, date_end=day_next)

    results_dict = calculate_emission_flows(df_gen, df_ic)

    flow_series = pd.concat(results_dict).reset_index()

    flow_series.rename(columns={"level_0": "SETTLEMENTDATE", "index": "REGIONIDS"}, inplace=True)
    flow_series["REGIONID_FROM"] = flow_series.apply(lambda x: x.REGIONIDS[0], axis=1)
    flow_series["REGIONID_TO"] = flow_series.apply(lambda x: x.REGIONIDS[1], axis=1)

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

    # insert into db
    daily_flow.to_sql("EMISSION_FLOW", engine=ENGINE, if_exist="append")

    # daily_flow.to_("~/emissions/daily_summary.csv".format(d.date()), mode='a', header=False)


if __name__ == "__main__":
    logger.info("starting")

    test_date = datetime.fromisoformat("2021-10-01T00:00:00")

    calc_day(test_date)
