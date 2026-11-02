import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".github" / "scripts"))

import data_freshness as df  # noqa: E402

NOW = datetime(2026, 11, 3, 4, 0, 0, tzinfo=UTC)  # 14:00 NEM, 12:00 WEM


def chk(lag: float | None, net: str = "NEM") -> df.Check:
    return df.Check(net, lag, "x" if lag is not None else None, None if lag is not None else "boom")


def test_lag_nem_offset():
    assert df.compute_lag_minutes("2026-11-03T13:40:00+10:00", NOW, "NEM") == 20


def test_lag_naive_uses_network_tz():
    assert df.compute_lag_minutes("2026-11-03T11:30:00", NOW, "WEM") == 30


def test_url_network_time():
    assert "date_start=2026-11-03T11:00:00" in df.build_url("NEM", NOW)
    assert "date_start=2026-11-03T09:00:00" in df.build_url("WEM", NOW)


def test_threshold():
    assert not df.is_stale(chk(20))
    assert df.is_stale(chk(20.1))
    assert df.is_stale(chk(None))


def test_first_stale_alerts_then_dedupes():
    msgs, st = df.decide({}, [chk(30), chk(5, "WEM")], NOW)
    assert len(msgs) == 1 and "NEM" in msgs[0] and "30 minutes" in msgs[0]
    msgs2, st2 = df.decide(st, [chk(40), chk(5, "WEM")], NOW + timedelta(minutes=10))
    assert msgs2 == [] and st2 == st


def test_realert_after_60():
    _, st = df.decide({}, [chk(30)], NOW)
    msgs, st2 = df.decide(st, [chk(90)], NOW + timedelta(minutes=60))
    assert len(msgs) == 1 and "still stale" in msgs[0]
    assert st2["NEM"]["since"] == st["NEM"]["since"]


def test_recovered_once():
    _, st = df.decide({}, [chk(30)], NOW)
    msgs, st2 = df.decide(st, [chk(3)], NOW + timedelta(minutes=10))
    assert len(msgs) == 1 and "recovered" in msgs[0] and st2 == {}
    msgs3, _ = df.decide(st2, [chk(3)], NOW + timedelta(minutes=20))
    assert msgs3 == []


def test_unknown_alerts():
    msgs, _ = df.decide({}, [chk(None)], NOW)
    assert "unknown" in msgs[0]
