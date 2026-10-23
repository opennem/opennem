"""Tracker-like load against the DEV API: per-call latency distribution (#745, epic #747).

Dev only: refuses any base url that is not the dev host. GET requests only.
Key is read at runtime from the opennem .env (never printed or written to results).
One scenario = a "region switch": 10 parallel metric calls plus 4 prior-period calls (as the tracker fe does).

Usage (from repo root):
    PYTHONPATH=$PWD uv run --no-sync python bin/bench_tracker.py --label warm --repeat 2
    PYTHONPATH=$PWD uv run --no-sync python bin/bench_tracker.py --label cold --cold --out bench-tracker-cold.json
"""

import argparse
import asyncio
import json
import math
import random
import statistics
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

DEV_HOST = "api.oedev.org"
DEFAULT_BASE = f"https://{DEV_HOST}"
DEFAULT_ENV_FILE = Path("/Users/n/Projects/Opennem/opennem/.env")
NEM_TZ = timezone(timedelta(hours=10))
GRID_MINUTES = 5
REGIONS: list[str | None] = ["NSW1", "QLD1", "SA1", "TAS1", "VIC1", None]  # None = whole NEM
RANGES: dict[str, tuple[timedelta, str]] = {
    "1d": (timedelta(days=1), "5m"),
    "3d": (timedelta(days=3), "5m"),
    "7d": (timedelta(days=7), "5m"),
    "30d": (timedelta(days=30), "30m"),
}
# (kind, name, metrics query fragment)
CALLS: list[tuple[str, str, str]] = [
    ("data", "power", "power"),
    ("data", "emissions_intensity", "emissions&metrics=power"),
    ("data", "market_value", "market_value"),
    ("data", "emissions", "emissions"),
    ("market", "price", "price"),
    ("market", "demand", "demand"),
    ("market", "renewables", "generation_renewable&metrics=demand_gross"),
    ("market", "curtailment", "curtailment_solar_utility&metrics=curtailment_wind"),
    ("market", "renewable_share", "renewable_proportion"),
    ("market", "flows", "flow_imports&metrics=flow_exports"),
]
PRIOR_CALLS = CALLS[:4]  # fe also asks the prior-period window for the heavy metrics
SUMMARY_METRICS = ("power", "emissions_intensity", "market_value", "emissions", "price")

Result = tuple[float, int, str, str, str | None, bool]  # ms, status, metric, range, region, prior


