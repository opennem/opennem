import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))

import bench_tracker  # noqa: E402
import check_auth_leak  # noqa: E402
import compare_envs  # noqa: E402
import pytest  # noqa: E402

NAMES = ("dev", "prod")
NEM = timezone(timedelta(hours=10))


def test_percentile() -> None:
    assert math.isnan(bench_tracker.percentile([], 50))
    assert bench_tracker.percentile([5.0], 99) == 5.0
    assert bench_tracker.percentile([4, 1, 3, 2], 50) == 2.5
    assert bench_tracker.percentile(list(range(101)), 95) == 95


def test_cold_window_shifting() -> None:
    now = datetime(2026, 10, 24, 12, 47, 33, tzinfo=NEM)
    warm = bench_tracker.scenario_end(now, False, random.Random(1))
    assert warm == datetime(2026, 10, 24, 12, 45, tzinfo=NEM)
    rng = random.Random(7)
    for _ in range(200):
        cold = bench_tracker.scenario_end(now, True, rng)
        delta = (now.replace(second=0) - cold).total_seconds() / 60
        assert 30 <= delta <= 3001
        assert delta % 5 != 0  # off the 5m grid relative to a grid-aligned now


def test_build_path() -> None:
    end = datetime(2026, 10, 24, 12, 45, tzinfo=NEM)
    p = bench_tracker.build_path("data", "power", "NSW1", end - timedelta(days=1), end, "5m")
    assert p.endswith("&network_region=NSW1&secondary_grouping=fueltech")
    assert "date_start=2026-10-23T12:45:00&date_end=2026-10-24T12:45:00" in p
    assert "secondary_grouping" not in bench_tracker.build_path("market", "price", None, end, end, "5m")


def test_classify_equal_and_ignored_keys() -> None:
    a = {"version": "1", "created_at": "x", "data": [1, 2]}
    b = {"version": "2", "created_at": "y", "data": [1, 2]}
    assert compare_envs.classify(200, 200, a, b, NAMES) == ("equal", [])


def test_classify_value_shape_status() -> None:
    cls, d = compare_envs.classify(200, 200, {"data": [1.0, 2.0]}, {"data": [1.0, 3.0]}, NAMES)
    assert cls == "value" and "dev=2.0 prod=3.0" in d[0]
    assert compare_envs.classify(200, 200, {"data": [1]}, {"data": [1, 2]}, NAMES)[0] == "shape"
    assert compare_envs.classify(200, 200, {"a": 1}, {"b": 1}, NAMES)[0] == "shape"
    assert compare_envs.classify(200, 200, {"a": "x"}, {"a": 1}, NAMES)[0] == "shape"
    assert compare_envs.classify(200, 404, {}, None, NAMES)[0] == "status"
    assert compare_envs.classify(404, 404, None, None, NAMES)[0] == "both_err"


def test_classify_float_tolerance_is_equal() -> None:
    assert compare_envs.classify(200, 200, {"v": 1.0}, {"v": 1.0 + 1e-12}, NAMES)[0] == "equal"


def test_exit_code() -> None:
    assert compare_envs.exit_code({"equal": 5}, False) == 0
    assert compare_envs.exit_code({"value": 2}, False) == 0
    assert compare_envs.exit_code({"value": 2}, True) == 1
    assert compare_envs.exit_code({"shape": 1}, False) == 1
    assert compare_envs.exit_code({"status": 1}, False) == 1


def test_windows_and_cases() -> None:
    assert compare_envs.resolve_windows("short") == compare_envs.WINDOW_SETS["short"]
    assert compare_envs.resolve_windows("7d/1h, 90d/1d") == ["7d/1h", "90d/1d"]
    with pytest.raises(SystemExit):
        compare_envs.resolve_windows("bogus")
    cases = compare_envs.build_cases(datetime(2026, 10, 24, 12, 47, tzinfo=NEM), ["1d/5m"], lag_hours=3)
    assert len(cases) == len(compare_envs.REGIONS) * (len(compare_envs.DATA_SETS) + len(compare_envs.MARKET_SETS))
    assert all("date_end=2026-10-24T09:00:00" in c.path for c in cases)


def _p(status: int, cf: str | None = None, age: str | None = None) -> check_auth_leak.Probe:
    return check_auth_leak.Probe(status, cf, age, None)


def test_leak_judge() -> None:
    assert check_auth_leak.judge(_p(200), [_p(401), _p(401)])[0]
    assert not check_auth_leak.judge(_p(200), [_p(401), _p(200, "HIT", "3")])[0]
    assert not check_auth_leak.judge(_p(200), [_p(200, "DYNAMIC", "5")])[0]
    ok, why = check_auth_leak.judge(_p(200), [_p(200, "DYNAMIC")])
    assert ok and "public" in why
    assert not check_auth_leak.judge(_p(401), [_p(401)])[0]  # inconclusive
