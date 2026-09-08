#!/usr/bin/env uv run
"""Divide the 6x-inflated WEM energy columns in ClickHouse `market_summary` and drop the duplicate
WEMDE region rows.

`_prepare_market_summary_data` turned the trapezoid MW average into MWh by dividing by an
intervals-per-hour value it looked up per network: 12 for NEM, 2 for WEM. But `_get_market_summary_data`
gapfills every network onto a `time_bucket_gapfill('5 minutes', ...)` grid — WEM included, right back
to its first rows in 2011 — so a WEM row covers five minutes, not the thirty its trading cadence
suggests. Every WEM energy column, and the three market values derived from them, therefore came out
6x high: 105 TWh a year of demand energy against a true ~18 TWh.

The same query's `regions` CTE was `SELECT DISTINCT network_id, network_region FROM balancing_summary`,
which emitted two region rows that are not markets of their own:

- WEM/WEMDE — the WEMDE dispatch feed lands under the WEM network with its own region label. Demand
  for it is joined from the network-wide `wem_generation` CTE, so it is a byte-for-byte duplicate of
  WEM/WEM and doubles every network-level WEM sum over its window. A 2024-02-19 daily demand energy
  milestone came out at exactly 2x because of it.
- NEM/WEM — long-standing bad data with null demand, called out in CLAUDE.md.

This script repairs the data that code fix leaves behind. It is NOT a substitute for deploying the
fix first: an old worker still writing 6x rows will re-inflate the table.

REQUIRED RUN ORDER
------------------
1. deploy the market_summary fix and let the ARQ workers cycle
2. run this script (dry run, then --apply)
3. rebuild the milestones table — every `au.wem.demand.energy.*` record was derived from these
   values, so they are all 6x too, and the WEMDE window's are doubled on top of that

Usage:
    uv run bin/repair_wem_market_summary_energy.py
    uv run bin/repair_wem_market_summary_energy.py --apply
    ENV=production uv run bin/repair_wem_market_summary_energy.py
    ENV=production uv run bin/repair_wem_market_summary_energy.py --apply
"""

import argparse
import logging
import time
from datetime import datetime
from typing import Any, cast

from clickhouse_driver.client import Client

from opennem.db.clickhouse import get_clickhouse_client
from opennem.db.clickhouse.materialized_views import backfill_materialized_view
from opennem.db.clickhouse.views import MARKET_SUMMARY_DAILY_VIEW, MARKET_SUMMARY_MONTHLY_VIEW

logger = logging.getLogger("opennem.bin.repair_wem_market_summary_energy")

# The rows that hold the real WEM market series and carry the inflated energy.
WEM_NETWORK_ID = "WEM"
WEM_NETWORK_REGION = "WEM"

# Region rows that should never have existed. Deleted outright, not rescaled.
BOGUS_NETWORK_REGIONS = [
    ("WEM", "WEMDE"),
    ("NEM", "WEM"),
]

# Everything computed from the trapezoid MW average, plus the market values that multiply it by
# price. They all took the same divisor, so they all carry the same factor.
INFLATED_COLUMNS = [
    "demand_energy",
    "demand_total_energy",
    "demand_gross_energy",
    "generation_renewable_energy",
    "generation_renewable_with_storage_energy",
    "curtailment_energy_solar_total",
    "curtailment_energy_wind_total",
    "curtailment_energy_total",
    "demand_market_value",
    "demand_total_market_value",
    "demand_gross_market_value",
]

# 30-minute divisor over 5-minute rows: 12 / 2.
INFLATION_FACTOR = 6.0

# Ratio of stored energy to the energy the MW column implies. Wide enough to absorb rows where
# demand and demand_energy disagree at the gapfilled edges, narrow enough that an already-repaired
# table (ratio 1) or a partially-repaired one is refused.
RATIO_BEFORE = (5.5, 6.5)
RATIO_AFTER = (0.9, 1.1)

# WEM market_summary starts 2011-12. Used as a floor only — the real start comes from the data.
MV_BACKFILL_FLOOR = datetime(2011, 12, 1)
MV_CHUNK_SIZE_DAYS = 240

MUTATION_POLL_SECONDS = 5
MUTATION_TIMEOUT_SECONDS = 3600


