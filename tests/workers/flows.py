""" Unit tests for the flows worker """

import pandas as pd

from opennem.schema.network import NetworkNEM
from opennem.utils.tests import TEST_FIXTURE_PATH
from tests.conftest import TestException


def get_flow_fixture_dataframe(filename: str) -> pd.DataFrame:
    """Get interconnector intervals for a time series"""
    fixture_path = TEST_FIXTURE_PATH / "workers" / filename

    if not fixture_path.is_file():
        raise TestException(f"Not a file {fixture_path}")

    df_gen = pd.read_csv(fixture_path, parse_dates=["trading_interval"], index_col=["trading_interval"])

    if df_gen.empty:
        raise TestException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=NetworkNEM.get_fixed_offset())

    return df_gen
