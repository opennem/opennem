import pytest

from opennem.utils.numbers import filesize_from_string


@pytest.mark.parametrize(
    ["subject", "expected_size", "expected_units"],
    [("202.3KB", 202.3, "KB"), ("202.3 KB", 202.3, "KB"), ("202.3MB", 202.3, "MB")],
)
def test_filesize_from_string(subject: str, expected_size: float, expected_units: str) -> None:
    size, units = filesize_from_string(subject)

    assert size == expected_size, "Size matches"
    assert units == expected_units
