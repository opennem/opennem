"""Repeatable read-only benchmark for the DEV API (https://api.oedev.org).

Dev only: refuses any base url that is not the dev host. GET requests only, no admin or webhook routes.
Keys are read at runtime from the opennem .env (never printed or written to results).

Usage (from repo root):
    PYTHONPATH=$PWD uv run --no-sync python bin/bench_api.py --dry-run
    PYTHONPATH=$PWD uv run --no-sync python bin/bench_api.py --out bench-dev.json
    PYTHONPATH=$PWD uv run --no-sync python bin/bench_api.py --burst --wait-idle 660 --out burst.json
    PYTHONPATH=$PWD uv run --no-sync python bin/bench_api.py --report bench-dev.json --server-spans spans.json

spans.json (from Sentry http.server spans, per transaction): {"get_facilities": {"p50": 41, "p95": 619, "n": 12}, ...}
"""

import argparse
import asyncio
import json
import math
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

DEV_HOST = "api.oedev.org"
DEFAULT_BASE = f"https://{DEV_HOST}"
DEFAULT_ENV_FILE = Path("/Users/n/Projects/Opennem/opennem/.env")
LEVELS = (1, 5, 20)
TIMING_HEADERS = ("x-process-time", "x-response-time", "server-timing")
MAX_ERROR_RATE = 0.05
MAX_P95_S = 10.0

# prod 7d Sentry http.server span ms {transaction: [p50, p95]}
BASELINE_FILE = Path(__file__).with_name("bench_baseline_prod_7d.json")
BASELINE_PROD_7D: dict[str, tuple[float, float]] = {k: (v[0], v[1]) for k, v in json.loads(BASELINE_FILE.read_text()).items()}

# group -> server-side warm p50 target (ms)
TARGET_P50_MS: dict[str, float] = {
    "get_facility_data": 100,
    "data get_network_data": 100,
    "market get_network_data": 100,
    "get_user_me": 300,
    "get_facility_pollution": 50,
    "get_metrics": 20,
    "get_facilities": 50,
}
TARGET_P95_MS = 1000
P95_EXEMPT = {"get_facility_pollution"}


@dataclass(frozen=True)
class Endpoint:
    name: str
    group: str
    path: str
    auth: bool = True
    scale: float = 1.0  # request-count multiplier (throttle slow/third-party-backed routes)


