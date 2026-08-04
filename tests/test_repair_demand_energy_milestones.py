"""Guards on the #605 demand energy milestone repair script.

The purge is pattern-based (`%.demand.energy.%`) but the rebuild is period-scoped (day and up).
Nothing currently lives outside that set, but if a `season` or `week` demand energy record ever
appears the purge would delete rows the rebuild cannot regenerate, and the loss is unrecoverable.
`_assert_purge_matches_rebuild` turns that into a hard failure before anything is deleted.
"""

import pytest

from bin.repair_demand_energy_milestones import (
    REBUILD_PERIODS,
    _assert_purge_matches_rebuild,
    _assert_rebuild_sane,
)


def test_accepts_the_periods_actually_present() -> None:
    # what prod and dev both hold today
    _assert_purge_matches_rebuild(["day", "month", "quarter", "year"])


def test_accepts_a_subset() -> None:
    _assert_purge_matches_rebuild(["day"])


def test_accepts_nothing_to_purge() -> None:
    _assert_purge_matches_rebuild([])


@pytest.mark.parametrize("orphan", ["season", "week", "week_rolling", "interval", "<null>"])
def test_rejects_a_period_the_rebuild_cannot_regenerate(orphan: str) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _assert_purge_matches_rebuild(["day", "month", orphan])

    assert orphan in str(excinfo.value)


def test_rebuild_periods_are_day_and_up() -> None:
    # the interval period is demand power in MW and must never enter the rebuild set, or the
    # script would regenerate records the purge deliberately leaves alone
    assert [period.value for period in REBUILD_PERIODS] == ["day", "month", "quarter", "year"]


def test_rebuild_sane_accepts_a_clean_rebuild() -> None:
    _assert_rebuild_sane(["MWh"], stored=161, attempted=161)


@pytest.mark.parametrize("units", [["MW"], ["MW", "MWh"], ["GWh"], []])
def test_rebuild_sane_rejects_any_unit_but_mwh(units: list[str]) -> None:
    # the whole point of the repair is a single-unit series — anything else means the backlog unit
    # fix did not take, so fail rather than leave a mixed series in place
    with pytest.raises(SystemExit):
        _assert_rebuild_sane(units, stored=161, attempted=161)


def test_rebuild_sane_rejects_an_empty_series() -> None:
    with pytest.raises(SystemExit, match="backfill"):
        _assert_rebuild_sane(["MWh"], stored=0, attempted=0)


def test_rebuild_sane_rejects_rows_the_rebuild_did_not_produce() -> None:
    # the incremental worker racing the purge/rebuild window
    with pytest.raises(SystemExit, match="incremental"):
        _assert_rebuild_sane(["MWh"], stored=164, attempted=161)


def test_rebuild_sane_rejects_dropped_rows() -> None:
    with pytest.raises(SystemExit, match="dropped on insert"):
        _assert_rebuild_sane(["MWh"], stored=150, attempted=161)
