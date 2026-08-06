"""Regression tests for #607: v3 export curtailment energy must be GWh.

The v3 static export declares every energy series as GWh and the tracker
frontend applies one GWh scale to the whole dataset, so the curtailment query
must scale MWh storage down and the export units must resolve to GWh without
changing the exported series ids (built from unit name_alias).
"""

from datetime import datetime

import pytest

from opennem.core.units import get_unit
from opennem.queries.curtailment import get_network_curtailment_energy_query_analytics
from opennem.schema.network import NetworkNEM, NetworkWEM


def test_curtailment_energy_query_scales_to_gwh() -> None:
    query = get_network_curtailment_energy_query_analytics(
        network=NetworkNEM,
        date_min=datetime(2026, 1, 1),
        date_max=datetime(2026, 2, 1),
        network_region_code="VIC1",
    )

    assert "round(sum(curtailment_energy_total) / 1000, 4)" in query
    assert "round(sum(curtailment_energy_solar_total) / 1000, 4)" in query
    assert "round(sum(curtailment_energy_wind_total) / 1000, 4)" in query


def test_curtailment_energy_query_rejects_non_nem() -> None:
    with pytest.raises(ValueError):
        get_network_curtailment_energy_query_analytics(network=NetworkWEM, date_min=datetime(2026, 1, 1))


@pytest.mark.parametrize(
    "unit_name,alias",
    [
        ("curtailment_solar_utility_energy_giga", "curtailment.solar.utility.energy"),
        ("curtailment_wind_energy_giga", "curtailment.wind.energy"),
    ],
)
def test_curtailment_export_units_are_giga_with_original_alias(unit_name: str, alias: str) -> None:
    unit = get_unit(unit_name)

    assert unit.unit == "GWh"
    assert unit.unit_type == "energy"
    # the alias builds the v3 series id (au.nem.<region>.<alias>) — it must not change
    assert unit.name_alias == alias
