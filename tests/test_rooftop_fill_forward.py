"""Rooftop solar must be carried forward to the core-generation edge (#579).

solar_rooftop (AEMO_ROOFTOP) is a 30-min feed that lags the 5-min core-generation /
demand / price feeds. We partition it onto the 5-min grid for the aggregate joins.
Previously the partition ended at the last obtained 30-min reading:

  - unit_intervals: the solar gapfill had no explicit finish and, in the narrow
    incremental window, no real reading to seed locf (the last 30-min reading fell
    before the window start), so rooftop simply stopped early.
  - market_summary: interpolate() has no future anchor past the last real reading, so
    the trailing edge collapsed to NULL -> 0.

Either way core generation / demand kept moving forward while rooftop dropped out,
inflecting emissions and renewable_proportion at the bleeding edge.

The fix carries the last real reading forward (locf) up to the core-gen edge, bounded
to a single 30-min block (+25 min) past the last real reading so we never fabricate a
whole missing interval (that interior-gap case is #580, handled separately).

These are source-level guards (inspect.getsource) because the queries are local text()
built inside the aggregate functions and executed against a TimescaleDB session — there
is no returned SQL string to assert on without a live connection. Whitespace is
collapsed so the assertions survive reindentation / line-wrap changes.
"""

import inspect
from datetime import timedelta

from opennem.aggregates.market_summary import _get_market_summary_data
from opennem.aggregates.unit_intervals import (
    _ROOFTOP_LOOKBACK,
    _get_unit_interval_data,
    _stream_unit_interval_data,
)


def _collapse(fn) -> str:
    """Function source with all runs of whitespace collapsed to single spaces."""
    return " ".join(inspect.getsource(fn).split())


# --- unit_intervals ---------------------------------------------------------

_UNIT_INTERVAL_QUERY_FNS = [_get_unit_interval_data, _stream_unit_interval_data]


def test_unit_intervals_solar_gapfill_extends_to_end_with_lookback_seed() -> None:
    for fn in _UNIT_INTERVAL_QUERY_FNS:
        src = _collapse(fn)
        # gapfill must have an explicit window [solar_start_time, end_time] so locf can
        # carry the last reading forward to the core-gen edge (implicit bounds truncated
        # rooftop at the last real reading in the narrow incremental window).
        assert "time_bucket_gapfill('5 minutes', fs.interval, :solar_start_time, :end_time)" in src, (
            f"{fn.__name__}: rooftop gapfill must use explicit :solar_start_time/:end_time bounds (#579)"
        )
        # locf carries the 30-min reading across the 5-min grid and past the last reading.
        assert "locf(coalesce(round(sum(fs.generated), 4), 0)) as generated" in src, (
            f"{fn.__name__}: rooftop generated must be locf() carried forward (#579)"
        )


def test_unit_intervals_solar_fill_is_bounded_to_one_block() -> None:
    for fn in _UNIT_INTERVAL_QUERY_FNS:
        src = _collapse(fn)
        # per-unit last real reading, used to bound the carry-forward
        assert "max(real_interval) OVER (PARTITION BY unit_code) as max_real_interval" in src, (
            f"{fn.__name__}: must compute per-unit max real interval to bound the fill (#579)"
        )
        # never carry more than a single 30-min block past the last real reading
        assert "interval <= max_real_interval + interval '25 minutes'" in src, (
            f"{fn.__name__}: carry-forward must be bounded to +25 min (one 30-min block) (#579)"
        )
        # leading gap buckets before the first real reading are dropped (pre-existing)
        assert "interval >= min_real_interval" in src, (
            f"{fn.__name__}: must drop leading gap buckets before the first real reading (#579)"
        )


def test_unit_intervals_passes_solar_start_lookback() -> None:
    for fn in _UNIT_INTERVAL_QUERY_FNS:
        src = _collapse(fn)
        assert '"solar_start_time": start_time_naive - _ROOFTOP_LOOKBACK' in src, (
            f"{fn.__name__}: must bind solar_start_time = start - _ROOFTOP_LOOKBACK to seed locf (#579)"
        )


def test_rooftop_lookback_covers_one_rooftop_interval() -> None:
    # Must look back at least one full 30-min rooftop interval so the last real reading
    # before the window is captured as the locf seed; +5 min margin.
    assert _ROOFTOP_LOOKBACK >= timedelta(minutes=30), "rooftop lookback must cover one 30-min interval (#579)"


# --- market_summary ---------------------------------------------------------


def test_market_summary_rooftop_interpolates_interior_and_locf_tail() -> None:
    src = _collapse(_get_market_summary_data)
    # interior stays interpolated between the half-hourly points (unchanged)
    assert "interpolate(avg(fs.generated)) as rooftop_interp" in src, (
        "market_summary rooftop interior must remain interpolate() (#579)"
    )
    # trailing edge carries the last real value forward (locf) where interpolate has no
    # future anchor
    assert "locf(avg(fs.generated)) as rooftop_locf" in src, "market_summary rooftop trailing edge must locf() forward (#579)"


def test_market_summary_rooftop_fill_is_bounded_to_one_block() -> None:
    src = _collapse(_get_market_summary_data)
    assert "WHEN rooftop_interp IS NOT NULL THEN rooftop_interp" in src, (
        "market_summary must prefer the interpolated interior value when present (#579)"
    )
    assert (
        "WHEN interval <= max(real_interval) OVER (PARTITION BY network_region) + interval '25 minutes' THEN rooftop_locf"
    ) in src, "market_summary rooftop carry-forward must be bounded to +25 min (one 30-min block) (#579)"
