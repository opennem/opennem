"""One-off backfill of next-day-only unit gaps on prod from AEMO Next_Day_Dispatch files (#773). Dry run unless --apply.

Usage: ENV=production PYTHONPATH=$PWD uv run --no-sync python bin/backfill_next_day_gaps_773.py [--units SNOWYGJP,KEPBL1]
           [--start-day 2025-09-01] [--end-day 2026-10-26] [--days 2026-02-23,2026-06-18]
           [--include-pre-split] [--apply --i-know-this-writes]

Units in `NEXT_DAY_ONLY_UNITS` (opennem/workers/next_day_heal.py) only arrive from DISPATCH_UNIT_SOLUTION in the next-day
dispatch file. Missed daily crawls left holes on prod. This script:

1. finds gap trading days with read-only SELECTs (trading day D = D 04:05 .. D+1 04:00, interval-ending):
   - plain units (SNOWYGJP, KEPBG1, KEPBL1): a day after the unit's first day with fewer than 288 intervals
   - split battery units (eg TB3BG1/TB3BL1 from TB3B1): a day where the parent duid has more intervals than G and L
     together, from the day after the first G/L row (the G/L copies are made by `generate_facility_scada`; days before
     the split mapping existed have none and are only included with --include-pre-split)
2. fetches that day's file from nemweb CURRENT (daily zip), else the monthly ARCHIVE zip (zip of daily zips)
3. parses DISPATCH_UNIT_SOLUTION for the source duids only and runs the crawler's own `generate_facility_scada`
   (generated = initialmw, energy = generated/12 with flag 0, energy_storage, battery split, aliases)
4. keeps only intervals where no member of the unit's group has a row yet, and prints per unit-day: rows now, rows the
   file supplies, rows to insert

--apply writes those rows with the crawler's upsert (`bulkinsert_mms_items`, UNIT_SOLUTION_UPDATE_COLUMNS,
keep_processed_energy) and needs ENV=production, --i-know-this-writes and a db-prod host. It then prints the energy
backfill and clickhouse re-aggregation commands to run next (energy first, then clickhouse).
"""

import argparse
import asyncio
import csv
import io
import sys
import zipfile
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from opennem.workers.next_day_heal import (
    INTERVALS_PER_TRADING_DAY,
    NEXT_DAY_ONLY_UNITS,
    trading_day_bounds,
    trading_day_of,
)

CURRENT_URL = "https://nemweb.com.au/Reports/Current/Next_Day_Dispatch/"
ARCHIVE_URL = "https://nemweb.com.au/Reports/ARCHIVE/Next_Day_Dispatch/"
DEFAULT_START_DAY = date(2025, 9, 1)  # oldest file in CURRENT and ARCHIVE as of oct 2026
PROD_HOST_MARKER = "db-prod"
UNIT_SOLUTION_PREFIXES = ("I,DISPATCH,UNIT_SOLUTION,", "D,DISPATCH,UNIT_SOLUTION,")

Key = tuple[str, datetime]  # (facility_code, interval)


@dataclass(frozen=True)
class UnitGroup:
    """Codes that share intervals: a plain unit is its own group, a split battery is G + L under a parent duid."""

    name: str
    members: tuple[str, ...]  # facility_scada codes filled by this script
    parent: str | None = None  # source duid in the file for split batteries

    @property
    def source_duids(self) -> tuple[str, ...]:
        return (self.parent,) if self.parent else self.members


@dataclass(frozen=True)
class GapDay:
    group: UnitGroup
    trading_day: date
    rows_now: int
    expected: int
    reason: str


@dataclass(frozen=True)
class UnitDayPlan:
    unit_code: str
    trading_day: date
    reason: str
    rows_now: int
    file_rows: int
    to_insert: int


# pure helpers


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start-day", type=date.fromisoformat, default=DEFAULT_START_DAY, help="first trading day to scan")
    p.add_argument("--end-day", type=date.fromisoformat, default=None, help="last trading day (default: 2 days ago)")
    p.add_argument("--units", type=lambda s: [u.strip().upper() for u in s.split(",") if u.strip()], default=None)
    p.add_argument("--days", type=lambda s: [date.fromisoformat(d.strip()) for d in s.split(",") if d.strip()], default=None)
    p.add_argument(
        "--include-pre-split",
        action="store_true",
        help="also fill split battery days before their first G/L row (mostly 0 MW, moves first-seen back)",
    )
    p.add_argument("--apply", action="store_true", help="write; default is a read-only dry run")
    p.add_argument("--i-know-this-writes", action="store_true", help="required with --apply")
    return p.parse_args(argv)