def _query(client: Client, sql: str, params: dict[str, Any] | None = None) -> list[tuple[Any, ...]]:
    """clickhouse-driver types execute() as a wide union that includes int and streaming results.

    Every query here is a plain SELECT returning rows, so narrow it once rather than at each call.
    """
    return cast(list[tuple[Any, ...]], client.execute(sql, params))


def _wem_yearly_ratios(client: Client, max_interval: datetime | None = None) -> list[tuple[int, int, float, float, float]]:
    """Per year: row count, stored demand energy, the energy sum(demand)/12 implies, and the ratio.

    FINAL is scoped to the WEM region rows. Without it, unmerged ReplacingMergeTree duplicates are
    counted twice — harmless for the ratio, which they scale on both sides, but the absolute totals
    printed for the operator would be wrong.

    `max_interval` bounds the check to the rows the repair will actually touch, so already-correct
    rows written after the code fix deployed do not drag the pre-flight ratios down.
    """
    bound = "AND interval <= %(max_interval)s" if max_interval is not None else ""

    rows = _query(
        client,
        f"""
        SELECT
            toYear(interval) AS year,
            count() AS rows,
            sum(demand_energy) AS stored_energy,
            sum(demand) / 12 AS implied_energy,
            sum(demand_energy) / nullIf(sum(demand) / 12, 0) AS ratio
        FROM market_summary FINAL
        WHERE network_id = %(network_id)s AND network_region = %(network_region)s
        {bound}
        GROUP BY year
        ORDER BY year
        """,
        {
            "network_id": WEM_NETWORK_ID,
            "network_region": WEM_NETWORK_REGION,
            "max_interval": max_interval,
        },
    )

    return [(row[0], row[1], row[2] or 0.0, row[3] or 0.0, row[4]) for row in rows]


def _inflated_row_span(client: Client) -> tuple[int, datetime | None]:
    """Count the rows still carrying the 6x signature, and the latest interval among them.

    A row's own numbers give it away. `demand_energy` is the trapezoid mean of `demand` and the
    previous interval's demand divided by intervals-per-hour, so on a correct row it sits near
    demand/12 and on an inflated one near demand/2. Measured across the whole WEM series the
    inflated ratio spans 0.42 to 0.64, and a correct row cannot exceed about 0.11, so the midpoint
    of 0.25 separates them with an order of magnitude to spare.

    The latest inflated interval is the cutoff for the UPDATE. Rows above it were written by the
    fixed code after it deployed and must not be divided. Old-code rows form a contiguous prefix:
    market_summary is a ReplacingMergeTree keyed on (interval, network_id, network_region), so a
    re-aggregated interval supersedes its old value rather than sitting beside it.
    """
    rows = _query(
        client,
        """
        SELECT count(), max(interval)
        FROM market_summary FINAL
        WHERE network_id = %(network_id)s
          AND network_region = %(network_region)s
          AND demand > 0
          AND demand_energy > demand / 4
        """,
        {"network_id": WEM_NETWORK_ID, "network_region": WEM_NETWORK_REGION},
    )

    if not rows or not rows[0][0]:
        return 0, None

    return int(rows[0][0]), cast(datetime, rows[0][1])


def _wem_rows_after(client: Client, interval: datetime) -> int:
    """WEM/WEM rows past the repair cutoff, left untouched."""
    rows = _query(
        client,
        """
        SELECT count()
        FROM market_summary FINAL
        WHERE network_id = %(network_id)s AND network_region = %(network_region)s AND interval > %(interval)s
        """,
        {"network_id": WEM_NETWORK_ID, "network_region": WEM_NETWORK_REGION, "interval": interval},
    )

    return int(rows[0][0]) if rows else 0


def _bogus_region_counts(client: Client) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}

    for network_id, network_region in BOGUS_NETWORK_REGIONS:
        result = _query(
            client,
            """
            SELECT count()
            FROM market_summary
            WHERE network_id = %(network_id)s AND network_region = %(network_region)s
            """,
            {"network_id": network_id, "network_region": network_region},
        )
        counts[(network_id, network_region)] = result[0][0] if result else 0

    return counts


def _affected_min_interval(client: Client) -> datetime | None:
    """Earliest interval across every row this script touches — the floor for the MV rebuild."""
    pairs = [(WEM_NETWORK_ID, WEM_NETWORK_REGION), *BOGUS_NETWORK_REGIONS]
    predicate = " OR ".join(
        f"(network_id = '{network_id}' AND network_region = '{network_region}')" for network_id, network_region in pairs
    )

    result = _query(client, f"SELECT min(interval) FROM market_summary WHERE {predicate}")

    if not result or result[0][0] is None:
        return None

    return cast(datetime, result[0][0])


