"""bin/backfill_next_day_gaps_773.py: gap detection, csv filter, missing-row selection, write guard (#773)."""

import importlib.util
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from opennem.core.battery import BatteryUnitMap

_SPEC = importlib.util.spec_from_file_location(
    "backfill_next_day_gaps_773", Path(__file__).parents[2] / "bin" / "backfill_next_day_gaps_773.py"
)
assert _SPEC and _SPEC.loader
bf = importlib.util.module_from_spec(_SPEC)
sys.modules["backfill_next_day_gaps_773"] = bf
_SPEC.loader.exec_module(bf)

BMAP = {
    "TB3B1": BatteryUnitMap(unit="TB3B1", charge_unit="TB3BL1", discharge_unit="TB3BG1"),
    "0TB3": BatteryUnitMap(unit="TB3B1", charge_unit="TB3BL1", discharge_unit="TB3BG1"),  # station-code alias row
    "OTHER1": BatteryUnitMap(unit="OTHER1", charge_unit="OTHERL1", discharge_unit="OTHERG1"),
}

HEADER = "I,DISPATCH,UNIT_SOLUTION,6,SETTLEMENTDATE,RUNNO,DUID,TRADETYPE,DISPATCHINTERVAL,INTERVENTION,INITIALMW,ENERGY_STORAGE\n"


def _row(ts: str, duid: str, mw: str) -> str:
    return f'D,DISPATCH,UNIT_SOLUTION,6,"{ts}",1,{duid},0,1,0,{mw},\n'


def test_build_groups_pairs_split_batteries_and_skips_alias_rows() -> None:
    groups = bf.build_groups({"SNOWYGJP", "TB3BL1", "TB3BG1"}, BMAP)
    assert [(g.name, g.members, g.parent) for g in groups] == [
        ("SNOWYGJP", ("SNOWYGJP",), None),
        ("TB3B1", ("TB3BG1", "TB3BL1"), "TB3B1"),
    ]
    assert groups[1].source_duids == ("TB3B1",)


def test_find_gap_days_plain_unit_whole_and_partial_days() -> None:
    g = bf.UnitGroup("SNOWYGJP", ("SNOWYGJP",))
    counts = {
        ("SNOWYGJP", date(2026, 2, 21)): 48,  # first (partial) day, not expected full
        ("SNOWYGJP", date(2026, 2, 22)): 288,
        ("SNOWYGJP", date(2026, 2, 24)): 287,
        ("SNOWYGJP", date(2026, 2, 25)): 288,
    }
    gaps = bf.find_gap_days([g], counts, date(2026, 2, 21), date(2026, 2, 25))
    assert [(x.trading_day, x.rows_now, x.reason) for x in gaps] == [
        (date(2026, 2, 23), 0, "short day"),
        (date(2026, 2, 24), 287, "short day"),
    ]


def test_find_gap_days_unit_never_seen_is_skipped() -> None:
    g = bf.UnitGroup("KEPBL1", ("KEPBL1",))
    assert bf.find_gap_days([g], {}, date(2026, 2, 1), date(2026, 2, 5)) == []


def _pair_counts() -> dict[tuple[str, date], int]:
    return {
        ("parent:TB3B1", date(2026, 9, 30)): 288,  # before the G/L mapping: no split rows
        ("parent:TB3B1", date(2026, 10, 1)): 288,
        ("TB3B1", date(2026, 10, 1)): 40,  # mapping went live mid-day
        ("parent:TB3B1", date(2026, 10, 2)): 288,
        ("TB3B1", date(2026, 10, 2)): 288,
        ("parent:TB3B1", date(2026, 10, 3)): 288,  # missed file
        ("parent:TB3B1", date(2026, 10, 4)): 0,  # parent idle: nothing expected
    }


def test_find_gap_days_split_pair_compares_to_parent_after_first_split_day() -> None:
    g = bf.UnitGroup("TB3B1", ("TB3BG1", "TB3BL1"), "TB3B1")
    gaps = bf.find_gap_days([g], _pair_counts(), date(2026, 9, 30), date(2026, 10, 4))
    assert [(x.trading_day, x.rows_now, x.expected, x.reason) for x in gaps] == [(date(2026, 10, 3), 0, 288, "split < parent")]