def default_end_day(now_nem: datetime) -> date:
    """Last trading day whose next-day file is surely published (file for D lands ~04:10 on D+1). Naive NEM time."""
    return trading_day_of(now_nem) - timedelta(days=2)


def describe_target(db_url: str) -> tuple[str, str]:
    """(host, database) only, no credentials."""
    u = urlparse(db_url)
    return u.hostname or "unknown", u.path.lstrip("/") or "unknown"


def check_write_allowed(args: argparse.Namespace, env: str, host: str) -> str | None:
    """Refusal message, or None when the run may proceed."""
    if not args.apply:
        return None
    if env.lower() != "production":
        return f"refusing to write: ENV is {env!r}, --apply needs ENV=production"
    if not args.i_know_this_writes:
        return "refusing to write: pass --i-know-this-writes as well as --apply"
    if PROD_HOST_MARKER not in host.lower():
        return f"refusing to write: host {host!r} is not {PROD_HOST_MARKER}"
    return None


def build_groups(units: Iterable[str], battery_map: Mapping[str, Any]) -> list[UnitGroup]:
    """Group target units: G/L codes of one battery go under their parent duid, the rest stand alone."""
    units = set(units)
    groups: dict[str, UnitGroup] = {}
    paired: set[str] = set()

    for duid, bmap in battery_map.items():
        members = (bmap.discharge_unit, bmap.charge_unit)
        if not units.intersection(members) or bmap.unit != duid:
            continue
        groups[duid] = UnitGroup(name=duid, members=members, parent=duid)
        paired.update(members)

    for code in sorted(units - paired):
        groups[code] = UnitGroup(name=code, members=(code,))

    return [groups[k] for k in sorted(groups)]


