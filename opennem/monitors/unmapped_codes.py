"""Detect facility_scada codes whose energy is silently dropped on the way to ClickHouse.

`aggregates/unit_intervals.py` builds its source rows with

    FROM facility_scada fs
    JOIN units u        ON fs.facility_code = u.code
    JOIN facilities f   ON u.station_id = f.id
    JOIN fueltech ft    ON ft.code = u.fueltech_id

Every one of those is an inner join, so a code that fails any of them contributes
nothing to ClickHouse and no warning is raised. Because both the API and the static
exports read from ClickHouse, the loss is invisible downstream — this is how ~19,900 GWh
of WEM history (2006-2016) stayed hidden until #599.

Two distinct failure modes are checked:

1. **unmapped** — a `facility_scada` code with no `units` row at all.
2. **unjoinable** — a `units` row that exists but has no `fueltech_id` or no
   `station_id`, so it dies on the second or third join instead of the first.

The check is windowed rather than full-history. A rolling window answers the question
that actually matters — "is AEMO sending us something we are dropping *right now*" —
and it does so in seconds against a table where the full-history equivalent takes
upwards of fifteen minutes. It also keeps the allowlist small: historic unmapped codes
age out of the window on their own instead of needing to be enumerated forever.
"""

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from opennem.clients.slack import slack_message
from opennem.db import get_read_session

logger = logging.getLogger("opennem.monitors.unmapped_codes")

# Codes deliberately left unmapped that still carry energy. Keep this as short as
# possible — anything here is data we are knowingly discarding.
KNOWN_UNMAPPED_CODES: set[str] = {
    # bouldercombe + dalrymple historic DUIDs. Mapping them as units would double count
    # against the derived gen/load series that covers the same period — see #603.
    "BBATTERY",
    "BBATRYL1",
    "DALNTH01",
}

# Interconnectors have no fueltech by design and are excluded from the generation
# aggregate; their flows are handled by the flows pipeline instead.
INTERCONNECTOR_PATTERNS = ("MNSP", "FLOW", "-NSW1", "-QLD1", "-VIC1", "-SA1", "-TAS1", "V-S", "V-SA", "N-Q")

# MWh over the window. Above float noise, far below anything a real generator produces.
ENERGY_THRESHOLD_MWH = 1.0

DEFAULT_WINDOW_DAYS = 7


@dataclass(frozen=True, slots=True)
class DroppedCode:
    """A code whose energy never reaches ClickHouse."""

    network_id: str
    code: str
    reason: str
    energy_mwh: float
    intervals: int

    def __str__(self) -> str:
        return f"{self.network_id} {self.code} ({self.reason}): {self.energy_mwh:,.1f} MWh over {self.intervals:,} intervals"


REASON_NO_UNIT = "no units row"
REASON_NO_FUELTECH = "unit has no fueltech or station"


def _is_interconnector(code: str) -> bool:
    return any(pattern in code for pattern in INTERCONNECTOR_PATTERNS)


def filter_dropped(rows: Iterable[Sequence[Any]], reason: str) -> list[DroppedCode]:
    """Turn query rows into alertable findings, dropping the ones we expect.

    Rows are `(network_id, code, energy, intervals)` — either plain tuples or SQLAlchemy
    `Row`s. Interconnectors are excluded because they carry no fueltech by design and
    never enter the generation aggregate.
    """
    findings: list[DroppedCode] = []

    for network_id, code, energy, intervals in rows:
        if code in KNOWN_UNMAPPED_CODES or _is_interconnector(code):
            logger.debug(f"Skipping expected unmapped code {code}")
            continue

        findings.append(
            DroppedCode(
                network_id=network_id,
                code=code,
                reason=reason,
                energy_mwh=float(energy),
                intervals=intervals,
            )
        )

    return findings


_UNMAPPED_QUERY = text("""
    select
        fs.network_id,
        fs.facility_code as code,
        coalesce(sum(fs.energy), 0) as energy,
        count(*) as intervals
    from facility_scada fs
    left join units u on fs.facility_code = u.code
    where
        u.code is null
        and fs.is_forecast is false
        and fs.interval >= now() - (:window_days * interval '1 day')
    group by 1, 2
    having abs(coalesce(sum(fs.energy), 0)) > :threshold
""")

_UNJOINABLE_QUERY = text("""
    select
        fs.network_id,
        u.code as code,
        coalesce(sum(fs.energy), 0) as energy,
        count(*) as intervals
    from units u
    join facility_scada fs on fs.facility_code = u.code
    where
        (u.fueltech_id is null or u.station_id is null)
        and fs.is_forecast is false
        and fs.interval >= now() - (:window_days * interval '1 day')
    group by 1, 2
    having abs(coalesce(sum(fs.energy), 0)) > :threshold
""")


async def check_unmapped_facility_codes(window_days: int = DEFAULT_WINDOW_DAYS) -> list[DroppedCode]:
    """Find codes carrying energy that the ClickHouse ingest joins discard.

    Args:
        window_days: how far back to look. Keep this comfortably longer than the
            longest crawler lag (WEM publishes ~24h behind) so a newly introduced
            code is seen before it ages out.

    Returns:
        Codes to alert on, worst first. Empty when the pipeline is clean.
    """
    params = {"window_days": window_days, "threshold": ENERGY_THRESHOLD_MWH}

    async with get_read_session() as session:
        unmapped = (await session.execute(_UNMAPPED_QUERY, params)).all()
        unjoinable = (await session.execute(_UNJOINABLE_QUERY, params)).all()

    dropped = filter_dropped(unmapped, REASON_NO_UNIT) + filter_dropped(unjoinable, REASON_NO_FUELTECH)
    dropped.sort(key=lambda d: abs(d.energy_mwh), reverse=True)

    if dropped:
        logger.warning(f"{len(dropped)} facility_scada codes are being dropped at clickhouse ingest over {window_days}d")
        for entry in dropped:
            logger.warning(f"  {entry}")
    else:
        logger.info(f"No dropped facility_scada codes over the last {window_days} days")

    return dropped


async def run_unmapped_code_check(window_days: int = DEFAULT_WINDOW_DAYS) -> list[DroppedCode]:
    """Run the check and alert to Slack when anything is being dropped."""
    from opennem import settings

    dropped = await check_unmapped_facility_codes(window_days=window_days)

    if not dropped:
        return dropped

    lines = "\n".join(f"• {entry}" for entry in dropped)
    await slack_message(
        webhook_url=settings.slack_hook_monitoring,
        message=(
            f"*Unmapped facility codes dropping energy* ({window_days}d window)\n"
            f"These codes carry energy in `facility_scada` but are discarded by the clickhouse "
            f"ingest joins, so they are missing from the API and every export:\n{lines}\n"
            f"Map them in the CMS, or add to `KNOWN_UNMAPPED_CODES` if the omission is intentional."
        ),
        tag_users=settings.slack_admin_alert,
    )

    return dropped


if __name__ == "__main__":
    import asyncio

    async def _main() -> None:
        dropped = await check_unmapped_facility_codes()
        if not dropped:
            print("clean — nothing being dropped")
        for entry in dropped:
            print(entry)

    asyncio.run(_main())
