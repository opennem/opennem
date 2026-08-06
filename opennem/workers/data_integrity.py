"""Data-integrity checks for the PG -> ClickHouse aggregation pipeline.

Guards against silent aggregate corruption of the kind found in the rooftop
catchup incident (2026-03-18 -> 2026-07-07): a re-aggregation window starting
off the 30-min rooftop grid made locf() emit leading-edge NULL rows which
clobbered previously-good unit_intervals rows under ReplacingMergeTree (newest
version wins). Rooftop energy silently under-reported ~12.5%/day for months
while the exports stayed perfectly consistent with ClickHouse — only comparing
against the PostgreSQL source data could catch it.

The checks here are shared by:
  * tests/e2e/test_pipeline_data_integrity.py (on-demand, RUN_E2E=1)
  * task_data_integrity_check (daily worker task, alerts Slack monitoring)

Each check returns a list of human-readable failure strings (empty = healthy).
"""

import logging
from datetime import datetime, timedelta
from typing import cast

from sqlalchemy import text

from opennem import settings
from opennem.clients.slack import slack_message
from opennem.db import get_read_session
from opennem.db.clickhouse import get_clickhouse_client
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.workers.data_integrity")

# Exclude the bleeding edge where rooftop legitimately lags / settles (#575/#577).
_SETTLING_BUFFER = timedelta(hours=2)

# CH aggregates are rounded to 4dp and rooftop energy is spread over 5-min buckets;
# anything beyond 1% daily divergence vs PG is data loss, not rounding.
DAILY_TOLERANCE_PCT = 1.0

DEFAULT_LOOKBACK_DAYS = 7

# Ignore empty region-days below this many MWh when comparing daily sums
_MIN_DAILY_ENERGY_MWH = 1.0


def get_check_window(lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> tuple[datetime, datetime]:
    """Last N full days up to the settled edge, as naive network-time datetimes."""
    end = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None) - _SETTLING_BUFFER
    end = end.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=lookback_days)
    return start, end


async def check_rooftop_null_rows(start: datetime, end: datetime) -> list[str]:
    """No NULL energy/generated rooftop rows in CH inside the settled window.

    NULL rows here mean an aggregate write clobbered real data (the rooftop
    catchup incident wrote locf leading-edge NULLs over good rows).
    """
    client = get_clickhouse_client()
    rows = cast(
        list[tuple],
        client.execute(
            """
        SELECT
            toDate(interval) AS day,
            countIf(energy IS NULL) AS null_energy,
            countIf(generated IS NULL) AS null_generated
        FROM unit_intervals FINAL
        WHERE fueltech_id = 'solar_rooftop'
            AND network_id = 'AEMO_ROOFTOP'
            AND interval >= %(start)s
            AND interval < %(end)s
        GROUP BY day
        HAVING null_energy > 0 OR null_generated > 0
        ORDER BY day
        """,
            {"start": start, "end": end},
        ),
    )
    return [
        f"{day}: {null_energy} NULL energy / {null_generated} NULL generated rooftop rows"
        for day, null_energy, null_generated in rows
    ]


async def check_rooftop_ch_vs_pg(start: datetime, end: datetime) -> list[str]:
    """CH rooftop daily energy per facility must match PG facility_scada.

    facility_scada is the source of truth (validated against AEMO nemweb).
    Divergence means the PG->CH aggregation dropped or corrupted data — this is
    the check that would have caught the catchup incident on day one.
    """
    async with get_read_session() as session:
        result = await session.execute(
            text("""
                SELECT
                    interval::date AS day,
                    facility_code,
                    sum(energy) AS energy
                FROM facility_scada
                WHERE network_id = 'AEMO_ROOFTOP'
                    AND is_forecast IS FALSE
                    AND interval >= :start
                    AND interval < :end
                GROUP BY 1, 2
            """),
            {"start": start, "end": end},
        )
        pg = {(str(day), code): float(energy) for day, code, energy in result if energy is not None}

    client = get_clickhouse_client()
    ch_rows = cast(
        list[tuple],
        client.execute(
            """
        SELECT toDate(interval) AS day, facility_code, sum(energy) AS energy
        FROM unit_intervals FINAL
        WHERE fueltech_id = 'solar_rooftop'
            AND network_id = 'AEMO_ROOFTOP'
            AND interval >= %(start)s
            AND interval < %(end)s
        GROUP BY day, facility_code
        """,
            {"start": start, "end": end},
        ),
    )
    ch = {(str(day), code): float(energy) for day, code, energy in ch_rows}

    if not pg:
        return [f"no PG rooftop data in window {start} -> {end}"]

    failures: list[str] = []
    for key, pg_energy in sorted(pg.items()):
        if pg_energy < _MIN_DAILY_ENERGY_MWH:
            continue
        ch_energy = ch.get(key)
        if ch_energy is None:
            failures.append(f"{key[0]} {key[1]}: missing from ClickHouse (PG={pg_energy:.1f} MWh)")
            continue
        diff_pct = 100.0 * (ch_energy / pg_energy - 1.0)
        if abs(diff_pct) > DAILY_TOLERANCE_PCT:
            failures.append(f"{key[0]} {key[1]}: CH={ch_energy:.1f} PG={pg_energy:.1f} MWh ({diff_pct:+.1f}%)")

    return failures


