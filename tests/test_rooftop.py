import pytest

from opennem.importer.rooftop import remap_aemo_region


@pytest.mark.parametrize(
    "region_code,region_code_expected",
    [
        ("NSW1", "NSW1"),
        ("QLD1", "QLD1"),
        ("QLDC", "QLD1"),
        ("QLDN", "QLD1"),
        ("QLDS", "QLD1"),
        ("SA1", "SA1"),
        ("TAS1", "TAS1"),
        ("TASN", "TAS1"),
        ("TASS", "TAS1"),
        ("VIC1", "VIC1"),
    ],
)
def test_remap_region_code(region_code: str, region_code_expected: str) -> None:
    region_code_remapped = remap_aemo_region(region_code)
    assert region_code_remapped == region_code_expected