def _log_yearly_table(rows: list[tuple[int, int, float, float, float]], heading: str) -> None:
    logger.info(heading)
    logger.info(f"  {'year':>6}  {'rows':>9}  {'demand_energy TWh':>18}  {'sum(demand)/12 TWh':>19}  {'ratio':>6}")

    for year, count, stored, implied, ratio in rows:
        ratio_text = f"{ratio:.3f}" if ratio is not None else "n/a"
        logger.info(f"  {year:>6}  {count:>9,}  {stored / 1_000_000:>18.2f}  {implied / 1_000_000:>19.2f}  {ratio_text:>6}")


def _assert_ratios_within(rows: list[tuple[int, int, float, float, float]], bounds: tuple[float, float], stage: str) -> None:
    """Fail unless every year's ratio sits in the expected band.

    Before the update this is the idempotence guard: a table already divided reads ~1 and must not be
    divided again. After it, it is the proof the mutation landed on every year rather than some.
    """
    low, high = bounds
    offenders = [(year, ratio) for year, _, _, _, ratio in rows if ratio is None or not low <= ratio <= high]

    if not rows:
        raise SystemExit("No WEM market_summary rows found — nothing to repair, check the environment")

    if offenders:
        formatted = ", ".join(f"{year}={ratio if ratio is None else round(ratio, 3)}" for year, ratio in offenders)
        raise SystemExit(
            f"{stage}: expected every year's stored/implied demand energy ratio in [{low}, {high}] but got {formatted}. "
            f"Refusing to continue — a ratio near 1 means the repair has already run, and anything else means the "
            f"inflation is not the uniform {INFLATION_FACTOR}x this script assumes."
        )


def _wait_for_mutations(client: Client, known_before: set[str]) -> None:
    """Block until every mutation this run submitted against market_summary has finished.

    The MV rebuild re-aggregates from market_summary, so it must not start while the rewrite is
    still in flight or it would bake the old values straight back into the views.
    """
    deadline = time.monotonic() + MUTATION_TIMEOUT_SECONDS

    while True:
        rows = _query(
            client,
            """
            SELECT mutation_id, is_done, latest_fail_reason, parts_to_do
            FROM system.mutations
            WHERE database = currentDatabase() AND table = 'market_summary'
            """,
        )

        ours = [row for row in rows if row[0] not in known_before]
        failed = [(row[0], row[2]) for row in ours if row[2]]

        if failed:
            raise SystemExit(f"ClickHouse mutation failed: {failed}")

        pending = [(row[0], row[3]) for row in ours if not row[1]]

        if not pending:
            logger.info(f"All {len(ours)} mutation(s) complete")
            return

        if time.monotonic() > deadline:
            raise SystemExit(
                f"Mutations still running after {MUTATION_TIMEOUT_SECONDS}s: {pending}. They will finish on their own — "
                f"re-run the materialized view rebuild once system.mutations reports is_done."
            )

        logger.info(f"Waiting on {len(pending)} mutation(s), parts remaining: {[parts for _, parts in pending]}")
        time.sleep(MUTATION_POLL_SECONDS)


def _existing_mutation_ids(client: Client) -> set[str]:
    """Snapshot the table's mutations, refusing to start while any are still running.

    Two overlapping runs would each pass the pre-flight check — the first run's UPDATE is not
    visible until its mutation materialises — and each submit a divide-by-six, leaving WEM 36x low.
    An unfinished mutation is the one observable sign of that, so it is fatal rather than a warning.
    """
    rows = _query(
        client,
        """
        SELECT mutation_id, is_done
        FROM system.mutations
        WHERE database = currentDatabase() AND table = 'market_summary'
        """,
    )

    unfinished = [row[0] for row in rows if not row[1]]

    if unfinished:
        raise SystemExit(
            f"market_summary has {len(unfinished)} unfinished mutation(s): {unfinished}. Another repair may be "
            f"mid-flight — wait for system.mutations to report is_done for all of them before running."
        )

    return {row[0] for row in rows}


