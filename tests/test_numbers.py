import pytest

from opennem.utils.numbers import to_precision


@pytest.mark.parametrize(
    "number,number_expected",
    [
        (0.0, 0),
        (0.012, 0.012),
        (-0.012, -0.012),
        (12.00001, 12),
        (12.3456, 12.35),
        # (0.000087654, 0.00008765),
        (0.000087654, 0.0001),
        (1234567.89, 1234567),
    ],
)
def test_number_precision(number, number_expected):
    number = to_precision(number, 4)
    assert number == number_expected
