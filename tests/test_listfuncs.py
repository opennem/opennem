import pytest

from opennem.utils.numbers import cast_trailing_nulls


@pytest.mark.parametrize(
    "series,series_expected",
    [
        ([0.0], [0.0]),
        ([None, 0.0], [None, 0.0]),
        ([0.0, None], [0.0, 0]),
        ([0.0, None, None], [0.0, 0, 0]),
        ([0.0, None, None, 0.0], [0.0, None, None, 0.0]),
    ],
)
def test_sigfig_compact(series, series_expected):
    series_cast = cast_trailing_nulls(series)
    assert series_cast == series_expected