def _deflate_wem_energy(client: Client, max_interval: datetime) -> None:
    assignments = ",\n            ".join(f"{column} = {column} / {INFLATION_FACTOR}" for column in INFLATED_COLUMNS)

    # Every inflated column is Nullable(Float64), so NULL / 6 stays NULL and untouched rows stay
    # untouched — no COALESCE needed and none wanted, a NULL here means "not computed", not zero.
    #
    # Bounded by max_interval, never the whole region: the fix is deployed before this runs, so the
    # workers have already written correct rows for the most recent intervals and dividing those
    # again would put them 6x low. A whole-year ratio cannot see that — a day of correct rows inside
    # a year of inflated ones still reads ~5.98.
    client.execute(
        f"""
        ALTER TABLE market_summary
        UPDATE
            {assignments}
        WHERE network_id = %(network_id)s
          AND network_region = %(network_region)s
          AND interval <= %(max_interval)s
        """,
        {
            "network_id": WEM_NETWORK_ID,
            "network_region": WEM_NETWORK_REGION,
            "max_interval": max_interval,
        },
    )
    logger.info(
        f"Submitted UPDATE dividing {len(INFLATED_COLUMNS)} columns by {INFLATION_FACTOR} "
        f"for WEM/WEM up to and including {max_interval}"
    )


def _delete_bogus_regions(client: Client) -> None:
    for network_id, network_region in BOGUS_NETWORK_REGIONS:
        client.execute(
            """
            ALTER TABLE market_summary
            DELETE WHERE network_id = %(network_id)s AND network_region = %(network_region)s
            """,
            {"network_id": network_id, "network_region": network_region},
        )
        logger.info(f"Submitted DELETE for {network_id}/{network_region}")


def _rebuild_materialized_views(start_date: datetime, end_date: datetime) -> None:
    """Re-aggregate the daily and monthly views over the repaired range.

    The backfill deletes each chunk's date range across all networks before re-inserting from
    market_summary, so the stale WEMDE and NEM/WEM view rows disappear with it — they are gone from
    the source by this point.
    """
    for view in (MARKET_SUMMARY_DAILY_VIEW, MARKET_SUMMARY_MONTHLY_VIEW):
        logger.info(f"Rebuilding {view.name} from {start_date} to {end_date}")
        total = backfill_materialized_view(
            view=view,
            start_date=start_date,
            end_date=end_date,
            chunk_size_days=MV_CHUNK_SIZE_DAYS,
        )
        logger.info(f"{view.name} now holds {total:,} rows")


def _assert_materialized_views_match_source(client: Client, start_date: datetime) -> None:
    """The views must agree with the table they were rebuilt from.

    `backfill_materialized_view` logs and continues when a chunk fails, having already deleted that
    chunk's rows, so a failed INSERT leaves a silent hole. Checking the source alone would not see
    it. Each view is compared against market_summary over the same window, and both are checked for
    surviving rows of the deleted regions.
    """
    for view, energy_column in (
        (MARKET_SUMMARY_DAILY_VIEW, "demand_energy_daily"),
        (MARKET_SUMMARY_MONTHLY_VIEW, "demand_energy_monthly"),
    ):
        for network_id, network_region in BOGUS_NETWORK_REGIONS:
            leftover = _query(
                client,
                f"""
                SELECT count()
                FROM {view.name}
                WHERE network_id = %(network_id)s AND network_region = %(network_region)s
                """,
                {"network_id": network_id, "network_region": network_region},
            )
            if leftover and leftover[0][0]:
                raise SystemExit(f"{view.name} still holds {leftover[0][0]:,} {network_id}/{network_region} rows")

        view_total = _query(
            client,
            f"""
            SELECT sum({energy_column})
            FROM {view.name} FINAL
            WHERE network_id = %(network_id)s
              AND network_region = %(network_region)s
              AND {view.timestamp_column} >= %(start)s
            """,
            {"network_id": WEM_NETWORK_ID, "network_region": WEM_NETWORK_REGION, "start": start_date.date()},
        )
        source_total = _query(
            client,
            """
            SELECT sum(demand_energy)
            FROM market_summary FINAL
            WHERE network_id = %(network_id)s
              AND network_region = %(network_region)s
              AND interval >= %(start)s
            """,
            {"network_id": WEM_NETWORK_ID, "network_region": WEM_NETWORK_REGION, "start": start_date},
        )

        view_energy = (view_total[0][0] if view_total else 0) or 0.0
        source_energy = (source_total[0][0] if source_total else 0) or 0.0

        if not source_energy:
            raise SystemExit("market_summary holds no WEM demand energy after the repair — investigate before continuing")

        drift = abs(view_energy - source_energy) / source_energy

        if drift > 0.01:
            raise SystemExit(
                f"{view.name} demand energy is {view_energy:,.0f} MWh against {source_energy:,.0f} MWh in "
                f"market_summary ({drift:.1%} adrift). A backfill chunk failed after its DELETE — re-run the "
                f"rebuild before trusting the views."
            )

        logger.info(f"{view.name} matches market_summary within {drift:.2%}")


