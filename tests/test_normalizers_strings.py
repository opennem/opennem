import pytest

from opennem.core.normalizers import replace_accented


@pytest.mark.parametrize(
    "subject,expected",
    [
        ("", ""),
        ("test", "test"),
        ("ñ", "n"),
        ("ññ", "nn"),
        ("test_þ", "test_th"),
        ("test_þþ", "test_thth"),
    ],
)
def test_replace_accented(subject: str, expected: str) -> None:
    assert replace_accented(subject) == expected, "Replaces accented correctly"
