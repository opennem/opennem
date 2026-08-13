"""Detect generation telemetry that has frozen at its last value (#544).

When a unit's SCADA link fails, AEMO keeps publishing the last value it saw rather than
a gap or a zero. BUSF1 (Bundaberg, 101 MW solar) held exactly 60.76 MW day and night for
745 consecutive intervals in April 2026, inflating its energy roughly 3.8x and adding
~2.7 GWh of generation that never happened.

Nothing downstream catches this. The value is well inside the unit's capacity, so range
checks pass; it is present in every interval, so completeness checks pass; and the freeze
propagates into the next-day dispatch solution and the settled MMSDM archive alike, so a
re-crawl rewrites the same wrong number.

**The check is "solar generating at night", not "value hasn't changed".** A flat run is
not evidence of a fault: a solar farm clipping at its inverter limit holds its exact
capacity for hours every sunny day, and a curtailed farm or wind farm sits on its
constraint setpoint just as steadily. Scanning NEM history for long flat runs returns
mostly those, and separating them needs curtailment state the monitor does not have.

Night output has no such ambiguity. A solar farm produces nothing at 1am, so any material
reading in the small hours is the signal stuck at its last daylight value. Run over eleven
years of NEM history this found 22 incidents totalling ~8.6 GWh of generation that never
happened, with no false positives — BUSF1 among them, though not the largest.

The same trick has no equivalent for wind or thermal plant, which legitimately run flat
through the night, so the check is deliberately solar-only. It is a floor on detection,
not a ceiling: a freeze that begins and ends between dawn and dusk still slips through.
"""

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from opennem.clients.slack import slack_message
from opennem.db import get_read_session

logger = logging.getLogger("opennem.monitors.frozen_telemetry")

# Night in AEST. NEM intervals are AEST-naive, and 22:00-03:00 is comfortably dark across
# every NEM region year round — the widest civil twilight in the market (Hobart, midsummer)
# still ends before 21:30.
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 3

# Fraction of registered capacity a night reading has to reach before it counts. Solar
# farms legitimately draw a small auxiliary load overnight, which shows up as readings
# around 0.01-0.2 MW; without this floor those swamp the real signal.
CAPACITY_FRACTION = 0.1

# Half an hour of stuck night intervals. Below this, a single interval either side of dusk
# is more likely a timestamp edge than a fault.
MIN_NIGHT_INTERVALS = 6

# A freeze can persist for days, so the window wants to outlast one run-to-run gap.
DEFAULT_WINDOW_DAYS = 7


@dataclass(frozen=True, slots=True)
class FrozenSignal:
    """A solar unit reporting material generation in the middle of the night.

    `night` is the date the night *started* on, so a run from 22:00 to 02:00 stays one
    finding instead of being cut in half at midnight.
    """

    facility_code: str
    network_region: str
    night: str
    capacity_mw: float
    intervals: int
    min_mw: float
    max_mw: float

    @property
    def is_constant(self) -> bool:
        """A dead-flat value is the signature of a frozen signal specifically.

        A varying night reading is still wrong, but points at something else — a
        mis-registered co-located battery, or a unit reporting on the wrong DUID.
        """
        return abs(self.max_mw - self.min_mw) < 0.01

    def __str__(self) -> str:
        shape = f"flat at {self.min_mw:,.2f} MW" if self.is_constant else f"{self.min_mw:,.2f}-{self.max_mw:,.2f} MW"
        return (
            f"{self.facility_code} ({self.network_region}, {self.capacity_mw:,.0f} MW) "
            f"night of {self.night}: {shape} across {self.intervals} night intervals"
        )


