"""

OpenNEM v2 Energy Methods

"""
from datetime import date, datetime, timedelta
from typing import List, Tuple

import pandas as pd

GeneratedEnergyForDuid = Tuple[date, str, float]


def __trapezium_integration(d_ti: pd.DataFrame, power_column: str = "INITIALMW") -> float:
    """Trapezium integration fixed at 6 intervals and 30 minutes"""
    if power_column not in d_ti:
        raise Exception("No column {}".format(power_column))

    return 0.5 * (d_ti[power_column] * [1, 2, 2, 2, 2, 2, 1]).sum() / 12


def __trading_energy_generator(
    df: pd.DataFrame, duid_id: str, sel_day: date
) -> List[GeneratedEnergyForDuid]:
    df.sort_index(inplace=True)
    t_start = datetime(sel_day.year, sel_day.month, sel_day.day, 0, 5)
    generated_values = []

    # 48 trading intervals in the day
    # (could be better with groupby function)
    for TI in range(48):
        t_i = t_start + timedelta(0, 1800 * TI)
        t_f = t_start + timedelta(0, 1800 * (TI + 1))

        d_ti = df[(df.index >= t_i) & (df.index <= t_f) & (df.DUID == duid_id)]

        if not d_ti.index.empty:
            generated_values.append((d_ti.index[-2], duid_id, __trapezium_integration(d_ti)))

    return generated_values


def trading_energy_data(df: pd.DataFrame, duids: List[str], sel_day: date) -> pd.DataFrame:
    energy_genrecs = []

    for duid in duids:
        energy_genrecs += [d for d in __trading_energy_generator(df, duid, sel_day)]

    df = pd.DataFrame(energy_genrecs, columns=["SETTLEMENTDATE", "DUID", "OUTPUT_MWH"])

    return df
