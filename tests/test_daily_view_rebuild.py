"""Daily view rebuild after a historical backlog run (#592).

The fueltech/renewable daily views version rows by completeness, so a write landing on a
day they already hold loses the comparison and is discarded. Any backlog run therefore has
to rebuild them for the same window — except on the few-minute hot paths, where the rebuild
would cost far more than the write and the daily catchup covers the same days anyway.
"""

import inspect

from opennem.aggregates import unit_intervals


def test_rebuild_is_the_default():
    """A caller who doesn't think about it must get the safe behaviour."""
    sig = inspect.signature(unit_intervals.process_unit_intervals_backlog)

    assert sig.parameters["rebuild_daily_views"].default is True


def test_only_the_completeness_versioned_views_are_rebuilt():
    """unit_intervals_daily_mv is keyed per unit so it can't go stale — rebuilding it would
    be wasted work on every backlog run."""
    assert unit_intervals._DAILY_VIEWS_NEEDING_REBUILD == [
        "fueltech_intervals_daily_mv",
        "renewable_intervals_daily_mv",
    ]


def test_hot_paths_opt_out():
    """The 5-minute WEM tasks must not trigger a rebuild on every run."""
    source = inspect.getsource(unit_intervals)  # noqa: F841  (kept for symmetry / debugging)

    from opennem.tasks import tasks

    task_source = inspect.getsource(tasks)
    wem_calls = task_source.count("rebuild_daily_views=False")

    assert wem_calls == 2, f"expected both WEM interval tasks to opt out, found {wem_calls}"


def test_catchup_opts_out_because_it_rebuilds_everything_itself():
    from opennem.workers import catchup

    source = inspect.getsource(catchup)

    assert "rebuild_daily_views=False" in source
    assert "backfill_materialized_views" in source
