"""Compare API output between two environments (default dev vs prod) for identical requests (#745, epic #747).

Read-only GETs only. Windows end on the hour >= --lag-hours ago so live-edge timing does not matter.
Keys are read at runtime from each env file (never printed or written). Compares parsed json, ignoring `version` and `created_at`.
Classes: equal, value (numbers/strings differ), shape (keys/lengths/types differ), status (http status differs), both_err.
Exit code: non-zero on any shape or status diff (or transport error); value drift fails only with --strict.

Usage (from repo root):
    PYTHONPATH=$PWD uv run --no-sync python bin/compare_envs.py --windows short --limit 20
    PYTHONPATH=$PWD uv run --no-sync python bin/compare_envs.py --windows all --show 30
    PYTHONPATH=$PWD uv run --no-sync python bin/compare_envs.py --windows 7d/1h,90d/1d --strict
    PYTHONPATH=$PWD uv run --no-sync python bin/compare_envs.py --list   # print cases, no requests
"""

import argparse
import asyncio
import collections
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

NEM_TZ = timezone(timedelta(hours=10))
DEFAULT_A = ("dev", "https://api.oedev.org", Path("/Users/n/Projects/Opennem/opennem/.env"))
DEFAULT_B = ("prod", "https://api.openelectricity.org.au", Path("/Users/n/Projects/Opennem/opennem/.env.production"))
IGNORED_KEYS = ("version", "created_at")
REGIONS: list[str | None] = ["NSW1", "QLD1", "SA1", "TAS1", "VIC1", None]
DATA_SETS = [("power",), ("emissions", "power"), ("market_value",), ("emissions",), ("energy",)]
MARKET_SETS = [
    ("price",),
    ("demand",),
    ("generation_renewable", "demand_gross"),
    ("curtailment_solar_utility", "curtailment_wind"),
    ("renewable_proportion",),
    ("flow_imports", "flow_exports"),
    ("price", "demand"),
]
# label -> (interval, days)
WINDOWS: dict[str, tuple[str, int]] = {
    "1d/5m": ("5m", 1),
    "3d/5m": ("5m", 3),
    "7d/5m": ("5m", 7),
    "30d/30m": ("30m", 30),
    "7d/1h": ("1h", 7),
    "90d/1d": ("1d", 90),
    "365d/1d": ("1d", 365),
    "2y/1M": ("1M", 730),
    "90d/1w": ("1w", 90),
}
WINDOW_SETS: dict[str, list[str]] = {
    "short": ["1d/5m", "3d/5m", "7d/5m", "30d/30m"],
    "long": ["7d/1h", "90d/1d", "365d/1d", "2y/1M", "90d/1w"],
    "all": list(WINDOWS),
}


@dataclass(frozen=True)
class Case:
    kind: str
    label: str
    path: str


# ---- pure helpers ----


def resolve_windows(spec: str) -> list[str]:
    """`short|long|all` or a comma list of window labels (e.g. 7d/1h,90d/1d)."""
    if spec in WINDOW_SETS:
        return WINDOW_SETS[spec]
    names = [s.strip() for s in spec.split(",") if s.strip()]
    unknown = [n for n in names if n not in WINDOWS]
    if unknown:
        raise SystemExit(f"unknown windows {unknown}; known: {', '.join(WINDOWS)} or {', '.join(WINDOW_SETS)}")
    return names


def fmt(d: datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def build_cases(now: datetime, windows: list[str], lag_hours: int = 3) -> list[Case]:
    end = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=lag_hours)
    cases = []
    for region in REGIONS:
        for w in windows:
            interval, days = WINDOWS[w]
            start = end - timedelta(days=days)
            for kind, sets in (("data", DATA_SETS), ("market", MARKET_SETS)):
                for ms in sets:
                    q = "&".join(f"metrics={m}" for m in ms)
                    q += f"&interval={interval}&date_start={fmt(start)}&date_end={fmt(end)}"
                    if region:
                        q += f"&network_region={region}"
                    if kind == "data":
                        q += "&secondary_grouping=fueltech"
                    cases.append(Case(kind, f"{w}/{region}/{'+'.join(ms)}", f"/v4/{kind}/network/NEM?{q}"))
    return cases


def strip_ignored(obj: Any) -> Any:
    """Drop ignored top-level keys (version, created_at) from a response body."""
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k not in IGNORED_KEYS}
    return obj


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def diff_json(a: Any, b: Any, names: tuple[str, str], path: str = "", out: list[tuple[str, str]] | None = None, limit: int = 4,
              tol: float = 1e-9) -> list[tuple[str, str]]:  # fmt: skip
    """First `limit` differences as (class, message); class is `shape` or `value`. a is names[0], b is names[1]."""
    out = out if out is not None else []
    if len(out) >= limit:
        return out
    na, nb = names
    if type(a) is not type(b) and not (_is_num(a) and _is_num(b)):
        out.append(("shape", f"{path}: type {type(a).__name__} ({na}) vs {type(b).__name__} ({nb})"))
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(("shape", f"{path}.{k}: key only in {na if k in a else nb}"))
            else:
                diff_json(a[k], b[k], names, f"{path}.{k}", out, limit, tol)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(("shape", f"{path}: len {na}={len(a)} {nb}={len(b)}"))
        for i, (x, y) in enumerate(zip(a, b, strict=False)):
            diff_json(x, y, names, f"{path}[{i}]", out, limit, tol)
    elif _is_num(a):
        if abs(a - b) > tol * max(1, abs(a), abs(b)):
            out.append(("value", f"{path}: {na}={a} {nb}={b}"))
    elif a != b:
        out.append(("value", f"{path}: {na}={a!r} {nb}={b!r}"))
    return out[:limit]