async def check_rooftop_daily_mv_vs_base(start: datetime, end: datetime) -> list[str]:
    """fueltech_intervals_daily_mv must agree with the unit_intervals base table.

    The daily MV feeds the energy exports; ReplacingMergeTree partial-aggregate
    rot here produces wrong exports even when the base table is correct.
    """
    client = get_clickhouse_client()
    rows = cast(
        list[tuple],
        client.execute(
            """
        WITH base AS (
            SELECT toDate(interval) AS day, network_region, sum(energy) AS energy
            FROM unit_intervals FINAL
            WHERE fueltech_id = 'solar_rooftop'
                AND network_id = 'AEMO_ROOFTOP'
                AND interval >= %(start)s
                AND interval < %(end)s
            GROUP BY day, network_region
        ),
        daily AS (
            SELECT date AS day, network_region, sum(energy) AS energy
            FROM fueltech_intervals_daily_mv FINAL
            WHERE fueltech_id = 'solar_rooftop'
                AND network_id = 'AEMO_ROOFTOP'
                AND date >= toDate(%(start)s)
                AND date < toDate(%(end)s)
            GROUP BY day, network_region
        )
        SELECT b.day, b.network_region, b.energy AS base_energy, d.energy AS mv_energy
        FROM base b
        LEFT JOIN daily d ON b.day = d.day AND b.network_region = d.network_region
        WHERE b.energy > %(min_energy)s
            AND (d.energy IS NULL OR abs(d.energy / b.energy - 1) > %(tolerance)s)
        ORDER BY b.day, b.network_region
        """,
            {
                "start": start,
                "end": end,
                "tolerance": DAILY_TOLERANCE_PCT / 100.0,
                "min_energy": _MIN_DAILY_ENERGY_MWH,
            },
        ),
    )
    return [
        f"{day} {region}: daily MV={mv_energy if mv_energy is None else round(mv_energy, 1)} vs base={base_energy:.1f} MWh"
        for day, region, base_energy, mv_energy in rows
    ]


async def run_data_integrity_check(lookback_days: int = DEFAULT_LOOKBACK_DAYS, alert_slack: bool = True) -> list[str]:
    """Run all pipeline integrity checks and optionally alert Slack monitoring.

    Returns the combined list of failures (empty = healthy).
    """
    start, end = get_check_window(lookback_days=lookback_days)

    checks = {
        "rooftop NULL rows in unit_intervals": check_rooftop_null_rows,
        "rooftop CH vs PG source": check_rooftop_ch_vs_pg,
        "rooftop daily MV vs base": check_rooftop_daily_mv_vs_base,
    }

    all_failures: list[str] = []
    for name, check in checks.items():
        try:
            failures = await check(start, end)
        except Exception as e:
            logger.exception(f"data integrity check '{name}' errored")
            failures = [f"check errored: {e}"]
        if failures:
            all_failures.append(f"*{name}* ({len(failures)}):")
            all_failures.extend(f"  • {f}" for f in failures[:10])
            if len(failures) > 10:
                all_failures.append(f"  … and {len(failures) - 10} more")

    if all_failures:
        message = (
            f":rotating_light: *Data integrity check failed* ({settings.env}) "
            f"window {start.date()} -> {end.date()}\n" + "\n".join(all_failures)
        )
        logger.error(message)
        if alert_slack:
            await slack_message(webhook_url=settings.slack_hook_monitoring, message=message, tag_users=["nik"])
    else:
        logger.info(f"Data integrity checks passed for {start.date()} -> {end.date()}")

    return all_failures


if __name__ == "__main__":
    import asyncio

    failures = asyncio.run(run_data_integrity_check(alert_slack=False))
    for line in failures:
        print(line)
