"""Backfill energy for rows stuck on the generated/12 fallback (#764). Dry run unless --apply.

Usage: PYTHONPATH=$PWD uv run --no-sync python bin/energy_backfill.py --start 2026-03-24 --end 2026-10-22 [--apply]

For each chunk (default 3 days) prints how many NEM facility_scada rows have energy_quality_flag < 2 (read-only
SELECT count). With --apply it runs `run_energy_backlog` on the chunk, sequentially, with --max-workers day-chunks
in flight. If the resolved database host contains "prod" it refuses to write unless --i-know-this-writes is also
passed. Never prints credentials, only the host and database name.
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse

from sqlalchemy import text

DEFAULT_CHUNK_DAYS = 3
DEFAULT_MAX_WORKERS = 2

_COUNT_QUERY = text("""
    select count(*) from facility_scada
    where network_id = 'NEM' and is_forecast is false and energy_quality_flag < 2
      and interval >= :start and interval < :end
""")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", required=True, type=datetime.fromisoformat, help="naive NEM time, inclusive")
    p.add_argument("--end", required=True, type=datetime.fromisoformat, help="naive NEM time, exclusive")
    p.add_argument("--chunk-days", type=int, default=DEFAULT_CHUNK_DAYS)
    p.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    p.add_argument("--apply", action="store_true", help="write; default is a read-only dry run")
    p.add_argument("--i-know-this-writes", action="store_true", help="required with --apply when the host contains 'prod'")
    return p.parse_args(argv)


def plan_chunks(start: datetime, end: datetime, chunk_days: int) -> list[tuple[datetime, datetime]]:
    if chunk_days < 1:
        raise ValueError("chunk-days must be >= 1")
    chunks: list[tuple[datetime, datetime]] = []
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=chunk_days), end)
        chunks.append((cur, nxt))
        cur = nxt
    return chunks


def describe_target(db_url: str) -> tuple[str, str]:
    """(host, database) only, no credentials."""
    u = urlparse(db_url)
    return u.hostname or "unknown", u.path.lstrip("/") or "unknown"


def check_write_allowed(args: argparse.Namespace, host: str) -> str | None:
    """Return a refusal message, or None when the run may proceed."""
    if not args.apply:
        return None
    if "prod" in host.lower() and not args.i_know_this_writes:
        return f"refusing to write: host {host!r} looks like prod, pass --i-know-this-writes as well as --apply"
    return None


def validate(args: argparse.Namespace) -> str | None:
    if args.end <= args.start:
        return "--end must be after --start"
    if args.max_workers < 1:
        return "--max-workers must be >= 1"
    if args.chunk_days < 1:
        return "--chunk-days must be >= 1"
    return None


async def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    error = validate(args)
    if error:
        print(error, file=sys.stderr)
        return 2

    from opennem import settings

    host, dbname = describe_target(str(settings.db_url))
    refusal = check_write_allowed(args, host)
    if refusal:
        print(refusal, file=sys.stderr)
        return 3

    print(f"target: {host}/{dbname}  mode: {'APPLY' if args.apply else 'dry run'}  max_workers={args.max_workers}")

    from opennem.db import get_read_session
    from opennem.workers.energy import run_energy_backlog

    chunks = plan_chunks(args.start, args.end, args.chunk_days)
    total = 0
    for start, end in chunks:
        async with get_read_session() as session:
            pending = (await session.execute(_COUNT_QUERY, {"start": start, "end": end})).scalar_one()
        total += pending
        print(f"{start} -> {end}: {pending:,} rows with flag < 2")

        if args.apply:
            updated = await run_energy_backlog(
                date_start=start, date_end=end, chunk_size=timedelta(days=1), max_workers=args.max_workers
            )
            print(f"  applied: {updated:,} rows updated")

    print(f"{len(chunks)} chunks, {total:,} rows with flag < 2 before run")
    if not args.apply:
        print("dry run: nothing written. re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