def build_endpoints(milestone_record_id: str | None) -> list[Endpoint]:
    d = "date_start={s}&date_end={e}"
    nem = "/v4/data/network/NEM?"
    mkt = "/v4/market/network/NEM?"
    fac = "/v4/data/facilities/NEM?"
    eps = [
        Endpoint("health", "health", "/health", auth=False),
        Endpoint("me", "get_user_me", "/v4/me", scale=0.3),
        Endpoint("facilities_all", "get_facilities", "/v4/facilities/"),
        Endpoint("facilities_nem", "get_facilities", "/v4/facilities/?network_id=NEM"),
        Endpoint("facilities_coal", "get_facilities", "/v4/facilities/?fueltech_group_id=coal"),
        Endpoint("facilities_code", "get_facilities", "/v4/facilities/?facility_code=BANGOWF"),
        Endpoint(
            "fd_power_5m",
            "get_facility_data",
            fac + "metrics=power&interval=5m&facility_code=BANGOWF&" + d.format(s="2025-06-10T00:00:00", e="2025-06-12T00:00:00"),
        ),
        Endpoint(
            "fd_energy_1d",
            "get_facility_data",
            fac
            + "metrics=energy&interval=1d&facility_code=BANGOWF&facility_code=ERARING&"
            + d.format(s="2025-05-01T00:00:00", e="2025-06-01T00:00:00"),
        ),
        Endpoint(
            "fd_multi_5m",
            "get_facility_data",
            fac
            + "metrics=energy&metrics=power&interval=5m&facility_code=BANGOWF&facility_code=ERARING&facility_code=HALLWF&"
            + d.format(s="2025-06-10T00:00:00", e="2025-06-11T00:00:00"),
        ),
        Endpoint(
            "fd_emissions_1d",
            "get_facility_data",
            fac
            + "metrics=emissions&metrics=market_value&interval=1d&facility_code=ERARING&"
            + d.format(s="2025-05-01T00:00:00", e="2025-06-01T00:00:00"),
        ),
        Endpoint(
            "fd_monthly",
            "get_facility_data",
            fac
            + "metrics=energy&interval=1M&facility_code=ERARING&"
            + d.format(s="2023-01-01T00:00:00", e="2025-01-01T00:00:00"),
        ),
        Endpoint(
            "fd_no_filter_1d",
            "get_facility_data",
            fac + "metrics=energy&interval=1d&" + d.format(s="2025-06-10T00:00:00", e="2025-06-11T00:00:00"),
        ),
        Endpoint("fd_live", "get_facility_data", fac + "metrics=power&interval=5m&facility_code=BANGOWF"),
        Endpoint(
            "nd_power_5m_6h",
            "data get_network_data",
            nem
            + "metrics=power&interval=5m&primary_grouping=network_region&"
            + d.format(s="2025-06-10T00:00:00", e="2025-06-10T06:00:00"),
        ),
        Endpoint(
            "nd_power_5m_1d",
            "data get_network_data",
            nem
            + "metrics=power&interval=5m&secondary_grouping=fueltech_group&"
            + d.format(s="2025-06-10T00:00:00", e="2025-06-11T00:00:00"),
        ),
        Endpoint(
            "nd_power_5m_7d",
            "data get_network_data",
            nem
            + "metrics=power&interval=5m&secondary_grouping=fueltech_group&"
            + d.format(s="2025-06-03T00:00:00", e="2025-06-10T00:00:00"),
        ),
        Endpoint(
            "nd_energy_1h_2d",
            "data get_network_data",
            nem
            + "metrics=energy&interval=1h&secondary_grouping=fueltech&"
            + d.format(s="2025-06-10T00:00:00", e="2025-06-12T00:00:00"),
        ),
        Endpoint(
            "nd_multi_1d",
            "data get_network_data",
            nem
            + "metrics=energy&metrics=emissions&metrics=market_value&interval=1d&network_region=NSW1&"
            + d.format(s="2025-05-01T00:00:00", e="2025-06-01T00:00:00"),
        ),
        Endpoint(
            "nd_wem_30m",
            "data get_network_data",
            "/v4/data/network/WEM?metrics=power&interval=30m&secondary_grouping=fueltech_group&"
            + d.format(s="2025-06-01T00:00:00", e="2025-06-03T00:00:00"),
        ),
        Endpoint(
            "nd_battery_1h",
            "data get_network_data",
            nem
            + "metrics=storage_battery&interval=1h&network_region=SA1&"
            + d.format(s="2025-06-10T00:00:00", e="2025-06-12T00:00:00"),
        ),
        Endpoint(
            "nd_monthly_2y",
            "data get_network_data",
            nem
            + "metrics=energy&interval=1M&secondary_grouping=fueltech_group&"
            + d.format(s="2023-01-01T00:00:00", e="2025-01-01T00:00:00"),
        ),
        Endpoint("nd_live", "data get_network_data", nem + "metrics=power&interval=5m&secondary_grouping=fueltech_group"),
        Endpoint(
            "mk_price_demand_5m",
            "market get_network_data",
            mkt
            + "metrics=price&metrics=demand&interval=5m&primary_grouping=network_region&"
            + d.format(s="2025-06-10T00:00:00", e="2025-06-12T00:00:00"),
        ),
        Endpoint(
            "mk_price_5m_7d",
            "market get_network_data",
            mkt + "metrics=price&interval=5m&network_region=NSW1&" + d.format(s="2025-06-03T00:00:00", e="2025-06-10T00:00:00"),
        ),
        Endpoint(
            "mk_price_1h",
            "market get_network_data",
            mkt + "metrics=price&interval=1h&network_region=NSW1&" + d.format(s="2025-06-10T00:00:00", e="2025-06-12T00:00:00"),
        ),
        Endpoint(
            "mk_curtailment_1d",
            "market get_network_data",
            mkt
            + "metrics=curtailment&metrics=curtailment_energy&interval=1d&"
            + d.format(s="2025-05-01T00:00:00", e="2025-06-01T00:00:00"),
        ),
        Endpoint(
            "mk_renew_prop_1d",
            "market get_network_data",
            mkt
            + "metrics=renewable_proportion&interval=1d&primary_grouping=network_region&"
            + d.format(s="2025-05-01T00:00:00", e="2025-06-01T00:00:00"),
        ),
        Endpoint(
            "mk_flows_1h",
            "market get_network_data",
            mkt
            + "metrics=flow_imports&metrics=flow_exports&interval=1h&network_region=VIC1&"
            + d.format(s="2025-06-10T00:00:00", e="2025-06-12T00:00:00"),
        ),
        Endpoint(
            "mk_wem_30m",
            "market get_network_data",
            "/v4/market/network/WEM?metrics=price&metrics=demand&interval=30m&"
            + d.format(s="2025-06-01T00:00:00", e="2025-06-03T00:00:00"),
        ),
        Endpoint(
            "mk_monthly",
            "market get_network_data",
            mkt
            + "metrics=demand_energy&metrics=generation_renewable_energy&interval=1M&"
            + d.format(s="2023-01-01T00:00:00", e="2025-01-01T00:00:00"),
        ),
        Endpoint("mk_live", "market get_network_data", mkt + "metrics=price&metrics=demand&interval=5m"),
        Endpoint("pollution_default", "get_facility_pollution", "/v4/pollution/facilities"),
        Endpoint("pollution_yallourn", "get_facility_pollution", "/v4/pollution/facilities?facility_code=YALLOURN"),
        Endpoint(
            "pollution_nox",
            "get_facility_pollution",
            "/v4/pollution/facilities?facility_code=BAYSWATER&facility_code=ERARING&pollutant_code=nox",
        ),
        Endpoint("metrics", "get_metrics", "/v4/metrics"),
        Endpoint("station_7d", "power_station_v4", "/v4/stats/power/station/NEM/BANGOWF"),
        Endpoint("station_1M_1h", "power_station_v4", "/v4/stats/power/station/NEM/BANGOWF?period=1M&interval=1h"),
    ]
    if milestone_record_id:
        eps.append(Endpoint("milestone_history", "get_milestone_by_record_id", f"/v4/milestones/history/{milestone_record_id}"))
    return eps