def test_find_gap_days_pre_split_days_are_opt_in() -> None:
    g = bf.UnitGroup("TB3B1", ("TB3BG1", "TB3BL1"), "TB3B1")
    gaps = bf.find_gap_days([g], _pair_counts(), date(2026, 9, 30), date(2026, 10, 4), include_pre_split=True)
    assert [(x.trading_day, x.rows_now, x.reason) for x in gaps] == [
        (date(2026, 9, 30), 0, "pre-split"),
        (date(2026, 10, 1), 40, "pre-split"),
        (date(2026, 10, 3), 0, "split < parent"),
    ]
    # never split at all: skipped by default, all parent days when opted in
    counts = {("parent:TB3B1", date(2026, 10, 1)): 288}
    assert bf.find_gap_days([g], counts, date(2026, 10, 1), date(2026, 10, 1)) == []
    assert len(bf.find_gap_days([g], counts, date(2026, 10, 1), date(2026, 10, 1), include_pre_split=True)) == 1


def test_filter_unit_solution_csv_keeps_header_and_wanted_duids_only() -> None:
    lines = [
        "C,NEMP.WORLD,NEXT_DAY_DISPATCH\n",
        HEADER,
        _row("2026/02/23 04:05:00", "SNOWYGJP", "-1.5"),
        _row("2026/02/23 04:05:00", "BAYSW1", "600"),
        "I,DISPATCH,LOCAL_PRICE,1,SETTLEMENTDATE,DUID\n",
        'D,DISPATCH,LOCAL_PRICE,1,"2026/02/23 04:05:00",SNOWYGJP\n',
    ]
    out = bf.filter_unit_solution_csv(lines, ["snowygjp"])
    assert out.splitlines() == [
        HEADER.rstrip("\n"),
        _row("2026/02/23 04:05:00", "SNOWYGJP", "-1.5").rstrip("\n"),
        "C,END OF REPORT",
    ]
    assert bf.filter_unit_solution_csv(lines, ["NOPE"]) == HEADER + "C,END OF REPORT\n"
    assert bf.filter_unit_solution_csv(lines[:1], ["SNOWYGJP"]) == ""


def _rec(code: str, ts: str, mw: float = 1.0) -> dict[str, Any]:
    return {"facility_code": code, "interval": datetime.fromisoformat(ts), "generated": mw, "energy_quality_flag": 0}


def test_keep_missing_skips_taken_intervals_across_the_pair_and_other_days() -> None:
    g = bf.UnitGroup("TB3B1", ("TB3BG1", "TB3BL1"), "TB3B1")
    records = [
        _rec("TB3B1", "2026-10-01T04:05"),  # parent row: not ours to write
        _rec("TB3BG1", "2026-10-01T04:05"),  # interval already held by TB3BL1 below
        _rec("TB3BL1", "2026-10-01T04:10"),
        _rec("TB3BG1", "2026-10-02T04:00"),  # last interval of trading day 10-01
        _rec("TB3BG1", "2026-10-02T04:05"),  # next trading day
    ]
    existing = {("TB3BL1", datetime(2026, 10, 1, 4, 5)), ("SNOWYGJP", datetime(2026, 10, 1, 4, 10))}
    missing, supplied = bf.keep_missing(records, g, date(2026, 10, 1), existing)
    assert [(r["facility_code"], r["interval"]) for r in missing] == [
        ("TB3BL1", datetime(2026, 10, 1, 4, 10)),
        ("TB3BG1", datetime(2026, 10, 2, 4, 0)),
    ]
    assert supplied == {"TB3BG1": 2, "TB3BL1": 1}


def test_keep_missing_normalises_pandas_timestamps() -> None:
    import pandas as pd

    g = bf.UnitGroup("SNOWYGJP", ("SNOWYGJP",))
    rec = {"facility_code": "SNOWYGJP", "interval": pd.Timestamp("2026-02-23 04:05")}
    missing, _ = bf.keep_missing([rec], g, date(2026, 2, 23), set())
    assert missing[0]["interval"] == datetime(2026, 2, 23, 4, 5) and type(missing[0]["interval"]) is datetime


