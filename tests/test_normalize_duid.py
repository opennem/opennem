import pytest

from opennem.core.normalizers import normalize_duid


@pytest.mark.parametrize(
    ["duid", "duid_expected"],
    [
        ("TARONG#1", "TARONG#1"),
        ("V-S-MNSP1", "V-S-MNSP1"),
        (
            " LIMOSF11\
 ",
            "LIMOSF11",
        ),
    ],
)
def test_duid_cleaner(duid: str, duid_expected: str) -> None:
    duid_return = normalize_duid(duid)
    assert duid_return == duid_expected, "Matched duid"
