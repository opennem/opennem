import pytest

from opennem.importer.rooftop import rooftop_remap_regionids


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
    # we no longer remap rooftop regions
    pass


@pytest.mark.parametrize(
    "rooftop_record,rooftop_record_expected",
    [
        ({"facility_code": "NSW1"}, {"facility_code": "ROOFTOP_NEM_NSW"}),
        ({"facility_code": "QLD1"}, {"facility_code": "ROOFTOP_NEM_QLD"}),
    ],
)
def test_rooftop_remap_regionids(rooftop_record: dict, rooftop_record_expected: dict) -> None:
    rooftop_record_remapped = rooftop_remap_regionids(rooftop_record)
    assert rooftop_record_remapped == rooftop_record_expected
