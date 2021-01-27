import pytest

from opennem.utils.series import are_approx_equal


@pytest.mark.parametrize(
    ["actual", "desired", "expected"],
    [
        (3.14, 3.14, True),
        (0, 0, True),
        (5393.48, 5393.0, True),
        (5393.48, 5392.0, False),
        (100, 90, False),
        (100, 99, False),
    ],
)
def test_are_approx_equal(actual: float, desired: float, expected: bool) -> None:
    subject_value = are_approx_equal(actual, desired)
    assert subject_value == expected
