"""#771: trapezoid only between adjacent intervals. Pure Python model of the SQL plus SQL-shape checks, no database."""

from datetime import datetime, timedelta

import pytest

from opennem.monitors import energy_quality_flag as guard
from opennem.workers import energy

STEP = timedelta(minutes=5)
T0 = datetime(2026, 10, 25, 15, 20)
IPH = 12


def _sql(query) -> str:
    return " ".join(str(query).split())


def expected_energy(generated: float, prev_interval: datetime | None, prev_generated: float | None, interval: datetime) -> float:
    """Python mirror of EXPECTED_ENERGY_SQL."""
    if prev_interval is not None and prev_generated is not None and prev_interval == interval - STEP:
        return (generated + prev_generated) / 2 / IPH
    return generated / IPH


def rows_energy(rows: list[tuple[datetime, float]]) -> list[float]:
    out = []
    for i, (ts, gen) in enumerate(rows):
        prev = rows[i - 1] if i else (None, None)
        out.append(expected_energy(gen, prev[0], prev[1], ts))
    return out


def test_adjacent_rows_use_trapezoid() -> None:
    assert rows_energy([(T0, 12.0), (T0 + STEP, 24.0)])[1] == pytest.approx(18.0 / 12)


def test_gap_of_two_or_more_intervals_uses_fallback() -> None:
    # ERBL01 case: 97.69 at 15:20, next row 17:00 at 1.09
    out = rows_energy([(T0, 97.69), (datetime(2026, 10, 25, 17, 0), 1.09)])
    assert out[1] == pytest.approx(1.09 / 12)
    assert out[1] < 0.1
    assert rows_energy([(T0, 5.0), (T0 + 2 * STEP, 5.0)])[1] == pytest.approx(5.0 / 12)


def test_first_row_has_no_previous_so_fallback() -> None:
    assert rows_energy([(T0, 6.0)])[0] == pytest.approx(0.5)


def test_expected_sql_is_adjacency_aware_and_shared() -> None:
    expr = _sql(energy.EXPECTED_ENERGY_SQL)
    assert "rs.prev_interval = rs.interval - nd.interval_size * interval '1 minute'" in expr
    assert "ELSE rs.generated / nd.intervals_per_hour" in expr
    for query in (energy.ENERGY_UPDATE_QUERY, energy.ENERGY_MISMATCH_COUNT_QUERY):
        sql = _sql(query)
        assert expr in sql
        assert "LAG(interval, 1)" in sql
        # rows without an adjacent previous row are processed too (fallback, flag 2), never skipped
        assert "prev_generated IS NOT NULL" not in sql


def test_update_and_mismatch_count_agree_on_definition() -> None:
    upd = _sql(energy.ENERGY_UPDATE_QUERY)
    cnt = _sql(energy.ENERGY_MISMATCH_COUNT_QUERY)
    cond = f"abs(fs.energy - ({_sql(energy.EXPECTED_ENERGY_SQL)})) > :energy_tolerance"
    assert cond in upd and cond in cnt
    assert f"energy = {_sql(energy.EXPECTED_ENERGY_SQL)}," in upd


def test_repair_is_idempotent_in_model() -> None:
    """after the update writes the expected value, the off-definition check finds 0 and a re-run changes nothing."""
    rows = [(T0, 97.69), (datetime(2026, 10, 25, 17, 0), 1.09), (datetime(2026, 10, 25, 17, 5), 2.0)]
    stored = [g / IPH for _, g in rows]  # fallback stored by upsert
    expected = rows_energy(rows)

    def off(stored_energy: list[float]) -> int:
        return sum(abs(s - e) > energy.ENERGY_REPAIR_TOLERANCE for s, e in zip(stored_energy, expected, strict=True))

    assert off(stored) == 1  # only the adjacent trapezoid row differs from fallback
    stored = expected
    assert off(stored) == 0
    # a gap row stored at 4.116 (old bug) is off, then fixed
    assert abs(4.116 - expected[1]) > energy.ENERGY_REPAIR_TOLERANCE


def test_lookback_covers_longest_network_interval() -> None:
    params = energy._energy_params(datetime(2026, 10, 5), datetime(2026, 10, 6))
    assert params["start_time"] - params["lag_start"] >= timedelta(minutes=30)


def test_monitor_sampled_check_uses_shared_count() -> None:
    # the monitor delegates to count_energy_mismatches, so it uses the same adjacency-aware definition
    assert guard.count_energy_mismatches is energy.count_energy_mismatches
