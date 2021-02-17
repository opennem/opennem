from typing import List, Union

import pandas as pd
import pytest

from opennem.core.compat.energy import bucket_average_fill


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
def test_trap_gapfill(series: List[Union[float, int]], expected_value: int) -> None:
    value = bucket_average_fill(pd.Series(series))

    assert value == expected_value
