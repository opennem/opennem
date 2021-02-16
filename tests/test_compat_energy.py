from typing import List, Union

import pandas as pd
import pytest

from opennem.core.compat.energy import __trapezium_integration_gapfill


@pytest.mark.parametrize(
    ["series", "expected_value"],
    [
        ([1], 0.5),
        ([1, 1], 0.5),
        ([1, 1, 1], 0.5),
        ([1, 1, 1], 0.5),
        ([1, 1, 1, 1], 0.5),
        ([1, 1, 1, 1, 1], 0.5),
        ([1, 1, 1, 1, 1, 1], 0.5),
        ([1, 1, 1, 1, 1, 1, 1], 0.5),
        ([1, 1, 1, 1, 1, 1, 1, 1], 0.5),
        ([1, 1, 1, 1, 1, 1, 1, 1, None], 0.5),
    ],
)
def test_trap_gapfill(series: List[Union[float, int]], expected_value: int):
    value = __trapezium_integration_gapfill(pd.Series(series))

    assert value == expected_value