DRY_RUN_NAMES = (
    "health",
    "me",
    "facilities_code",
    "fd_power_5m",
    "nd_power_5m_6h",
    "mk_price_1h",
    "pollution_default",
    "metrics",
    "milestone_history",
)


@dataclass
class Sample:
    status: int  # 0 = transport error
    seconds: float
    nbytes: int
    server_timing: str | None = None
    error: str | None = None

    @property
    def is_error(self) -> bool:
        return self.status == 0 or self.status == 429 or self.status >= 500


@dataclass
class RunState:
    started: float = field(default_factory=time.monotonic)
    requests: int = 0
    aborted: str | None = None


# ---- pure stats ----


def percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (0-100) of an ascending list."""
    if not sorted_values:
        return math.nan
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100) * (len(sorted_values) - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (rank - lo)


def summarize(samples: list[Sample], wall_seconds: float) -> dict[str, Any]:
    """Latency percentiles (ms), error rate, req/s and bytes for one batch of samples."""
    n = len(samples)
    if n == 0:
        return {"n": 0}
    ms = sorted(s.seconds * 1000 for s in samples)
    errors = sum(1 for s in samples if s.is_error)
    statuses: dict[str, int] = {}
    for s in samples:
        statuses[str(s.status)] = statuses.get(str(s.status), 0) + 1
    return {
        "n": n,
        "p50": round(percentile(ms, 50), 1),
        "p90": round(percentile(ms, 90), 1),
        "p95": round(percentile(ms, 95), 1),
        "p99": round(percentile(ms, 99), 1),
        "max": round(ms[-1], 1),
        "error_rate": round(errors / n, 4),
        "rps": round(n / wall_seconds, 2) if wall_seconds > 0 else None,
        "avg_bytes": round(sum(s.nbytes for s in samples) / n),
        "statuses": statuses,
    }


def should_abort(summary: dict[str, Any]) -> str | None:
    if summary.get("n", 0) == 0:
        return None
    if summary["error_rate"] > MAX_ERROR_RATE:
        return f"error rate {summary['error_rate']:.1%} > {MAX_ERROR_RATE:.0%}"
    if summary["p95"] > MAX_P95_S * 1000:
        return f"p95 {summary['p95']}ms > {MAX_P95_S}s"
    return None


# ---- http ----


def read_env_key(env_file: Path, var: str) -> str:
    for line in env_file.read_text().splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == var:
            return value.strip().strip('"').strip("'")
    raise SystemExit(f"{var} not found in {env_file}")


async def timed_get(client: httpx.AsyncClient, path: str, headers: dict[str, str]) -> Sample:
    t0 = time.perf_counter()
    try:
        r = await client.get(path, headers=headers)
        body = r.content
    except httpx.HTTPError as e:
        return Sample(0, time.perf_counter() - t0, 0, error=type(e).__name__)
    elapsed = time.perf_counter() - t0
    timing = next((f"{h}={r.headers[h]}" for h in TIMING_HEADERS if h in r.headers), None)
    return Sample(r.status_code, elapsed, len(body), server_timing=timing)


async def run_level(
    client: httpx.AsyncClient, ep: Endpoint, headers: dict[str, str], concurrency: int, total: int, state: RunState
) -> tuple[list[Sample], float]:
    """Fire `total` requests with at most `concurrency` in flight."""
    sem = asyncio.Semaphore(concurrency)
    samples: list[Sample] = []

    async def one() -> None:
        async with sem:
            samples.append(await timed_get(client, ep.path, headers))
            state.requests += 1

    t0 = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(total)))
    return samples, time.perf_counter() - t0


async def prewarm_connections(client: httpx.AsyncClient, n: int) -> None:
    """Open n keep-alive connections via /health so TLS handshakes don't pollute samples."""
    await asyncio.gather(*(client.get("/health") for _ in range(n)), return_exceptions=True)


