"""#773: next-day-only units self-heal. No database, no network."""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from opennem.controllers.schema import ControllerReturn
from opennem.core.parsers.aemo.filenames import parse_aemo_filename
from opennem.core.parsers.dirlisting import DirlistingEntry
from opennem.workers import next_day_heal as heal
from opennem.workers.next_day_heal import (
    INTERVALS_PER_TRADING_DAY,
    NEXT_DAY_ONLY_UNITS,
    ShortDay,
    extend_window_start,
    find_short_days,
    format_alert,
    heal_window,
    select_entries_for_days,
    short_trading_days,
    trading_day_bounds,
    trading_day_of,
)

# 05:20 on 28 oct, the cron's last completed interval: trading day 27 oct closed at 04:00
NOW = datetime(2026, 10, 28, 5, 20)
FULL = INTERVALS_PER_TRADING_DAY


def _entry(day: date, modified: datetime, seq: str = "0000000500000001") -> DirlistingEntry:
    name = f"PUBLIC_NEXT_DAY_DISPATCH_{day:%Y%m%d}_{seq}.zip"
    return DirlistingEntry(
        filename=Path(name),
        link=f"https://nemweb.com.au/Reports/Current/Next_Day_Dispatch/{name}",
        modified_date=modified,
        aemo_interval_date=parse_aemo_filename(name),
        file_size=5_000_000,
    )


def _full_counts(units: list[str], days: list[date]) -> dict[tuple[str, date], int]:
    return {(u, d): FULL for u in units for d in days}


# trading day maths


@pytest.mark.parametrize(
    ("interval", "expected"),
    [
        (datetime(2026, 10, 27, 4, 5), date(2026, 10, 27)),
        (datetime(2026, 10, 27, 23, 55), date(2026, 10, 27)),
        (datetime(2026, 10, 28, 0, 0), date(2026, 10, 27)),
        (datetime(2026, 10, 28, 4, 0), date(2026, 10, 27)),
        (datetime(2026, 10, 28, 4, 5), date(2026, 10, 28)),
    ],
)
def test_trading_day_of(interval: datetime, expected: date) -> None:
    assert trading_day_of(interval) == expected


def test_trading_day_bounds_hold_exactly_288_intervals() -> None:
    start, end = trading_day_bounds(date(2026, 10, 27), date(2026, 10, 27))
    assert start == datetime(2026, 10, 27, 4, 0)  # exclusive
    assert end == datetime(2026, 10, 28, 4, 0)  # inclusive
    assert (end - start) / timedelta(minutes=5) == FULL


def test_heal_window_is_last_14_complete_trading_days() -> None:
    window = heal_window(NOW)
    assert len(window) == 14
    assert window[-1] == date(2026, 10, 27)
    assert window[0] == date(2026, 10, 14)
    assert window == sorted(window)


def test_heal_window_before_0405_still_excludes_the_open_day() -> None:
    # 03:00 on 28 oct is still trading day 27 oct, which is open
    assert heal_window(datetime(2026, 10, 28, 3, 0))[-1] == date(2026, 10, 26)


# short day detection


def test_unit_list_covers_issue_units() -> None:
    for code in ("SNOWYGJP", "KEPBL1", "KEPBG1", "WILLBESG1", "WILLBESL1", "WOORBG1", "MRNBESSG1", "TB3BG1", "TB3BL1"):
        assert code in NEXT_DAY_ONLY_UNITS


def test_complete_window_has_no_short_days() -> None:
    window = heal_window(NOW)
    counts = _full_counts(["KEPBL1", "SNOWYGJP"], [window[0] - timedelta(days=1), *window])
    assert find_short_days(counts, ["KEPBL1", "SNOWYGJP"], window) == []


def test_missing_and_partial_days_are_short() -> None:
    window = heal_window(NOW)
    counts = _full_counts(["KEPBL1", "SNOWYGJP"], [window[0] - timedelta(days=1), *window])
    del counts[("KEPBL1", window[3])]  # missed cron: whole day absent
    counts[("SNOWYGJP", window[5])] = 287  # one zero row missing

    short = find_short_days(counts, ["KEPBL1", "SNOWYGJP"], window)

    assert short == [
        ShortDay("KEPBL1", window[3], 0),
        ShortDay("SNOWYGJP", window[5], 287),
    ]
    assert short_trading_days(short) == [window[3], window[5]]


def test_oldest_window_day_is_checked_when_day_before_has_rows() -> None:
    window = heal_window(NOW)
    counts = _full_counts(["KEPBL1"], [window[0] - timedelta(days=1), *window[1:]])
    assert find_short_days(counts, ["KEPBL1"], window) == [ShortDay("KEPBL1", window[0], 0)]


def test_unit_without_rows_is_ignored() -> None:
    window = heal_window(NOW)
    counts = _full_counts(["KEPBL1"], [window[0] - timedelta(days=1), *window])
    # WOORBG1 has nothing at all: not registered yet or retired, a re-crawl can't help
    assert find_short_days(counts, ["KEPBL1", "WOORBG1"], window) == []


def test_sparse_unit_without_a_full_day_is_ignored() -> None:
    window = heal_window(NOW)
    counts = {**_full_counts(["KEPBL1"], [window[0] - timedelta(days=1), *window])}
    # TB3BL1 only dispatches some intervals: never a full day, a re-crawl can't make it 288
    counts.update({("TB3BL1", d): 12 for d in window[::2]})
    assert find_short_days(counts, ["KEPBL1", "TB3BL1"], window) == []


def test_unit_commissioned_mid_window_only_expected_after_first_day() -> None:
    window = heal_window(NOW)
    counts = {("WOORBG1", window[6]): 120, **_full_counts(["WOORBG1"], window[7:])}
    # days before and the partial first day are not flagged
    assert find_short_days(counts, ["WOORBG1"], window) == []