def iter_days(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def find_gap_days(
    groups: Iterable[UnitGroup],
    counts: Mapping[tuple[str, date], int],
    start_day: date,
    end_day: date,
    include_pre_split: bool = False,
) -> list[GapDay]:
    """Gap days per group from distinct-interval counts keyed by (group name or "parent:<duid>", trading day).

    counts[(group.name, day)] is distinct intervals over the group's members, counts[("parent:<duid>", day)] the
    parent's own rows. Every group is only checked from the day after its first row: the first day is usually partial
    (commissioning, the split mapping going live, or the scan's own start). For split batteries the days before the
    G/L mapping existed are a different question (the parent was mostly 0 MW pre-commissioning, writing them moves the
    units' first-seen date back), so they are only included with include_pre_split.
    """
    gaps: list[GapDay] = []

    for group in groups:
        seen = sorted(day for (name, day), n in counts.items() if name == group.name and n > 0)

        if group.parent:
            first = start_day if include_pre_split or not seen else max(start_day, seen[0] + timedelta(days=1))
            if not seen and not include_pre_split:
                continue
            for day in iter_days(first, end_day):
                parent_rows = counts.get((f"parent:{group.parent}", day), 0)
                rows = counts.get((group.name, day), 0)
                if rows < parent_rows:
                    reason = "split < parent" if seen and day > seen[0] else "pre-split"
                    gaps.append(GapDay(group, day, rows, parent_rows, reason))
            continue

        if not seen:
            continue
        for day in iter_days(max(start_day, seen[0] + timedelta(days=1)), end_day):
            rows = counts.get((group.name, day), 0)
            if rows < INTERVALS_PER_TRADING_DAY:
                gaps.append(GapDay(group, day, rows, INTERVALS_PER_TRADING_DAY, "short day"))

    return sorted(gaps, key=lambda g: (g.trading_day, g.group.name))


def filter_unit_solution_csv(lines: Iterable[str], duids: Iterable[str]) -> str:
    """Keep the DISPATCH_UNIT_SOLUTION header and the data rows for `duids`, as csv text for parse_aemo_mms_csv."""
    wanted = {d.upper() for d in duids}
    out: list[str] = []
    duid_index: int | None = None

    for line in lines:
        if not line.startswith(UNIT_SOLUTION_PREFIXES):
            continue
        row = next(csv.reader([line]))
        if row[0] == "I":
            duid_index = row.index("DUID")
            out.append(line.rstrip("\r\n"))
            continue
        if duid_index is not None and row[duid_index].strip().upper() in wanted:
            out.append(line.rstrip("\r\n"))

    if not out:
        return ""
    # parse_aemo_mms_csv only commits a table when the next C/I row arrives, so close it like a real file does
    out.append("C,END OF REPORT")
    return "\n".join(out) + "\n"


def keep_missing(
    records: Iterable[Mapping[str, Any]],
    group: UnitGroup,
    trading_day: date,
    existing: set[Key],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Records for the group's members on the trading day whose interval no member already has.

    Returns (rows to insert, rows the file supplies per member).
    """
    taken = {interval for code, interval in existing if code in group.members}
    supplied: dict[str, int] = defaultdict(int)
    missing: list[dict[str, Any]] = []

    for r in records:
        code = r["facility_code"]
        if code not in group.members:
            continue
        interval = to_naive_datetime(r["interval"])
        if trading_day_of(interval) != trading_day:
            continue
        supplied[code] += 1
        if interval not in taken:
            missing.append({**r, "interval": interval})

    return missing, dict(supplied)


def to_naive_datetime(value: Any) -> datetime:
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if not isinstance(value, datetime):
        raise TypeError(f"not a datetime: {value!r}")
    return value.replace(tzinfo=None)


def contiguous_spans(days: Iterable[date]) -> list[tuple[date, date]]:
    """Collapse trading days into inclusive (first, last) runs."""
    spans: list[tuple[date, date]] = []
    for day in sorted(set(days)):
        if spans and day == spans[-1][1] + timedelta(days=1):
            spans[-1] = (spans[-1][0], day)
        else:
            spans.append((day, day))
    return spans


def followup_commands(days: Iterable[date]) -> list[str]:
    """Energy backfill (flag 0 -> 2, plus the trapezoid of the interval after each hole) then clickhouse re-agg."""
    env = "ENV=production PYTHONPATH=$PWD uv run --no-sync python"
    energy: list[str] = []
    reagg: list[str] = []

    for first, last in contiguous_spans(days):
        start, end = trading_day_bounds(first, last)
        # include the interval after the span: its trapezoid used a LAG across the hole (#771)
        e_start, e_end = start, end + timedelta(minutes=10)
        s, e = e_start.isoformat(), e_end.isoformat()
        energy.append(f"{env} bin/energy_backfill.py --start {s} --end {e} --apply --i-know-this-writes")
        energy.append(f"{env} bin/energy_backfill.py --repair --start {s} --end {e} --apply --i-know-this-writes")
        reagg.append(
            f'{env} -c "import asyncio; from datetime import datetime as d; '
            f"from opennem.workers.next_day_heal import reaggregate_nem_window as r; "
            f"asyncio.run(r(d.fromisoformat('{s}'), d.fromisoformat('{e}')))\""
        )

    return energy + reagg


def format_table(plans: Iterable[UnitDayPlan]) -> str:
    rows = [f"{'unit':<10} {'trading_day':<11} {'reason':<15} {'rows_now':>8} {'file_rows':>9} {'to_insert':>9}"]
    for p in plans:
        rows.append(
            f"{p.unit_code:<10} {p.trading_day.isoformat():<11} {p.reason:<15} {p.rows_now:>8} {p.file_rows:>9} {p.to_insert:>9}"
        )
    return "\n".join(rows)


def daily_file_day(name: str) -> date | None:
    """Trading day from PUBLIC_NEXT_DAY_DISPATCH_YYYYMMDD_<seq>.zip, None for the monthly archive name."""
    stem = name.rsplit("/", 1)[-1].upper()
    parts = stem.removesuffix(".ZIP").split("_")
    if len(parts) != 6 or not parts[4].isdigit() or len(parts[4]) != 8:
        return None
    return datetime.strptime(parts[4], "%Y%m%d").date()


def archive_name_for(day: date) -> str:
    return f"PUBLIC_NEXT_DAY_DISPATCH_{day:%Y%m}01.zip"


# io


_COUNT_QUERY = """
    with g(code, grp) as (select * from unnest(cast(:codes as text[]), cast(:grps as text[])))
    select g.grp, date(fs.interval - interval '4 hours 5 minutes') as trading_day, count(distinct fs.interval)
    from facility_scada fs join g on g.code = fs.facility_code
    where fs.network_id = 'NEM' and fs.is_forecast is false and fs.interval > :start and fs.interval <= :end
    group by 1, 2
"""

_KEYS_QUERY = """
    select facility_code, interval from facility_scada
    where network_id = 'NEM' and is_forecast is false and facility_code = any(cast(:codes as text[]))
      and interval > :start and interval <= :end
"""


async def count_group_days(groups: list[UnitGroup], start_day: date, end_day: date) -> dict[tuple[str, date], int]:
    from sqlalchemy import text

    from opennem.db import get_read_session

    codes: list[str] = []
    grps: list[str] = []
    for g in groups:
        for m in g.members:
            codes.append(m)
            grps.append(g.name)
        if g.parent:
            codes.append(g.parent)
            grps.append(f"parent:{g.parent}")

    start, end = trading_day_bounds(start_day, end_day)
    async with get_read_session() as session:
        rows = (await session.execute(text(_COUNT_QUERY), {"codes": codes, "grps": grps, "start": start, "end": end})).all()
    return {(str(grp), day): int(n) for grp, day, n in rows}


async def existing_keys(codes: Iterable[str], day: date) -> set[Key]:
    from sqlalchemy import text

    from opennem.db import get_read_session

    start, end = trading_day_bounds(day, day)
    async with get_read_session() as session:
        rows = (await session.execute(text(_KEYS_QUERY), {"codes": sorted(codes), "start": start, "end": end})).all()
    return {(str(c), i) for c, i in rows}


async def list_current_files() -> dict[date, str]:
    """Trading day -> newest CURRENT file url."""
    from opennem.core.parsers.dirlisting import get_dirlisting

    listing = await get_dirlisting(CURRENT_URL, timezone="Australia/Brisbane")
    picked: dict[date, Any] = {}
    for entry in listing.get_files():
        day = daily_file_day(str(entry.link))
        if day and (day not in picked or entry.modified_date > picked[day].modified_date):
            picked[day] = entry
    return {d: str(e.link) for d, e in picked.items()}


async def _get_bytes(url: str) -> bytes:
    from opennem.utils.http import http_factory

    response = await http_factory(proxy=True).get(url)
    response.raise_for_status()
    return response.content


def _csv_lines_from_daily_zip(blob: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.upper().endswith(".CSV")]
        if len(names) != 1:
            raise ValueError(f"expected one csv in daily zip, got {names}")
        with zf.open(names[0]) as fh:
            return [ln for ln in io.TextIOWrapper(fh, encoding="utf-8") if ln.startswith(UNIT_SOLUTION_PREFIXES)]


async def fetch_unit_solution_lines(
    day: date, current: Mapping[date, str], archive_cache: dict[str, bytes]
) -> tuple[str, list[str]]:
    """(source url, DISPATCH_UNIT_SOLUTION lines) for one trading day, CURRENT first then the monthly ARCHIVE zip."""
    if day in current:
        url = current[day]
        return url, await asyncio.to_thread(_csv_lines_from_daily_zip, await _get_bytes(url))

    month_url = ARCHIVE_URL + archive_name_for(day)
    if month_url not in archive_cache:
        archive_cache.clear()  # ~200MB each, keep one month in memory
        archive_cache[month_url] = await _get_bytes(month_url)

    def inner() -> list[str]:
        with zipfile.ZipFile(io.BytesIO(archive_cache[month_url])) as outer:
            members = [n for n in outer.namelist() if daily_file_day(n) == day]
            if not members:
                raise FileNotFoundError(f"no file for {day} in {month_url}")
            return _csv_lines_from_daily_zip(outer.read(sorted(members)[-1]))

    return f"{month_url}#{day}", await asyncio.to_thread(inner)


async def transform(lines: list[str], duids: Iterable[str]) -> list[dict[str, Any]]:
    """The crawler's own parse + generate_facility_scada over the filtered DISPATCH_UNIT_SOLUTION rows."""
    from opennem.controllers.nem import generate_facility_scada
    from opennem.core.parsers.aemo.mms import parse_aemo_mms_csv

    content = filter_unit_solution_csv(lines, duids)
    if not content:
        return []
    table_set = parse_aemo_mms_csv(content)
    table = next((t for t in table_set.tables if t.full_name.lower() == "dispatch_unit_solution"), None)
    if not table or not table.records:
        return []
    records = await generate_facility_scada(
        table.records,  # type: ignore[arg-type]
        interval_field="settlementdate",
        facility_code_field="duid",
        power_field="initialmw",
        energy_storage_field="energy_storage",
    )
    return [{str(k): v for k, v in r.items()} for r in records]


async def write_rows(rows: list[dict[str, Any]]) -> int:
    from opennem.controllers.nem import UNIT_SOLUTION_UPDATE_COLUMNS
    from opennem.db.bulk_insert_csv import bulkinsert_mms_items
    from opennem.db.models.opennem import FacilityScada

    return await bulkinsert_mms_items(FacilityScada, rows, UNIT_SOLUTION_UPDATE_COLUMNS, keep_processed_energy=True)  # type: ignore[arg-type]


async def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    from opennem import settings
    from opennem.core.battery import get_battery_unit_map

    host, dbname = describe_target(str(settings.db_url))
    refusal = check_write_allowed(args, settings.env, host)
    if refusal:
        print(refusal, file=sys.stderr)
        return 3

    end_day = args.end_day or default_end_day(datetime.now(ZoneInfo("Australia/Brisbane")).replace(tzinfo=None))
    if end_day < args.start_day:
        print("--end-day is before --start-day", file=sys.stderr)
        return 2

    units = set(args.units) if args.units else set(NEXT_DAY_ONLY_UNITS)
    unknown = units - NEXT_DAY_ONLY_UNITS
    if unknown:
        print(f"not next-day-only units: {sorted(unknown)}", file=sys.stderr)
        return 2

    print(f"target: {host}/{dbname}  env: {settings.env}  mode: {'APPLY' if args.apply else 'dry run'}")
    print(f"scan: trading days {args.start_day} .. {end_day}  units: {','.join(sorted(units))}")

    groups = build_groups(units, await get_battery_unit_map())
    counts = await count_group_days(groups, args.start_day - timedelta(days=1), end_day)
    gaps = find_gap_days(groups, counts, args.start_day, end_day, args.include_pre_split)
    if args.days:
        gaps = [g for g in gaps if g.trading_day in set(args.days)]

    if not gaps:
        print("no gap days found")
        return 0

    by_day: dict[date, list[GapDay]] = defaultdict(list)
    for g in gaps:
        by_day[g.trading_day].append(g)
    print(f"{len(gaps)} gap group-days over {len(by_day)} trading days, fetching files")

    current = await list_current_files()
    archive_cache: dict[str, bytes] = {}
    plans: list[UnitDayPlan] = []
    written_days: list[date] = []
    failed: list[str] = []

    for day in sorted(by_day):
        day_gaps = by_day[day]
        duids = {d for g in day_gaps for d in g.group.source_duids}
        try:
            source, lines = await fetch_unit_solution_lines(day, current, archive_cache)
            records = await transform(lines, duids)
        except Exception as e:
            failed.append(f"{day}: {e}")
            print(f"  {day}: fetch/parse failed: {e}", file=sys.stderr)
            continue

        members = {m for g in day_gaps for m in g.group.members}
        existing = await existing_keys(members, day)
        to_write: list[dict[str, Any]] = []

        for g in day_gaps:
            missing, supplied = keep_missing(records, g.group, day, existing)
            to_write.extend(missing)
            missing_by_code: dict[str, int] = defaultdict(int)
            for r in missing:
                missing_by_code[r["facility_code"]] += 1
            for code in g.group.members:
                rows_now = sum(1 for c, _ in existing if c == code)
                plans.append(UnitDayPlan(code, day, g.reason, rows_now, supplied.get(code, 0), missing_by_code.get(code, 0)))

        print(f"  {day}: {source.rsplit('/', 1)[-1]} -> {len(to_write)} rows to insert")

        if args.apply and to_write:
            inserted = await write_rows(to_write)
            print(f"    applied: {inserted} rows upserted")
            written_days.append(day)
        elif to_write:
            written_days.append(day)

    print()
    print(format_table(plans))
    total = sum(p.to_insert for p in plans)
    print(f"\n{total:,} rows {'inserted' if args.apply else 'would be inserted'} over {len(written_days)} trading days")
    if failed:
        print(f"{len(failed)} days failed: {failed}")

    if written_days:
        print("\nfollow-up, in order (energy first, then clickhouse), after --apply:")
        for cmd in followup_commands(written_days):
            print(f"  {cmd}")

    if not args.apply:
        print("\ndry run: nothing written. re-run with ENV=production --apply --i-know-this-writes to write.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
