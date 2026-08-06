"""E2E data-integrity checks for the PG -> ClickHouse aggregation pipeline.

Guards against silent aggregate corruption of the kind found in the rooftop
catchup incident (2026-03-18 -> 2026-07-07): the 2-hourly catchup_aggregates
task re-aggregated a 12h window whose start fell off the 30-min rooftop grid,
locf() had no seed for the first three 5-min buckets, and the query emitted
NULL rows that clobbered previously-good values under ReplacingMergeTree
(newest version wins). Result: rooftop energy silently under-reported by
~12.5%/day for months, while exports stayed perfectly consistent with CH —
only a comparison against the PostgreSQL source data could catch it.

The check logic lives in opennem.workers.data_integrity and also runs daily on
the worker (task_data_integrity_check) with Slack alerting. These tests run the
same checks against live databases (dev by default via the standard env
config) and are skipped unless RUN_E2E=1 is set:

    RUN_E2E=1 uv run pytest tests/e2e/test_pipeline_data_integrity.py -v
"""

import os

import pytest

pytestmark = [
    pytest.mark.skipif(os.environ.get("RUN_E2E") != "1", reason="e2e: set RUN_E2E=1 to run against live databases"),
    pytest.mark.asyncio,
]


def _window():
    from opennem.workers.data_integrity import get_check_window

    return get_check_window()


async def test_rooftop_no_null_rows_in_settled_range() -> None:
    """No NULL energy/generated rooftop rows in CH inside the settled window."""
    from opennem.workers.data_integrity import check_rooftop_null_rows

    start, end = _window()
    failures = await check_rooftop_null_rows(start, end)
    assert not failures, "NULL rooftop rows in unit_intervals:\n" + "\n".join(failures)


async def test_rooftop_ch_daily_energy_matches_pg_source() -> None:
    """CH rooftop daily energy per facility must match PG facility_scada (source of truth)."""
    from opennem.workers.data_integrity import check_rooftop_ch_vs_pg

    start, end = _window()
    failures = await check_rooftop_ch_vs_pg(start, end)
    assert not failures, "CH rooftop diverges from PG source:\n" + "\n".join(failures)


async def test_rooftop_daily_mv_matches_base_table() -> None:
    """fueltech_intervals_daily_mv (feeds the energy exports) must agree with unit_intervals."""
    from opennem.workers.data_integrity import check_rooftop_daily_mv_vs_base

    start, end = _window()
    failures = await check_rooftop_daily_mv_vs_base(start, end)
    assert not failures, "daily MV diverges from unit_intervals base:\n" + "\n".join(failures)
