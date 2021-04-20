import pytest

from opennem.utils.numbers import sigfig_compact, trim_nulls


@pytest.mark.parametrize(
    "number,number_expected",
    [
        (0, 0),
        (0.0, 0),
        (1, 1),
        (1.0, 1),
        (-1.0, -1),
        (0.012, 0.012),
        (-0.012, -0.012),
        (123.01, 123),
        (1234.9, 1235),
        (123.49, 123.5),
        (12.349, 12.35),
        (1.2349, 1.235),
        (0.12349, 0.1235),
        (12.00001, 12),
        (12.3456, 12.35),
        (0.000087654, 0.00008765),
        (0.000087657, 0.00008766),
        (1234567.89, 1234567),
        (-1234567.89, -1234567),
    ],
)
def test_sigfig_compact(number: float, number_expected: float) -> None:
    number = sigfig_compact(number, 4)
    assert number == number_expected


def test_trim_nulls() -> None:
    subject = {"a": None, "b": 1, "c": None}

    expected = {"b": 1}

    res = trim_nulls(subject)

    assert res == expected, "Got expected return"