def test_empty_window() -> None:
    assert find_short_days({}, ["KEPBL1"], []) == []


# file selection


def test_select_entries_maps_files_by_trading_day_and_newest_wins() -> None:
    d1, d2, d3 = date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22)
    old = _entry(d2, datetime(2026, 10, 22, 4, 10), seq="0000000500000001")
    new = _entry(d2, datetime(2026, 10, 22, 9, 0), seq="0000000500000002")
    entries = [_entry(d1, datetime(2026, 10, 21, 4, 10)), old, new, _entry(d3, datetime(2026, 10, 23, 4, 10))]

    selected = select_entries_for_days(entries, [d2, d3, date(2026, 9, 1)])

    assert set(selected) == {d2, d3}
    assert selected[d2] is new


def test_extend_window_start() -> None:
    start = datetime(2026, 10, 24, 4, 5)
    assert extend_window_start(start, None) == start
    assert extend_window_start(start, datetime(2026, 10, 18, 4, 5)) == datetime(2026, 10, 18, 4, 5)
    assert extend_window_start(start, datetime(2026, 10, 25, 4, 5)) == start


def test_format_alert_lists_rows_and_missing_files() -> None:
    msg = format_alert([ShortDay("KEPBL1", date(2026, 10, 20), 0)], [date(2026, 10, 20)])
    assert "KEPBL1 2026-10-20: 0/288" in msg
    assert "No file in nemweb CURRENT for: 2026-10-20" in msg


# orchestration


@pytest.mark.asyncio
async def test_heal_recrawls_short_days_and_recounts(monkeypatch: pytest.MonkeyPatch) -> None:
    window = heal_window(NOW)
    full = _full_counts(sorted(NEXT_DAY_ONLY_UNITS), [window[0] - timedelta(days=1), *window])
    before = {k: v for k, v in full.items() if k[1] != window[4]}
    counts = iter([before, full])
    crawled_days: list[list[date]] = []

    async def fake_count(units: Any, first_day: date, last_day: date) -> dict[tuple[str, date], int]:
        assert first_day == window[0] - timedelta(days=1)
        assert last_day == window[-1]
        return next(counts)

    async def fake_recrawl(days: list[date]) -> tuple[ControllerReturn, list[date], list[date]]:
        crawled_days.append(days)
        cr = ControllerReturn(interval_min=datetime(2026, 10, 18, 4, 5), interval_max=datetime(2026, 10, 19, 4, 0))
        return cr, days, []

    monkeypatch.setattr(heal, "count_unit_day_rows", fake_count)
    monkeypatch.setattr(heal, "recrawl_next_day_files", fake_recrawl)

    result = await heal.heal_next_day_units(NOW)

    assert crawled_days == [[window[4]]]
    assert {s.trading_day for s in result.short_before} == {window[4]}
    assert len(result.short_before) == len(NEXT_DAY_ONLY_UNITS)
    assert result.short_after == []
    assert result.crawl.interval_min == datetime(2026, 10, 18, 4, 5)


@pytest.mark.asyncio
async def test_heal_noop_when_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    window = heal_window(NOW)
    full = _full_counts(sorted(NEXT_DAY_ONLY_UNITS), [window[0] - timedelta(days=1), *window])

    async def fake_count(*_: Any) -> dict[tuple[str, date], int]:
        return full

    async def boom(days: list[date]) -> Any:
        raise AssertionError("must not re-crawl a complete window")

    monkeypatch.setattr(heal, "count_unit_day_rows", fake_count)
    monkeypatch.setattr(heal, "recrawl_next_day_files", boom)

    result = await heal.heal_next_day_units(NOW)
    assert result.short_before == [] and result.crawl.interval_min is None


@pytest.mark.asyncio
async def test_alert_only_when_still_short(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []

    async def fake_slack(**kwargs: Any) -> bool:
        sent.append(kwargs["message"])
        return True

    monkeypatch.setattr("opennem.clients.slack.slack_message", fake_slack)

    assert await heal.alert_still_short(heal.HealResult()) is False
    assert sent == []

    still = heal.HealResult(short_after=[ShortDay("TB3BL1", date(2026, 10, 1), 71)])
    assert await heal.alert_still_short(still) is True
    assert "TB3BL1 2026-10-01: 71/288" in sent[0]


@pytest.mark.asyncio
async def test_recrawl_selects_files_and_merges_span(monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.core.parsers.dirlisting import DirectoryListing

    d_listed, d_gone = date(2026, 10, 20), date(2026, 10, 1)
    entry = _entry(d_listed, datetime(2026, 10, 21, 4, 10))
    processed: list[str] = []

    async def fake_dirlisting(url: str, timezone: str | None = None) -> DirectoryListing:
        return DirectoryListing(url=url, timezone=timezone, entries=[entry])

    async def fake_process(crawler: Any, entry: DirlistingEntry, max_date: datetime) -> ControllerReturn:
        processed.append(entry.link)
        return ControllerReturn(
            inserted_records=10,
            interval_min=datetime(2026, 10, 20, 4, 5),
            interval_max=datetime(2026, 10, 21, 4, 0),
        )

    monkeypatch.setattr("opennem.core.parsers.dirlisting.get_dirlisting", fake_dirlisting)
    monkeypatch.setattr("opennem.crawlers.nemweb.process_nemweb_entry", fake_process)

    cr, crawled, without_file = await heal.recrawl_next_day_files([d_gone, d_listed])

    assert processed == [entry.link]
    assert crawled == [d_listed]
    assert without_file == [d_gone]
    assert (cr.interval_min, cr.interval_max) == (datetime(2026, 10, 20, 4, 5), datetime(2026, 10, 21, 4, 0))
    assert cr.inserted_records == 10
