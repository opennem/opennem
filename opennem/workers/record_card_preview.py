"""CLI for previewing the milestone/record social card locally.

Usage:
    uv run python -m opennem.workers.record_card_preview \\
        --record-id au.nem.battery_charging.energy.day.high

Picks the most recent instance of the given record_id, fetches its history,
renders the card, and writes it to /tmp.
"""

import argparse
import asyncio
import logging
from pathlib import Path

from sqlalchemy import and_, desc, select

from opennem.db import get_read_session
from opennem.db.models.opennem import Milestones
from opennem.social.content import render_milestone_card

logger = logging.getLogger("opennem.workers.record_card_preview")


async def preview(record_id: str | None, instance_id: str | None) -> Path:
    async with get_read_session() as session:
        if instance_id:
            rec = (await session.execute(select(Milestones).where(Milestones.instance_id == instance_id))).scalar_one_or_none()
        elif record_id:
            rec = (
                await session.execute(
                    select(Milestones).where(Milestones.record_id == record_id).order_by(desc(Milestones.interval)).limit(1)
                )
            ).scalar_one_or_none()
        else:
            # Pick the most recent significant record
            rec = (
                await session.execute(
                    select(Milestones).where(Milestones.significance >= 9).order_by(desc(Milestones.interval)).limit(1)
                )
            ).scalar_one_or_none()

        if not rec:
            raise ValueError("No matching record found")

        # Fetch the most recent 40 history rows; reverse to oldest→newest for the renderer.
        history_rows = (
            (
                await session.execute(
                    select(Milestones)
                    .where(and_(Milestones.record_id == rec.record_id, Milestones.interval < rec.interval))
                    .order_by(Milestones.interval.desc())
                    .limit(40)
                )
            )
            .scalars()
            .all()
        )

    history = [(h.interval, float(h.value)) for h in reversed(history_rows)]

    print(f"Record: {rec.record_id}")
    print(f"  interval={rec.interval}, value={rec.value} {rec.value_unit}")
    print(f"  description={rec.description}")
    print(f"  history points: {len(history)}")

    image_bytes = render_milestone_card(
        record_id=str(rec.record_id),
        interval=rec.interval,
        description=str(rec.description) if rec.description is not None else None,
        value=float(rec.value),
        value_unit=str(rec.value_unit) if rec.value_unit is not None else "",
        pct_change=float(rec.pct_change) if rec.pct_change is not None else None,
        period=str(rec.period) if rec.period is not None else None,
        network_region=str(rec.network_region) if rec.network_region is not None else None,
        fueltech_id=str(rec.fueltech_id) if rec.fueltech_id is not None else None,
        history=history,
    )

    out_path = Path("/tmp") / f"record_card_preview_{rec.record_id.replace('.', '_')}.png"
    out_path.write_bytes(image_bytes)
    print(f"Wrote: {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preview a milestone/record social card")
    parser.add_argument("--record-id", help="record_id slug (e.g. au.nem.battery_charging.energy.day.high)")
    parser.add_argument("--instance-id", help="UUID of a specific milestone instance")
    args = parser.parse_args()

    asyncio.run(preview(args.record_id, args.instance_id))
