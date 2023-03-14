import pytest

from opennem.utils.series import add_series


@pytest.mark.parametrize("expected,first,second", [([2, 4, 6], [1, 2, 3], [1, 2, 3])])
def test_add_series(expected, first, second):
    sum_value = add_series(first, second)
    assert sum_value == expected, "Values add"