async def discover_milestone_id(client: httpx.AsyncClient, headers: dict[str, str]) -> str | None:
    r = await client.get("/v4/milestones/records?limit=3", headers=headers)
    data = r.json().get("data") if r.status_code == 200 else None
    return data[0]["record_id"] if data else None


def make_client(base: str, concurrency: int) -> httpx.AsyncClient:
    limits = httpx.Limits(max_connections=max(concurrency, 1), max_keepalive_connections=max(concurrency, 1))
    return httpx.AsyncClient(base_url=base, timeout=30, limits=limits, headers={"Accept": "application/json"})


def check_dev(base: str) -> None:
    host = urlparse(base).hostname
    if host != DEV_HOST:
        raise SystemExit(f"refusing: base host {host!r} is not {DEV_HOST} (dev only)")


async def run_bench(args: argparse.Namespace, key: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {key}"}
    state = RunState()
    started_at = datetime.now(UTC)
    results: list[dict[str, Any]] = []
    levels = (1,) if args.dry_run else LEVELS
    per_level = {1: args.n1, 5: args.n5, 20: args.n20}

    async with make_client(args.base, 1) as c0:
        mid = await discover_milestone_id(c0, headers)
    endpoints = build_endpoints(mid)
    if args.dry_run:
        endpoints = [e for e in endpoints if e.name in DRY_RUN_NAMES]
    if args.only:
        endpoints = [e for e in endpoints if e.name in args.only or e.group in args.only]

    for ep in endpoints:
        if state.aborted:
            break
        if time.monotonic() - state.started > args.max_seconds:
            state.aborted = f"time budget {args.max_seconds}s exhausted before {ep.name}"
            break
        h = headers if ep.auth else {}
        row: dict[str, Any] = {"name": ep.name, "group": ep.group, "path": ep.path, "levels": {}}
        async with make_client(args.base, max(levels)) as client:
            if not args.dry_run:
                await prewarm_connections(client, max(levels))
            cold = await timed_get(client, ep.path, h)
            state.requests += 1
            row["cold"] = {
                "status": cold.status,
                "ms": round(cold.seconds * 1000, 1),
                "bytes": cold.nbytes,
                "server_timing": cold.server_timing,
            }
            for lvl in levels:
                if args.dry_run:
                    total = 1
                else:
                    total = max(1, min(300, round(per_level[lvl] * ep.scale)))
                samples, wall = await run_level(client, ep, h, lvl, total, state)
                summ = summarize(samples, wall)
                summ["server_timing_sample"] = next((s.server_timing for s in samples if s.server_timing), None)
                row["levels"][str(lvl)] = summ
                reason = should_abort(summ)
                if reason:
                    state.aborted = f"{ep.name} c={lvl}: {reason}"
                    break
                await asyncio.sleep(args.pause)
        print(
            f"{ep.name:24s} cold={row['cold']['ms']:>8}ms "
            + " ".join(f"c{k}:p50={v['p50']}/p95={v['p95']}/err={v['error_rate']}" for k, v in row["levels"].items()),
            flush=True,
        )
        results.append(row)

    return {
        "base": args.base,
        "started_at": started_at.isoformat(),
        "ended_at": datetime.now(UTC).isoformat(),
        "dry_run": args.dry_run,
        "key_var": args.key_var,
        "total_requests": state.requests,
        "aborted": state.aborted,
        "endpoints": results,
    }


async def run_burst(args: argparse.Namespace, key: str) -> dict[str, Any]:
    """20 concurrent first requests with a (presumed) expired auth cache. Caller guarantees idle time via --wait-idle."""
    if args.wait_idle:
        print(f"waiting {args.wait_idle}s for auth cache expiry", flush=True)
        await asyncio.sleep(args.wait_idle)
    path = "/v4/facilities/?facility_code=BANGOWF"
    headers = {"Authorization": f"Bearer {key}"}
    n = 20
    async with make_client(args.base, n) as client:
        await prewarm_connections(client, n)
        started_at = datetime.now(UTC)
        t0 = time.perf_counter()
        samples = await asyncio.gather(*(timed_get(client, path, headers) for _ in range(n)))
        wall = time.perf_counter() - t0
        ended_at = datetime.now(UTC)
        after = [await timed_get(client, path, headers) for _ in range(5)]
    return {
        "base": args.base,
        "path": path,
        "waited_idle_s": args.wait_idle,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "burst": summarize(list(samples), wall),
        "burst_ms_sorted": sorted(round(s.seconds * 1000) for s in samples),
        "after_warm": summarize(after, sum(s.seconds for s in after)),
    }


# ---- report ----


def pooled_warm(rows: list[dict[str, Any]], group: str) -> dict[str, float] | None:
    """Group client-side stat at c=1 (median/max of endpoint p50/p95 so groups with many cases stay comparable)."""
    p50s = [r["levels"]["1"]["p50"] for r in rows if r["group"] == group and "1" in r["levels"]]
    p95s = [r["levels"]["1"]["p95"] for r in rows if r["group"] == group and "1" in r["levels"]]
    if not p50s:
        return None
    return {"p50": percentile(sorted(p50s), 50), "p95": max(p95s)}


def render_report(result: dict[str, Any], spans: dict[str, dict[str, float]]) -> str:
    rows = result["endpoints"]
    lines = [
        f"# dev api benchmark ({result['started_at']} .. {result['ended_at']})",
        f"requests={result['total_requests']} aborted={result['aborted']}",
        "",
        "| group | prod p50/p95 | dev client c1 p50/p95 | dev server p50/p95 | target p50 | p50 | p95<=1s |",
        "|---|---|---|---|---|---|---|",
    ]
    for group, (b50, b95) in BASELINE_PROD_7D.items():
        cl = pooled_warm(rows, group)
        sv = spans.get(group)
        tgt = TARGET_P50_MS.get(group)
        p50_ok = "n/a"
        p95_ok = "n/a"
        if tgt is not None and sv:
            p50_ok = "PASS" if sv["p50"] <= tgt else "FAIL"
        if sv:
            p95_ok = "PASS" if (sv["p95"] <= TARGET_P95_MS or group in P95_EXEMPT) else "FAIL"
        cls = f"{cl['p50']:.0f}/{cl['p95']:.0f}" if cl else "-"
        svs = f"{sv['p50']:.0f}/{sv['p95']:.0f}" if sv else "-"
        lines.append(f"| {group} | {b50:g}/{b95:g} | {cls} | {svs} | {tgt if tgt is not None else '-'} | {p50_ok} | {p95_ok} |")
    lines += [
        "",
        "| endpoint | cold ms | c1 p50/p95 | c5 p50/p95 | c20 p50/p95 | c20 rps | err |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lv: dict[str, Any] = r["levels"]
        cells = [f"{lv[k]['p50']:.0f}/{lv[k]['p95']:.0f}" if k in lv else "-" for k in ("1", "5", "20")]
        err = max((v["error_rate"] for v in lv.values()), default=0)
        rps = lv["20"]["rps"] if "20" in lv else "-"
        cold = f"{r['cold']['ms']:.0f} ({r['cold']['status']})"
        lines.append(f"| {r['name']} | {cold} | {cells[0]} | {cells[1]} | {cells[2]} | {rps} | {err} |")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    p.add_argument(
        "--key-var", default="API_KEY_DEV_TEST_KEY", help="env var holding the bearer key (read at runtime, never printed)"
    )
    p.add_argument("--dry-run", action="store_true", help="<=20 requests, concurrency 1, one cold + one warm per endpoint subset")
    p.add_argument("--burst", action="store_true", help="cold-key burst test: 20 concurrent first requests")
    p.add_argument("--wait-idle", type=int, default=0, help="seconds to sleep before the burst so the auth cache expires")
    p.add_argument("--only", nargs="*", help="endpoint names or groups to run")
    p.add_argument("--n1", type=int, default=20, help="requests at c=1 (before scale)")
    p.add_argument("--n5", type=int, default=50)
    p.add_argument("--n20", type=int, default=100)
    p.add_argument("--pause", type=float, default=0.5, help="seconds between levels")
    p.add_argument("--max-seconds", type=int, default=600, help="total run time budget")
    p.add_argument("--out", type=Path)
    p.add_argument("--report", type=Path, help="render a markdown report from a results json (no requests)")
    p.add_argument("--server-spans", type=Path, help="json of Sentry per-transaction p50/p95 for --report")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.report:
        spans = json.loads(args.server_spans.read_text()) if args.server_spans else {}
        print(render_report(json.loads(args.report.read_text()), spans))
        return
    check_dev(args.base)
    key = read_env_key(args.env_file, args.key_var)
    result = asyncio.run(run_burst(args, key) if args.burst else run_bench(args, key))
    if args.out:
        args.out.write_text(json.dumps(result, indent=1))
    print(json.dumps({k: v for k, v in result.items() if k != "endpoints"}, indent=1))


if __name__ == "__main__":
    main()