def classify(status_a: int, status_b: int, body_a: Any, body_b: Any, names: tuple[str, str]) -> tuple[str, list[str]]:
    """-> (class, first diffs). class in equal|value|shape|status|both_err."""
    if status_a != status_b:
        return "status", [f"status {names[0]}={status_a} {names[1]}={status_b}"]
    if status_a != 200:
        return "both_err", []
    a, b = strip_ignored(body_a), strip_ignored(body_b)
    if a == b:
        return "equal", []
    diffs = diff_json(a, b, names)
    if not diffs:  # only float-tolerance level differences
        return "equal", []
    cls = "shape" if any(c == "shape" for c, _ in diffs) else "value"
    return cls, [m for _, m in diffs]


def exit_code(counts: dict[str, int], strict: bool) -> int:
    if counts.get("shape") or counts.get("status") or counts.get("error"):
        return 1
    if strict and counts.get("value"):
        return 1
    return 0


# ---- http ----


def read_env_key(env_file: Path, var: str) -> str:
    for line in env_file.read_text().splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == var:
            return value.strip().strip('"').strip("'")
    raise SystemExit(f"{var} not found in {env_file}")


async def run(args: argparse.Namespace, cases: list[Case]) -> tuple[dict[str, int], list[tuple[Case, str, list[str]]]]:
    na, nb = args.name_a, args.name_b
    key_a = read_env_key(args.env_a, args.key_var)
    key_b = read_env_key(args.env_b, args.key_var)
    sem = asyncio.Semaphore(args.concurrency)
    counts: dict[str, int] = collections.Counter()
    found: list[tuple[Case, str, list[str]]] = []

    async with httpx.AsyncClient(timeout=120) as c:

        async def one(case: Case) -> None:
            async with sem:
                try:
                    ra, rb = await asyncio.gather(
                        c.get(args.base_a + case.path, headers={"Authorization": f"Bearer {key_a}"}),
                        c.get(args.base_b + case.path, headers={"Authorization": f"Bearer {key_b}"}),
                    )
                except httpx.HTTPError as e:
                    counts["error"] += 1
                    found.append((case, "error", [type(e).__name__]))
                    return
            body_a = ra.json() if ra.status_code == 200 else None
            body_b = rb.json() if rb.status_code == 200 else None
            cls, diffs = classify(ra.status_code, rb.status_code, body_a, body_b, (na, nb))
            counts[cls] += 1
            if cls not in ("equal", "both_err"):
                found.append((case, cls, diffs))

        await asyncio.gather(*(one(x) for x in cases))
    return dict(counts), found


def render(counts: dict[str, int], found: list[tuple[Case, str, list[str]]], total: int, show: int) -> str:
    lines = [
        f"cases={total} "
        + " ".join(f"{k}={counts.get(k, 0)}" for k in ("equal", "value", "shape", "status", "both_err", "error"))
    ]
    by_window = collections.Counter("/".join(c.label.split("/")[:2]) for c, _, _ in found)
    by_metric = collections.Counter(c.label.split("/")[-1] for c, _, _ in found)
    if found:
        lines.append(f"non-equal by window: {dict(by_window)}")
        lines.append(f"non-equal by metrics: {dict(by_metric)}")
    # shape/status first: they fail the run
    order = {"status": 0, "shape": 1, "error": 2, "value": 3}
    for case, cls, diffs in sorted(found, key=lambda f: order.get(f[1], 9))[:show]:
        lines.append(f"[{cls}] {case.kind} {case.label}")
        lines += [f"    {d}" for d in diffs[:2]]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name-a", default=DEFAULT_A[0])
    p.add_argument("--base-a", default=DEFAULT_A[1])
    p.add_argument("--env-a", type=Path, default=DEFAULT_A[2])
    p.add_argument("--name-b", default=DEFAULT_B[0])
    p.add_argument("--base-b", default=DEFAULT_B[1])
    p.add_argument("--env-b", type=Path, default=DEFAULT_B[2])
    p.add_argument("--key-var", default="API_DEV_KEY", help="env var holding the bearer key in both env files (never printed)")
    p.add_argument("--windows", default="short", help=f"short|long|all or comma list of {','.join(WINDOWS)}")
    p.add_argument("--lag-hours", type=int, default=3, help="window end = top of the hour this many hours ago")
    p.add_argument("--limit", type=int, default=0, help="only the first N cases (0 = all)")
    p.add_argument("--concurrency", type=int, default=6)
    p.add_argument("--show", type=int, default=25, help="max non-equal cases to print")
    p.add_argument("--strict", action="store_true", help="value drift also fails the run")
    p.add_argument("--list", action="store_true", help="print cases and exit, no requests")
    p.add_argument("--out", type=Path, help="write non-equal cases json (paths and diffs only, no keys)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cases = build_cases(datetime.now(NEM_TZ), resolve_windows(args.windows), args.lag_hours)
    if args.limit:
        cases = cases[: args.limit]
    if args.list:
        for c in cases:
            print(c.kind, c.label)
        print(f"{len(cases)} cases")
        return
    counts, found = asyncio.run(run(args, cases))
    print(render(counts, found, len(cases), args.show))
    if args.out:
        args.out.write_text(
            json.dumps(
                [{"kind": c.kind, "label": c.label, "path": c.path, "class": k, "diffs": d} for c, k, d in found], indent=1
            )
        )
    sys.exit(exit_code(counts, args.strict))


if __name__ == "__main__":
    main()