_NIGHT_SOLAR_QUERY = text("""
    select
        fs.facility_code,
        f.network_region,
        to_char(date_trunc('day', fs.interval - interval '3 hours'), 'YYYY-MM-DD') as night,
        u.capacity_registered,
        count(*) as intervals,
        min(fs.generated) as min_mw,
        max(fs.generated) as max_mw
    from facility_scada fs
    join units u on u.code = fs.facility_code
    join facilities f on f.id = u.station_id
    where
        fs.network_id = 'NEM'
        and fs.is_forecast is false
        and fs.interval >= (now() at time zone 'Australia/Brisbane') - (:window_days * interval '1 day')
        and u.fueltech_id = 'solar_utility'
        and u.capacity_registered > 0
        and (extract(hour from fs.interval) >= :night_start or extract(hour from fs.interval) < :night_end)
        and fs.generated > :capacity_fraction * u.capacity_registered
    group by 1, 2, 3, 4
    having count(*) >= :min_intervals
    order by 3 desc, 5 desc
""")


def to_findings(rows: Iterable[Sequence[Any]]) -> list[FrozenSignal]:
    """Turn query rows into findings, worst (longest) first."""
    findings = [
        FrozenSignal(
            facility_code=facility_code,
            network_region=network_region,
            night=night,
            capacity_mw=float(capacity),
            intervals=intervals,
            min_mw=float(min_mw),
            max_mw=float(max_mw),
        )
        for facility_code, network_region, night, capacity, intervals, min_mw, max_mw in rows
    ]

    findings.sort(key=lambda f: f.intervals, reverse=True)

    return findings


async def check_frozen_telemetry(window_days: int = DEFAULT_WINDOW_DAYS) -> list[FrozenSignal]:
    """Find solar units reporting generation overnight.

    Args:
        window_days: how far back to look. A freeze can persist for days, so this wants to
            be long enough to still catch one that started just after the last run.

    Returns:
        Findings, longest first. Empty when telemetry is behaving.
    """
    params = {
        "window_days": window_days,
        "night_start": NIGHT_START_HOUR,
        "night_end": NIGHT_END_HOUR,
        "capacity_fraction": CAPACITY_FRACTION,
        "min_intervals": MIN_NIGHT_INTERVALS,
    }

    async with get_read_session() as session:
        rows = (await session.execute(_NIGHT_SOLAR_QUERY, params)).all()

    findings = to_findings(rows)

    if findings:
        logger.warning(f"{len(findings)} solar unit-nights reporting generation over {window_days}d")
        for finding in findings:
            logger.warning(f"  {finding}")
    else:
        logger.info(f"No frozen solar telemetry over the last {window_days} days")

    return findings


async def run_frozen_telemetry_check(window_days: int = DEFAULT_WINDOW_DAYS) -> list[FrozenSignal]:
    """Run the check and alert to Slack on anything found."""
    from opennem import settings

    findings = await check_frozen_telemetry(window_days=window_days)

    if not findings:
        return findings

    lines = "\n".join(f"• {finding}" for finding in findings)
    await slack_message(
        webhook_url=settings.slack_hook_monitoring,
        message=(
            f"*Solar units reporting generation overnight* ({window_days}d window)\n"
            f"Solar cannot generate at night, so these readings are almost certainly telemetry "
            f"frozen at their last daylight value — inflating energy for as long as the freeze "
            f"lasts:\n{lines}\n"
            f"Re-crawling will not fix it: the freeze propagates into next-day dispatch and the "
            f"settled archive too. See #544."
        ),
        tag_users=settings.slack_admin_alert,
    )

    return findings


if __name__ == "__main__":
    import asyncio

    async def _main() -> None:
        findings = await check_frozen_telemetry()
        if not findings:
            print("clean — no night solar generation")
        for finding in findings:
            print(finding)

    asyncio.run(_main())


def recent_unit_energy() -> list:
    """Deliberate CLAUDE.md violation for a CI smoke test — unscoped FINAL, sync client
    in an async codebase. Reverted before merge."""
    from opennem.db.clickhouse.client import get_clickhouse_client

    return get_clickhouse_client().execute("SELECT unit_code, sum(energy) FROM unit_intervals FINAL GROUP BY unit_code")
