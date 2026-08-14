"""One-way generators cannot generate negative (#613).

A negative reading on a generator's meter is site or auxiliary load measured at the same
point, not negative generation, so `unit_intervals` floors it at 0. Storage and pumps are
exempt because they really do consume as part of normal operation.

The clamp is written into the aggregate SQL, so these tests pin the two things that can
silently break it: the exempt set drifting, and the SQL losing the CASE for one of the two
query builders (the CTE is duplicated between the batch and streaming paths).
"""

import inspect
import re

from opennem.aggregates import unit_intervals
from opennem.aggregates.unit_intervals import (
    _NEGATIVE_CAPABLE_FUELTECHS,
    _NEGATIVE_CAPABLE_FUELTECHS_SQL,
)

_SOURCE = inspect.getsource(unit_intervals)


def test_only_storage_and_pumps_may_read_negative():
    """Adding a fueltech here silently republishes negative generation, so pin the set.

    Batteries are the reason the clamp can't just be `greatest(x, 0)` everywhere: charging
    is genuine consumption and floors would erase it.
    """
    assert set(_NEGATIVE_CAPABLE_FUELTECHS) == {
        "battery",
        "battery_charging",
        "battery_discharging",
        "pumps",
    }


def test_solar_rooftop_is_not_exempt():
    """Rooftop is one-way. It is gap-filled separately but must never be negative-capable."""
    assert "solar_rooftop" not in _NEGATIVE_CAPABLE_FUELTECHS


def test_sql_fragment_quotes_every_fueltech():
    """The constant is interpolated straight into an f-string SQL IN (...) list."""
    for fueltech in _NEGATIVE_CAPABLE_FUELTECHS:
        assert f"'{fueltech}'" in _NEGATIVE_CAPABLE_FUELTECHS_SQL

    assert '"' not in _NEGATIVE_CAPABLE_FUELTECHS_SQL
    assert ";" not in _NEGATIVE_CAPABLE_FUELTECHS_SQL


def test_both_query_builders_clamp_generated_and_energy():
    """The facility_data CTE is duplicated across the batch and streaming query builders.

    Patching only one leaves negatives flowing through whichever path the worker happens to
    take, which is exactly how this would regress. Both copies must carry both clamps.
    """
    generated_clamps = _SOURCE.count("ELSE greatest(round(sum(fs.generated), 4), 0)")
    energy_clamps = _SOURCE.count("ELSE greatest(round(sum(fs.energy), 4), 0)")

    assert generated_clamps == 2, f"expected both query builders to clamp generated, found {generated_clamps}"
    assert energy_clamps == 2, f"expected both query builders to clamp energy, found {energy_clamps}"


def test_no_unclamped_generated_sum_remains():
    """Catch a future edit that reintroduces a bare sum in the facility_data projection."""
    bare_projections = re.findall(r"^\s*round\(sum\(fs\.(?:generated|energy)\), 4\) as ", _SOURCE, re.MULTILINE)

    assert not bare_projections, f"unclamped projection(s) reintroduced: {bare_projections}"


def test_energy_storage_is_not_clamped():
    """energy_storage is a state-of-charge measure, not a flow, and is left alone."""
    assert "round(sum(fs.energy_storage), 4) as energy_storage" in _SOURCE