# ---- pure helpers ----


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (0-100) of an unsorted list; nan when empty."""
    if not values:
        return math.nan
    s = sorted(values)
    rank = (pct / 100) * (len(s) - 1)
    lo, hi = math.floor(rank), math.ceil(rank)
    return s[lo] + (s[hi] - s[lo]) * (rank - lo)


def floor_to_grid(dt: datetime, minutes: int = GRID_MINUTES) -> datetime:
    return dt.replace(minute=dt.minute - dt.minute % minutes, second=0, microsecond=0)


def scenario_end(now: datetime, cold: bool, rng: random.Random) -> datetime:
    """Window end. Warm: on the 5m grid (repeats share cache keys). Cold: shifted back 30..3000 min, off the grid."""
    if not cold:
        return floor_to_grid(now)
    minutes = rng.randint(30, 3000)
    if minutes % GRID_MINUTES == 0:
        minutes += 1
    return now.replace(second=0, microsecond=0) - timedelta(minutes=minutes)


def fmt(d: datetime) -> str:
    return d.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")


def build_path(kind: str, metrics: str, region: str | None, start: datetime, end: datetime, interval: str) -> str:
    q = f"/v4/{kind}/network/NEM?metrics={metrics}&interval={interval}&date_start={fmt(start)}&date_end={fmt(end)}"
    if region:
        q += f"&network_region={region}"
    if kind == "data":
        q += "&secondary_grouping=fueltech"
    return q


def stats_line(results: list[Result], with_max: bool = False) -> str:
    ms = [r[0] for r in results if r[1] == 200]
    if not ms:
        return "no successful calls"
    out = f"p50={percentile(ms, 50):.0f} p95={percentile(ms, 95):.0f} p99={percentile(ms, 99):.0f}"
    return out + (f" max={max(ms):.0f}" if with_max else "")


def render_summary(label: str, results: list[Result], rtt_ms: float) -> str:
    errors = sum(1 for r in results if r[1] != 200)
    lines = [f"{label}: n={len(results)} errors={errors} rtt~{rtt_ms:.0f}ms | ALL {stats_line(results, with_max=True)}"]
    for g in RANGES:
        lines.append(f"  {g:>3}: {stats_line([r for r in results if r[3] == g])}")
    for m in SUMMARY_METRICS:
        lines.append(f"  {m:>20}: {stats_line([r for r in results if r[2] == m])}")
    return "\n".join(lines)


# ---- http ----


def check_dev(base: str) -> None:
    host = urlparse(base).hostname
    if host != DEV_HOST:
        raise SystemExit(f"refusing: base host {host!r} is not {DEV_HOST} (dev only)")


def read_env_key(env_file: Path, var: str) -> str:
    for line in env_file.read_text().splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == var:
            return value.strip().strip('"').strip("'")
    raise SystemExit(f"{var} not found in {env_file}")


async def one(
    c: httpx.AsyncClient, headers: dict[str, str], path: str, name: str, rng_name: str, region: str | None, prior: bool
) -> Result:
    t0 = time.perf_counter()
    try:
        code = (await c.get(path, headers=headers)).status_code
    except httpx.HTTPError:
        code = -1
    return ((time.perf_counter() - t0) * 1000, code, name, rng_name, region, prior)


async def scenario(
    c: httpx.AsyncClient, headers: dict[str, str], region: str | None, rng_name: str, cold: bool, rng: random.Random
) -> list[Result]:
    span, interval = RANGES[rng_name]
    end = scenario_end(datetime.now(NEM_TZ), cold, rng)
    jobs = [one(c, headers, build_path(k, m, region, end - span, end, interval), n, rng_name, region, False) for k, n, m in CALLS]
    jobs += [
        one(c, headers, build_path(k, m, region, end - 2 * span, end - span, interval), n, rng_name, region, True)
        for k, n, m in PRIOR_CALLS
    ]
    return list(await asyncio.gather(*jobs))


async def run(args: argparse.Namespace, key: str) -> tuple[list[Result], float]:
    headers = {"Authorization": f"Bearer {key}", "Accept-Encoding": "gzip"}
    rng = random.Random(args.seed)
    async with httpx.AsyncClient(base_url=args.base, timeout=120, http2=False) as c:
        rtts = []
        for _ in range(5):
            t0 = time.perf_counter()
            await c.get("/health")
            rtts.append((time.perf_counter() - t0) * 1000)
        scenarios = [(r, g) for r in REGIONS for g in RANGES]
        rng.shuffle(scenarios)
        results: list[Result] = []
        for r, g in scenarios * args.repeat:
            results += await scenario(c, headers, r, g, args.cold, rng)
            await asyncio.sleep(args.pause)
    return results, statistics.median(rtts)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    p.add_argument("--key-var", default="API_DEV_KEY", help="env var holding the bearer key (never printed)")
    p.add_argument("--repeat", type=int, default=2, help="passes over all region x range scenarios")
    p.add_argument("--cold", action="store_true", help="shift windows back and off the 5m grid (cache-cold)")
    p.add_argument("--label", default="run")
    p.add_argument("--pause", type=float, default=1.0, help="seconds between scenarios")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--out", type=Path, help="write raw per-call results json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    check_dev(args.base)
    key = read_env_key(args.env_file, args.key_var)
    results, rtt = asyncio.run(run(args, key))
    print(render_summary(args.label, results, rtt))
    if args.out:
        rows: list[dict[str, Any]] = [
            {"ms": round(ms, 1), "status": s, "metric": n, "range": g, "region": rg, "prior": pr}
            for ms, s, n, g, rg, pr in results
        ]
        args.out.write_text(json.dumps({"label": args.label, "base": args.base, "cold": args.cold, "rtt_ms": rtt, "calls": rows}))


if __name__ == "__main__":
    main()
