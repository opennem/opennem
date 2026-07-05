from datetime import datetime

import pytest

from opennem.importer.rooftop import rooftop_remap_regionids
from opennem.queries.power import _floor_to_30min, get_rooftop_forecast_generation_query
from opennem.schema.network import NetworkNEM


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


@pytest.mark.parametrize(
    "dt,expected",
    [
        (datetime(2026, 6, 25, 8, 45, 0), datetime(2026, 6, 25, 8, 30, 0)),
        (datetime(2026, 6, 25, 8, 30, 0), datetime(2026, 6, 25, 8, 30, 0)),
        (datetime(2026, 6, 25, 8, 0, 0), datetime(2026, 6, 25, 8, 0, 0)),
        (datetime(2026, 6, 25, 8, 29, 59, 500000), datetime(2026, 6, 25, 8, 0, 0)),
        (datetime(2026, 6, 25, 8, 59, 0), datetime(2026, 6, 25, 8, 30, 0)),
    ],
)
def test_floor_to_30min(dt: datetime, expected: datetime) -> None:
    assert _floor_to_30min(dt) == expected


def test_rooftop_forecast_query_snaps_window_to_30min() -> None:
    """Forecast window bounds must snap to the 30-min AEMO rooftop grid so the
    5-min gapfill/interpolate has an anchor at each edge (no leading/trailing
    nulls — #580)."""
    query = str(
        get_rooftop_forecast_generation_query(
            network=NetworkNEM,
            date_start=datetime(2026, 6, 25, 8, 45, 0),
            date_end=datetime(2026, 6, 26, 8, 45, 0),
        )
    )
    assert "2026-06-25 08:30:00" in query
    assert "2026-06-26 08:30:00" in query
    assert "08:45:00" not in query
