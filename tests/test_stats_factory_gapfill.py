"""Calendar (month/year) gapfill in stats_factory.

Static file exports reconstruct each point's time as ``start + i*interval``, so a
source gap in a monthly/yearly series must become an explicit null — otherwise
every value after the gap shifts earlier in time and the tail blanks out
(issue #548, the NSW1 May gas_ocgt mismatch). The live API opts out via
``fill_monthly_gaps=False`` because it returns sparse x,y where missing periods
are expected.
"""

from datetime import datetime

from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemDataSet
from opennem.api.time import human_to_interval
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit


def _run(rows: list[tuple[datetime, float | None]], interval_human: str, fill_monthly_gaps: bool = True) -> OpennemDataSet:
    """Build a single-group series and push it through stats_factory."""
    network = network_from_network_code("NEM")
    stats = [DataQueryResult(interval=dt, result=v, group_by="gas_ocgt") for dt, v in rows]

    result = stats_factory(
        stats,
        code="NSW1",
        network=network,
        interval=human_to_interval(interval_human),
        units=get_unit("energy_giga"),
        region="NSW1",
        fueltech_group=True,
        fill_monthly_gaps=fill_monthly_gaps,
    )

    if not result or not result.data:
        raise Exception("Bad unit test data — no result")

    return result


def test_monthly_gap_is_filled_and_aligned() -> None:
    """A missing month becomes an explicit null so later values stay aligned."""
    rows = [
        (datetime(2024, 1, 1), 10.0),
        (datetime(2024, 2, 1), 20.0),
        # 2024-03 missing in source
        (datetime(2024, 4, 1), 40.0),
    ]

    history = _run(rows, "1M").data[0].history

    assert history.interval == "1M"
    assert len(history.data) == 4, "Jan..Apr inclusive = 4 monthly slots"
    assert history.data == [10.0, 20.0, None, 40.0], "March is an explicit null, April stays at index 3"

    # the contract consumers rely on: data[i] is at start + i months
    assert history.start.year == 2024 and history.start.month == 1
    assert history.last.year == 2024 and history.last.month == 4


def test_monthly_gap_reproduces_issue_548_offset() -> None:
    """Without the gap, the trailing value would land a month too early."""
    rows = [
        (datetime(2024, 1, 1), 10.0),
        (datetime(2024, 2, 1), 20.0),
        (datetime(2024, 4, 1), 40.0),
    ]

    filled = _run(rows, "1M", fill_monthly_gaps=True).data[0].history
    sparse = _run(rows, "1M", fill_monthly_gaps=False).data[0].history

    # April's value sits at the April index when filled (3), but at the March
    # index (2) when sparse — exactly the misalignment behind issue #548.
    assert filled.data.index(40.0) == 3
    assert sparse.data.index(40.0) == 2


def test_api_opt_out_keeps_series_sparse() -> None:
    """The live API (fill_monthly_gaps=False) leaves gaps absent, not null."""
    rows = [
        (datetime(2024, 1, 1), 10.0),
        (datetime(2024, 2, 1), 20.0),
        (datetime(2024, 4, 1), 40.0),
    ]

    history = _run(rows, "1M", fill_monthly_gaps=False).data[0].history

    assert len(history.data) == 3, "No null inserted for the missing month"
    assert history.data == [10.0, 20.0, 40.0]


def test_contiguous_monthly_series_unchanged() -> None:
    """A dense series (no gaps) is identical with or without gapfill."""
    rows = [
        (datetime(2024, 1, 1), 10.0),
        (datetime(2024, 2, 1), 20.0),
        (datetime(2024, 3, 1), 30.0),
    ]

    filled = _run(rows, "1M", fill_monthly_gaps=True).data[0].history
    sparse = _run(rows, "1M", fill_monthly_gaps=False).data[0].history

    assert filled.data == [10.0, 20.0, 30.0]
    assert filled.data == sparse.data


def test_yearly_gap_is_filled() -> None:
    """Year stepping fills a missing calendar year with a null."""
    rows = [
        (datetime(2020, 1, 1), 100.0),
        # 2021 missing
        (datetime(2022, 1, 1), 300.0),
    ]

    history = _run(rows, "1Y").data[0].history

    assert history.interval == "1Y"
    assert history.data == [100.0, None, 300.0]


def test_misaligned_keys_are_not_regridded() -> None:
    """Irregular keys (not on a uniform month step) are preserved, not dropped."""
    rows = [
        (datetime(2024, 1, 1), 10.0),
        (datetime(2024, 2, 15), 20.0),  # off the Jan-01 monthly grid
    ]

    history = _run(rows, "1M").data[0].history

    # guard skips gapfill rather than dropping the unaligned point
    assert history.data == [10.0, 20.0]
