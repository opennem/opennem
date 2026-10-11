import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bin"))

import bench_api  # noqa: E402
from bench_api import Sample, percentile, render_report, should_abort, summarize  # noqa: E402


def test_percentile_interpolates() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert percentile(values, 0) == 10.0
    assert percentile(values, 50) == 30.0
    assert percentile(values, 90) == pytest.approx(46.0)
    assert percentile(values, 100) == 50.0


def test_percentile_edge_cases() -> None:
    assert math.isnan(percentile([], 50))
    assert percentile([7.0], 99) == 7.0


def test_summarize_counts_errors_and_rps() -> None:
    samples = [Sample(200, 0.1, 100) for _ in range(18)] + [Sample(503, 0.2, 10), Sample(0, 1.0, 0)]
    s = summarize(samples, wall_seconds=2.0)
    assert s["n"] == 20
    assert s["error_rate"] == 0.1
    assert s["rps"] == 10.0
    assert s["statuses"] == {"200": 18, "503": 1, "0": 1}
    assert s["p50"] == 100.0


def test_4xx_not_counted_as_error_but_429_is() -> None:
    assert not Sample(404, 0.1, 0).is_error
    assert Sample(429, 0.1, 0).is_error


def test_should_abort_thresholds() -> None:
    ok = summarize([Sample(200, 0.1, 1)] * 20, 1.0)
    assert should_abort(ok) is None
    bad = summarize([Sample(200, 0.1, 1)] * 18 + [Sample(500, 0.1, 1)] * 2, 1.0)
    assert should_abort(bad) is not None
    slow = summarize([Sample(200, 11.0, 1)] * 20, 1.0)
    assert "p95" in (should_abort(slow) or "")


def test_endpoints_are_read_only_and_not_admin() -> None:
    eps = bench_api.build_endpoints("abc")
    assert all(not e.path.startswith(("/v4/admin", "/webhook")) for e in eps)
    assert any(e.name == "milestone_history" for e in eps)
    assert not any(e.name == "milestone_history" for e in bench_api.build_endpoints(None))


def test_render_report_pass_fail() -> None:
    result = {
        "started_at": "a",
        "ended_at": "b",
        "total_requests": 1,
        "aborted": None,
        "endpoints": [
            {
                "name": "metrics",
                "group": "get_metrics",
                "levels": {"1": {"p50": 15, "p95": 30, "rps": 1, "error_rate": 0}},
                "cold": {"ms": 20, "status": 200},
            }
        ],
    }
    out = render_report(result, {"get_metrics": {"p50": 12, "p95": 40}, "get_facilities": {"p50": 90, "p95": 100}})
    assert "| get_metrics |" in out and "PASS" in out and "FAIL" in out


def test_check_dev_refuses_prod() -> None:
    with pytest.raises(SystemExit):
        bench_api.check_dev("https://api.openelectricity.org.au")
    bench_api.check_dev("https://api.oedev.org")