def repair_wem_market_summary_energy(apply: bool = False) -> None:
    """Rescale the WEM energy columns and drop the duplicate region rows.

    Resumable rather than idempotent. Dividing a row twice would leave it 6x low, so the UPDATE is
    bounded to rows that still carry the 6x signature; once none do, that stage is skipped and a
    re-run picks up at the deletes and the view rebuild. That matters because the three stages fail
    independently — a completed division followed by a failed view rebuild must not lock the
    operator out of finishing the job.
    """
    client = get_clickhouse_client(timeout=300)

    inflated_rows, inflated_max = _inflated_row_span(client)

    before = _wem_yearly_ratios(client, max_interval=inflated_max)
    _log_yearly_table(before, "WEM/WEM demand energy before:")

    bogus = _bogus_region_counts(client)
    for (network_id, network_region), count in bogus.items():
        logger.info(f"{network_id}/{network_region}: {count:,} rows to delete")

    if inflated_max is None:
        logger.warning("No rows carry the 6x signature — the energy division has already run, moving to the later stages")
    else:
        total_rows = sum(count for _, count, _, _, _ in before)
        logger.info(
            f"{inflated_rows:,} of the {total_rows:,} WEM/WEM rows at or before {inflated_max} carry the 6x "
            f"signature; the rest have a null demand and are divided along with them."
        )
        # Rows past the cutoff were written by the fixed code, except possibly a trailing edge of
        # null-demand rows that carry no signature to test. Those sit inside the window the worker
        # re-aggregates every few minutes, so they correct themselves.
        logger.info(f"{_wem_rows_after(client, inflated_max):,} WEM/WEM rows sit after the cutoff and are left alone")
        _assert_ratios_within(before, RATIO_BEFORE, "Pre-flight check")

    affected_min = _affected_min_interval(client)
    if affected_min is None:
        raise SystemExit("No affected rows found — nothing to repair")

    mv_start = min(affected_min.replace(day=1, hour=0, minute=0, second=0, microsecond=0), MV_BACKFILL_FLOOR)
    mv_end = datetime.now()

    if not apply:
        logger.info(
            f"Dry run — would divide {INFLATED_COLUMNS} by {INFLATION_FACTOR} across {inflated_rows:,} WEM/WEM rows "
            f"up to {inflated_max}, delete {sum(bogus.values()):,} bogus region rows, then rebuild "
            f"market_summary_daily_mv and market_summary_monthly_mv from {mv_start} to {mv_end}. Re-run with --apply."
        )
        return

    known_mutations = _existing_mutation_ids(client)

    if inflated_max is not None:
        _deflate_wem_energy(client, inflated_max)

    _delete_bogus_regions(client)
    _wait_for_mutations(client, known_mutations)

    _rebuild_materialized_views(mv_start, mv_end)

    after = _wem_yearly_ratios(client)
    _log_yearly_table(after, "WEM/WEM demand energy after:")
    _assert_ratios_within(after, RATIO_AFTER, "Post-repair check")

    residual_rows, residual_max = _inflated_row_span(client)
    if residual_rows:
        raise SystemExit(f"{residual_rows:,} WEM/WEM rows still carry the 6x signature, latest at {residual_max}")

    remaining = _bogus_region_counts(client)
    if any(remaining.values()):
        raise SystemExit(f"Bogus region rows survived the delete: {remaining}")

    _assert_materialized_views_match_source(client, mv_start)

    logger.info("WEM market_summary energy repair complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Divide the 6x WEM market_summary energy columns and drop WEMDE rows")
    parser.add_argument("--apply", action="store_true", help="Write the changes. Without it the script only reports.")
    args = parser.parse_args()

    repair_wem_market_summary_energy(apply=args.apply)


if __name__ == "__main__":
    main()
