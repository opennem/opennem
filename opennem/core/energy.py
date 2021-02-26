# pylint: disable=no-self-argument
"""
OpenNEM Energy Tools

Uses an average in 30 minute buckets

@TODO variable bucket sizes

"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.compat.energy")


class ScadaResultCompat(BaseConfig):
    interval: datetime
    code: Optional[str]
    generated: Union[float, int, None]


def _trapezium_integration_variable(d_ti: pd.Series) -> float:
    """Gapfill version of trap int - will fill out"""
    # Clear no numbers
    d_ti = d_ti.dropna()

    # Fall back on average but warn to check data
    if d_ti.count() <= 3:
        d_sum = d_ti.sum()

        if d_sum == 0:
            return 0

        if d_ti.count() == 0:
            return 0

        return 0.5 * d_sum / d_ti.count()

    bucket_middle = d_ti.count() - 2

    bucket_middle_weights = [1] + [2] * bucket_middle + [1]

    weights = d_ti.values * bucket_middle_weights

    weights_sum = weights.sum()

    bucket_energy = 0.5 * weights_sum / ((d_ti.count() - 1) * 2)

    return bucket_energy


def _trapezium_integration(d_ti: pd.Series, gapfill: bool = False) -> Optional[float]:
    """ Energy for a 30 minute bucket """
    # Clear no numbers
    d_ti = d_ti.dropna()

    # Early return
    if d_ti.sum() == 0:
        return 0.0

    # Fall back on average but warn to check data
    if d_ti.count() != 7:
        # logger.error("Series {} has gaps".format(d_ti))

        if gapfill:
            return _trapezium_integration_variable(d_ti)

        return None

    weights = d_ti.values * [1, 2, 2, 2, 2, 2, 1]

    weights_sum: float = weights.sum()

    bucket_energy = 0.5 * weights_sum / 12

    return bucket_energy


def _energy_aggregate(df: pd.DataFrame, network: NetworkSchema) -> pd.DataFrame:
    """Energy aggregate that buckets into 30min intervals
    but takes edges in for 7 total values"""
    in_cap = {}
    capture: Dict[str, Any] = {}
    values = []
    dt: Optional[datetime] = None
    reading_stops: List[int] = [0, 30]

    for index, value in df.iterrows():
        i, network_id, duid = index

        if duid not in capture:
            capture[duid] = []
            in_cap[duid] = True

        if in_cap[duid]:
            capture[duid].append(value.eoi_quantity)

            if dt:
                energy = _trapezium_integration(pd.Series(capture[duid]), True)
                values.append((dt, network_id, duid, energy))

            in_cap[duid] = False
            capture[duid] = []

        if i.minute in reading_stops:
            dt = i
            capture[duid].append(value.eoi_quantity)
            in_cap[duid] = True

        else:
            capture[duid].append(value.eoi_quantity)

    return pd.DataFrame(
        values, columns=["trading_interval", "network_id", "facility_code", "eoi_quantity"]
    )


def energy_sum(gen_series: List[Dict], network: NetworkSchema) -> pd.DataFrame:
    """Takes the energy sum for a series of raw duid intervals
    and returns a fresh dataframe to be imported"""
    df = pd.DataFrame(
        gen_series,
        columns=[
            "trading_interval",
            "facility_code",
            "network_id",
            "eoi_quantity",
        ],
    )

    # Clean up types
    df.trading_interval = pd.to_datetime(df.trading_interval)
    df.eoi_quantity = pd.to_numeric(df.eoi_quantity)

    # Index by datetime
    df = df.set_index(["trading_interval", "network_id", "facility_code"])

    # Multigroup by datetime and facility code
    df = _energy_aggregate(df, network=network)

    # Reset back to a simple frame
    df = df.reset_index()

    # Shift back 5 minutes to even up into 30 minute bkocks
    if network.reading_shift:
        df.trading_interval = df.trading_interval - pd.Timedelta(minutes=network.reading_shift)

    # Add back the timezone for NEM
    # We use a fixed offset so need to loop
    df.trading_interval = df.apply(
        lambda x: pd.Timestamp(x.trading_interval, tz=network.get_fixed_offset()), axis=1
    )

    # filter out empties
    df = df[pd.isnull(df.eoi_quantity) == False]

    return df
