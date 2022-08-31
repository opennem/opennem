import pytest

from opennem.utils.numbers import generate_random_number_series


@pytest.mark.parametrize(
    ["number_of_numbers", "expected_value"],
    [
        (30, 30),
    ],
)
def test_generate_random_number_series(number_of_numbers: int, expected_value: int) -> None:
    subject_series = generate_random_number_series(length=number_of_numbers)
    assert len(subject_series) == expected_value, "Have the correct number of random values"
