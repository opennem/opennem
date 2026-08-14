"""Battery capacity must be counted once (#488).

A battery is three rows in `units` carrying the same megawatts: the bidirectional unit and
the derived charging and discharging halves. Power and energy series legitimately keep both
halves, so the exclusion has to live in the capacity query specifically.
"""

from opennem.queries import capacity_history


def _unit_query() -> str:
    """The unit-level capacity query, which is the one that sums across fueltechs."""
    import inspect

    source = inspect.getsource(capacity_history.get_capacity_history)
    return source.lower()


def test_charging_half_is_excluded_from_capacity():
    """Without this every battery contributes its rating twice, 11.6 GW across NEM and WEM."""
    query = _unit_query()

    assert "'battery_charging'" in query, "capacity sum must exclude the charging half"


def test_bidirectional_row_is_still_excluded():
    """The parent row carries the same megawatts again, so it cannot come back."""
    assert "'battery'" in _unit_query()


def test_discharging_half_is_kept():
    """Battery capacity means generation capacity, consistent with every other fueltech in
    this query, so the discharging half is the one that counts."""
    query = _unit_query()

    assert "'battery_discharging'" not in query, "the discharging half must remain in the sum"


def test_power_and_energy_queries_keep_both_halves():
    """Charge and discharge are distinct flows over time. Excluding a half there would drop
    real generation, so the #488 fix must not have leaked into those queries."""
    import inspect

    from opennem.queries import energy, power

    for module in (power, energy):
        source = inspect.getsource(module)
        assert "'battery_charging'" not in source, f"{module.__name__} must keep both battery halves"
