"""
Emissions Flow Calculations

(c) 2022 OpenNEM. University of Melbourne.


"""

import datetime
import os

import numpy as np
import pandas as pd

# from duid_meta import CONFIG, MODULE_DIR
# from opennem_emissions import db_connection as dbc
# from mms_analysis.data import interconnector
from sqlalchemy import create_engine

CONFIG = {}
PATH = os.path.join(CONFIG["local_settings"]["test_folder"], "testdb.db")
SQLITE = create_engine("sqlite:///{0}".format(PATH))
DERIVED = create_engine(
    "mysql://{username}:{password}@{hostname}/nemweb_derived?unix_socket={socket}".format(
        **CONFIG["python_sql"]
    )
)


def load_factors() -> None:
    sql = (
        "SELECT S.STATIONID, S.ID, GS.GENSETID, GU.CO2E_DATA_SOURCE, GU.CO2E_ENERGY_SOURCE, GU.CO2E_EMISSIONS_FACTOR, GU.REGISTEREDCAPACITY FROM GENUNITS GU "
        "INNER JOIN GENSET GS "
        "ON GS.ID = GU.GENSETID "
        "INNER JOIN STATION S "
        "ON S.ID = GU.STATIONID "
    )
    return pd.read_sql(sql, con=SQLITE)


def load_stations() -> None:
    # loads unique duids
    sql = "SELECT DUID, STATIONID " "FROM DUDETAILSUMMARY " "GROUP BY DUID"
    return pd.read_sql(sql, con=SQLITE)


def factor_maps() -> None:
    # load emissions factors and station maps
    factors = load_factors()
    stations = load_stations()

    station_dict = dict(stations.values)

    return station_dict, factors


def map_factors(df, unit="MW"):
    # load_maps
    station_dict, factors = factor_maps()

    # emissions dict
    factor_dict = dict(factors[["ID", "CO2E_EMISSIONS_FACTOR"]].values)

    # map station id's
    df["SID"] = df.ID.apply(lambda x: station_dict[x])
    df["emissions_factor"] = df.SID.apply(lambda x: factor_dict[x])
    df["EMISSIONS"] = df.emissions_factor * df[unit]

    return df


def load_day(
    d1=datetime.datetime(2019, 12, 1), d2=datetime.datetime(2019, 12, 2), db="nemweb_live"
):
    # load data
    df_gen = dbc.dispatch_all_int(d1=d1, d2=d2, db=db)
    df_emissions = map_factors(df_gen)
    df_ic = interconnector.load_interconnector(
        dt_start=d1,
        dt_end=d2,
        fields=["METEREDMWFLOW", "INTERVENTION", "FROM_REGIONID", "TO_REGIONID"],
    )
    return df_emissions, df_ic


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


def calculate_emission_flows(df_gen, df_ic):

    dx_emissions = calc_emissions(df_gen)
    dx_ic = calc_flows(df_ic)
    results = {}
    dt = df_gen.SETTLEMENTDATE.iloc[0]
    while dt <= df_gen.SETTLEMENTDATE.iloc[-1]:
        emissions_di, interconnector_di = isolate_di(dx_emissions, dx_ic, dt)
        results[dt] = solve_flows(emissions_di, interconnector_di)
        dt += datetime.timedelta(0, 300)
    return results


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


def power(df_emissions, df_ic):
    power_dict = dict(df_emissions.groupby(df_emissions.REGIONID).MW.sum())
    power_dict.update(interconnector_dict(df_ic))
    return power_dict


def interconnector_dict(interconnector_di):
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


def supply(power_dict) -> None:
    d = {}
    d[1] = power_dict[1] + power_dict[(2, 1)] + power_dict[(5, 1)]
    d[2] = power_dict[2] + power_dict[(1, 2)]
    d[3] = power_dict[3] + power_dict[(5, 3)]
    d[4] = power_dict[4] + power_dict[(5, 4)]
    d[5] = power_dict[5] + power_dict[(1, 5)] + power_dict[(3, 5)] + power_dict[(4, 5)]
    return d


def demand(power_dict) -> None:
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


def solve_flows(emissions_di, interconnector_di) -> None:
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
    # fill_constant(b, "v-n", power_dict[(1,2)] * emissions_dict[1] / supply_dict[2], _var_dict)
    # fill_constant(b, "n-q", power_dict[(1,5)] * (emissions_dict[1] + emissions_dict[(2,1)]) / supply_dict[2], _var_dict)
    # fill_constant(b, "n-v", power_dict[(5,4)] * emissions_dict[5] / supply_dict[5], _var_dict)
    # fill_constant(b, "v-s", power_dict[(5,3)] * emissions_dict[5] / supply_dict[5], _var_dict)
    # fill_constant(b, "v-t", power_dict[(5,1)] * (emissions_dict[5] + emissions_dict[(3,5)] + emissions_dict[(4,5)]) / supply_dict[5], _var_dict)
    result = np.linalg.solve(a, b)
    emission_flows = {}
    emission_flows[1, 2] = result[6][0]
    emission_flows[5, 1] = result[5][0]
    emission_flows[1, 5] = result[7][0]
    emission_flows[5, 3] = result[8][0]
    emission_flows[5, 4] = result[9][0]
    emission_flows[2, 1] = emissions_dict[2, 1]
    emission_flows[4, 5] = emissions_dict[4, 5]
    emission_flows[3, 5] = emissions_dict[3, 5]
    df = pd.DataFrame.from_dict(emission_flows, orient="index")
    df.columns = ["EMISSIONS"]
    df.reset_index(inplace=True)
    return df


def fill_row(a, row, pairs, _var_dict) -> None:
    for _var, value in pairs:
        a[row][_var_dict[_var]] = value


def fill_constant(a, _var, value, _var_dict) -> None:
    idx = _var_dict[_var]
    a[idx] = value


def calc_day(d=datetime.datetime(2019, 12, 2), db="nemweb_live") -> None:
    df_gen, df_ic = load_day(d1=d, d2=d + datetime.timedelta(1), db=db)

    results_dict = calculate_emission_flows(df_gen, df_ic)

    flow_series = pd.concat(results_dict).reset_index()

    flow_series.rename(columns={"level_0": "SETTLEMENTDATE", "index": "REGIONIDS"}, inplace=True)
    flow_series["REGIONID_FROM"] = flow_series.apply(lambda x: x.REGIONIDS[0], axis=1)
    flow_series["REGIONID_TO"] = flow_series.apply(lambda x: x.REGIONIDS[1], axis=1)
    flow_series[["SETTLEMENTDATE", "REGIONID_FROM", "REGIONID_TO", "EMISSIONS"]].to_csv(
        "~/emissions/series/{0}.csv".format(d.date()), index=None
    )

    daily_flow = pd.DataFrame(
        {
            "EXPORTS": flow_series.groupby("REGIONID_FROM").EMISSIONS.sum(),
            "IMPORTS": flow_series.groupby("REGIONID_TO").EMISSIONS.sum(),
        }
    )
    daily_flow.index.name = "REGIONID"
    daily_flow["DATE"] = d
    daily_flow.to_sql("EMISSION_FLOW", engine=DERIVED, if_exist="append")
    # daily_flow.to_("~/emissions/daily_summary.csv".format(d.date()), mode='a', header=False)


def run() -> None:
    """Runs the daily calculations for emissions"""
    return None


if __name__ == "__main__":
    run()
