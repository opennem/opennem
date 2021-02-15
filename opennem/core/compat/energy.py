"""
OpenNEM v2 compatible version of energy sums

Uses an average in 30 minute buckets
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd
from pytz import FixedOffset

from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.compat.energy")


class ScadaResultCompat(BaseConfig):
    interval: datetime
    code: Optional[str]
    generated: Union[float, int, None]


def __trading_energy_generator(df: pd.DataFrame, duids: List[str], sel_date: datetime) -> List:
    df.sort_index(inplace=True)
    t_start = datetime(sel_date.year, sel_date.month, sel_date.day, 0, 5)

    ret_list = []
    # 48 trading intervals in the day
    # (could be better with groupby function)
    for TI in range(48):
        # t_i initial timestamp of trading_interval, t_f = final timestamp of trading interval
        t_i = t_start + timedelta(0, 1800 * TI)
        t_f = t_start + timedelta(0, 1800 * (TI + 1))

        bucket_all = df[(df.index >= t_i) & (df.index <= t_f)]

        if bucket_all.empty:
            continue

        for duid in duids:
            d_ti = bucket_all[(bucket_all.facility_code == duid)]

            if d_ti.empty or d_ti.size < 7:
                continue

            ret_list.append(
                [
                    d_ti.index[-2].replace(tzinfo=FixedOffset(600)),
                    duid,
                    d_ti.network_id.unique()[0],
                    __trapezium_integration(d_ti.generated, duid, t_i, t_f),
                ]
            )

    return ret_list


def __trapezium_integration(d_ti: pd.Series, duid: str, t_i: datetime, t_f: datetime) -> float:

    # Fall back on average but warn to check data
    if d_ti.count() <= 3:
        logger.warn(
            "For duid {} only {} values in range {} => {}".format(duid, d_ti.count(), t_i, t_f)
        )
        return 0.5 * d_ti.sum() / d_ti.count()

    bucket_middle = d_ti.count() - 2

    bucket_middle_weights = [1] + [2] * bucket_middle + [1]

    weights = d_ti.values * bucket_middle_weights

    weights_sum = weights.sum()

    bucket_energy = 0.5 * weights_sum / ((d_ti.count() - 1) * 2)

    return bucket_energy


def energy_sum_compat(gen_series: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(
        gen_series,
        columns=[
            "trading_interval",
            "facility_code",
            "network_id",
            "generated",
        ],
    )
    df.trading_interval = pd.to_datetime(df.trading_interval)
    df.generated = pd.to_numeric(df.generated)
    df = df.set_index(df.trading_interval)

    sel_date = df.index.min().date()
    max_date = df.index.max().date()

    return_list: List[Dict] = []

    sel_date = df.trading_interval.min().date()
    duids = list(df.facility_code.unique())

    while sel_date <= max_date:
        return_list += __trading_energy_generator(df, duids, sel_date)
        sel_date = sel_date + timedelta(days=1)

    return_frame = pd.DataFrame(
        return_list,
        columns=[
            "trading_interval",
            "facility_code",
            "network_id",
            "eoi_quantity",
        ],
    )

    return_frame = return_frame.set_index(return_frame.trading_interval)

    return return_frame