def test_contiguous_spans_and_followups() -> None:
    days = [date(2026, 3, 3), date(2026, 3, 2), date(2026, 3, 5), date(2026, 6, 18)]
    assert bf.contiguous_spans(days) == [
        (date(2026, 3, 2), date(2026, 3, 3)),
        (date(2026, 3, 5), date(2026, 3, 5)),
        (date(2026, 6, 18), date(2026, 6, 18)),
    ]
    cmds = bf.followup_commands([date(2026, 6, 18)])
    # trading day 06-18 is 06-18 04:05 .. 06-19 04:00, plus the next interval whose trapezoid used the hole
    assert cmds[0].endswith(
        "bin/energy_backfill.py --start 2026-06-18T04:00:00 --end 2026-06-19T04:10:00 --apply --i-know-this-writes"
    )
    assert "--repair --start 2026-06-18T04:00:00 --end 2026-06-19T04:10:00" in cmds[1]
    assert "reaggregate_nem_window" in cmds[2] and "2026-06-19T04:10:00" in cmds[2]
    assert len(cmds) == 3


def test_file_names() -> None:
    assert bf.daily_file_day("/Reports/CURRENT/Next_Day_Dispatch/PUBLIC_NEXT_DAY_DISPATCH_20260223_0000000504870877.zip") == date(
        2026, 2, 23
    )
    assert bf.daily_file_day("PUBLIC_NEXT_DAY_DISPATCH_20260201.zip") is None
    assert bf.archive_name_for(date(2026, 3, 7)) == "PUBLIC_NEXT_DAY_DISPATCH_20260301.zip"


def test_default_end_day_leaves_two_trading_days() -> None:
    # 03:00 on 10-28 is still trading day 10-27, so the newest surely-published file is 10-25
    assert bf.default_end_day(datetime(2026, 10, 28, 3, 0)) == date(2026, 10, 25)
    assert bf.default_end_day(datetime(2026, 10, 28, 5, 0)) == date(2026, 10, 26)


@pytest.mark.parametrize(
    ("argv", "env", "host", "ok"),
    [
        ([], "production", "db-prod", True),  # dry run always allowed
        (["--apply", "--i-know-this-writes"], "production", "db-prod", True),
        (["--apply"], "production", "db-prod", False),
        (["--apply", "--i-know-this-writes"], "development", "db-prod", False),
        (["--apply", "--i-know-this-writes"], "production", "db-dev", False),
    ],
)
def test_write_guard(argv: list[str], env: str, host: str, ok: bool) -> None:
    args = bf.parse_args(argv)
    assert (bf.check_write_allowed(args, env, host) is None) is ok


def test_parse_args_defaults_to_dry_run() -> None:
    args = bf.parse_args(["--units", "snowygjp, kepbl1", "--days", "2026-02-23,2026-06-18"])
    assert not args.apply and args.units == ["SNOWYGJP", "KEPBL1"]
    assert args.days == [date(2026, 2, 23), date(2026, 6, 18)]
    assert args.start_day == date(2025, 9, 1)


@pytest.mark.asyncio
async def test_transform_runs_crawler_path_with_battery_split(monkeypatch: pytest.MonkeyPatch) -> None:
    import opennem.controllers.nem as nem

    async def fake_map() -> dict[str, BatteryUnitMap]:
        return {"TB3B1": BMAP["TB3B1"]}

    monkeypatch.setattr(nem, "get_battery_unit_map", fake_map)
    lines = [
        HEADER,
        _row("2026/10/01 04:05:00", "TB3B1", "-12"),
        _row("2026/10/01 04:10:00", "TB3B1", "24"),
        _row("2026/10/01 04:05:00", "BAYSW1", "600"),
    ]
    out = await bf.transform(lines, ["TB3B1"])
    got = {(r["facility_code"], bf.to_naive_datetime(r["interval"])): r for r in out}
    assert set(got) == {
        ("TB3B1", datetime(2026, 10, 1, 4, 5)),
        ("TB3B1", datetime(2026, 10, 1, 4, 10)),
        ("TB3BL1", datetime(2026, 10, 1, 4, 5)),
        ("TB3BG1", datetime(2026, 10, 1, 4, 10)),
    }
    charge = got[("TB3BL1", datetime(2026, 10, 1, 4, 5))]
    assert charge["generated"] == 12 and charge["energy"] == 1 and charge["energy_quality_flag"] == 0
    assert charge["network_id"] == "NEM" and charge["is_forecast"] is False
