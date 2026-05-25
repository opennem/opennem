"""E2E surface sweep — runs a parameter matrix against the requested envs,
saves raw responses, and emits a comparison report for an agent to evaluate.

Usage:
    uv run python e2e/run.py                          # local vs prod (default)
    uv run python e2e/run.py --targets dev,prod       # remote dev vs prod
    uv run python e2e/run.py --targets local,dev,prod # all three; reports compare each pair
    uv run python e2e/run.py --filter market          # subset by test id
    uv run python e2e/run.py --concurrency 8          # parallel requests per env

The first target listed is treated as the "candidate" (what's being verified) and the
second as the "baseline". Comparison columns are labelled accordingly.

Outputs land in ./e2e/responses/<UTC iso>/ with one folder per env, plus report.{json,md}.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# env

REQUIRED_KEYS_BY_TARGET = {
    "local": ("OE_API_KEY_DEV", "OE_LOCAL_URL"),  # local server uses dev DB so uses dev key
    "dev": ("OE_API_KEY_DEV", "OE_DEV_URL"),
    "prod": ("OE_API_KEY_PROD", "OE_PROD_URL"),
}


def load_env(targets: list[str]) -> dict[str, str]:
    env: dict[str, str] = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    # OS env takes precedence
    needed: set[str] = set()
    for t in targets:
        if t not in REQUIRED_KEYS_BY_TARGET:
            sys.exit(f"Unknown target: {t!r}. Choices: {sorted(REQUIRED_KEYS_BY_TARGET)}")
        needed.update(REQUIRED_KEYS_BY_TARGET[t])
    for k in needed:
        if k in os.environ:
            env[k] = os.environ[k]
    missing = [k for k in needed if not env.get(k)]
    if missing:
        sys.exit(f"Missing env vars: {missing}. Copy e2e/.env.example -> e2e/.env and fill in.")
    return env


def target_creds(env: dict[str, str], target: str) -> tuple[str, str]:
    """Return (base_url, api_key) for the given target."""
    key_name, url_name = REQUIRED_KEYS_BY_TARGET[target]
    return env[url_name], env[key_name]


# ---------------------------------------------------------------------------
# test matrix

# A representative fixed window inside the dev plan's 367-day window.
# All UTC, naive iso strings (the API accepts these).
WINDOWS = {
    "1h": ("2026-04-22T14:00:00", "2026-04-22T15:00:00"),
    "1d": ("2026-04-22T00:00:00", "2026-04-23T00:00:00"),
    "7d": ("2026-04-15T00:00:00", "2026-04-22T00:00:00"),
    "1M": ("2026-03-22T00:00:00", "2026-04-22T00:00:00"),
}

# Larger windows for 5m we still want to inspect — but a full month at 5m is heavy. Stick to a day.
WINDOWS["5m"] = ("2026-04-22T00:00:00", "2026-04-22T03:00:00")  # 36 intervals

# Networks and a representative region per network.
NETWORKS = ["NEM", "WEM"]
REGIONS_BY_NETWORK = {"NEM": ["NSW1"], "WEM": ["WEM"]}

# Representative units per network for facility endpoint.
UNITS_BY_NETWORK = {
    "NEM": ["WAUBRAWF", "BAYSW1", "ERARING01"],
    "WEM": ["COLLIE_G2"],
}

DATA_METRICS = ["power", "energy", "emissions", "market_value", "storage_battery"]
MARKET_METRICS = [
    "price",
    "demand",
    "demand_energy",
    "demand_gross",
    "demand_gross_energy",
    "generation_renewable",
    "generation_renewable_energy",
    "generation_renewable_with_storage",
    "generation_renewable_with_storage_energy",
    "curtailment",
    "curtailment_energy",
    "curtailment_solar_utility",
    "curtailment_wind",
    "curtailment_solar_utility_energy",
    "curtailment_wind_energy",
    "flow_imports",
    "flow_exports",
    "flow_imports_energy",
    "flow_exports_energy",
    "renewable_proportion",
    "renewable_with_storage_proportion",
]

DATA_INTERVALS = ["5m", "1h", "1d", "7d", "1M"]
MARKET_INTERVALS = ["5m", "1h", "1d", "7d", "1M"]


@dataclass
class TestCase:
    id: str
    path: str  # e.g. "/data/network/NEM"
    params: dict[str, Any]
    tags: list[str] = field(default_factory=list)  # for filtering + reporting

    def to_query(self) -> str:
        # Flatten lists into repeated params (FastAPI accepts this)
        items: list[tuple[str, str]] = []
        for k, v in self.params.items():
            if isinstance(v, list):
                for vi in v:
                    items.append((k, str(vi)))
            elif v is None:
                continue
            else:
                items.append((k, str(v)))
        return urlencode(items)


def build_matrix() -> list[TestCase]:
    cases: list[TestCase] = []

    # ---- /v4/data/network/{nc} — sweep intervals, metric subsets, regions ----
    data_metric_subsets = [
        ["power"],
        ["energy"],
        ["emissions"],
        ["market_value"],
        ["power", "energy"],
        ["power", "energy", "emissions"],
        ["power", "energy", "emissions", "market_value"],
    ]
    for net in NETWORKS:
        for interval in DATA_INTERVALS:
            start, end = WINDOWS[interval]
            for metrics in data_metric_subsets:
                for region in [None, *REGIONS_BY_NETWORK[net]]:
                    region_tag = region or "all"
                    test_id = f"data-network-{net}-{interval}-{region_tag}-{'_'.join(metrics)}"
                    params: dict[str, Any] = {
                        "metrics": metrics,
                        "interval": interval,
                        "date_start": start,
                        "date_end": end,
                        "primary_grouping": "network_region" if region else "network",
                    }
                    if region:
                        params["network_region"] = region
                    cases.append(
                        TestCase(
                            id=test_id,
                            path=f"/data/network/{net}",
                            params=params,
                            tags=["data", net.lower(), interval, *metrics],
                        )
                    )

    # ---- /v4/data/facilities/{nc} — per unit ----
    facility_metric_subsets = [
        ["power"],
        ["energy"],
        ["power", "energy"],
        ["power", "energy", "emissions", "market_value"],
    ]
    for net in NETWORKS:
        units = UNITS_BY_NETWORK.get(net, [])
        for unit in units:
            for interval in DATA_INTERVALS:
                start, end = WINDOWS[interval]
                for metrics in facility_metric_subsets:
                    test_id = f"facility-{net}-{unit}-{interval}-{'_'.join(metrics)}"
                    cases.append(
                        TestCase(
                            id=test_id,
                            path=f"/data/facilities/{net}",
                            params={
                                "unit_code": unit,
                                "metrics": metrics,
                                "interval": interval,
                                "date_start": start,
                                "date_end": end,
                            },
                            tags=["facility", net.lower(), interval, unit, *metrics],
                        )
                    )

    # ---- /v4/market/network/{nc} — sweep with both safe and known-broken combos ----
    market_metric_subsets = [
        ["price"],
        ["demand"],
        ["demand_energy"],
        ["generation_renewable"],
        ["generation_renewable_energy"],
        ["curtailment"],
        ["curtailment_energy"],
        ["flow_imports"],
        ["flow_imports_energy"],
        ["renewable_proportion"],
        ["price", "demand"],
        ["price", "demand_energy"],
        ["demand", "generation_renewable", "renewable_proportion"],  # the #525 trigger combo
        ["demand_energy", "generation_renewable_energy"],  # safe
        ["price", "demand", "generation_renewable", "curtailment", "renewable_proportion"],
    ]
    for net in NETWORKS:
        for interval in MARKET_INTERVALS:
            start, end = WINDOWS[interval]
            for metrics in market_metric_subsets:
                for region in [None, *REGIONS_BY_NETWORK[net]]:
                    region_tag = region or "all"
                    test_id = f"market-{net}-{interval}-{region_tag}-{'_'.join(metrics)}"
                    params: dict[str, Any] = {
                        "metrics": metrics,
                        "interval": interval,
                        "date_start": start,
                        "date_end": end,
                        "primary_grouping": "network_region" if region else "network",
                    }
                    if region:
                        params["network_region"] = region
                    cases.append(
                        TestCase(
                            id=test_id,
                            path=f"/market/network/{net}",
                            params=params,
                            tags=["market", net.lower(), interval, *metrics],
                        )
                    )

    # ---- /v4/facilities — single list call, dev and prod should match ----
    cases.append(
        TestCase(
            id="facilities-NEM-operating",
            path="/facilities/",
            params={"status_id": "operating", "network_id": "NEM"},
            tags=["facilities", "nem"],
        )
    )

    return cases


# ---------------------------------------------------------------------------
# request runner


async def fetch_one(client: httpx.AsyncClient, base_url: str, api_key: str, case: TestCase) -> tuple[int, dict[str, Any] | str]:
    url = f"{base_url.rstrip('/')}{case.path}?{case.to_query()}"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = await client.get(url, headers=headers, timeout=60)
    except httpx.HTTPError as e:
        return -1, f"http-error: {e}"
    try:
        body = r.json()
    except Exception:
        body = r.text
    return r.status_code, body


async def run_env(
    base_url: str, api_key: str, cases: list[TestCase], out_dir: Path, concurrency: int
) -> dict[str, dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    results: dict[str, dict[str, Any]] = {}

    async def worker(case: TestCase, client: httpx.AsyncClient) -> None:
        async with sem:
            status, body = await fetch_one(client, base_url, api_key, case)
            results[case.id] = {"status": status, "body": body}
            (out_dir / f"{case.id}.json").write_text(
                json.dumps({"case": asdict(case), "status": status, "body": body}, indent=2, default=str)
            )

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(worker(c, client) for c in cases))
    return results


# ---------------------------------------------------------------------------
# comparison


def extract_values(body: Any) -> dict[str, list[tuple[str, float | None]]]:
    """Pull (timestamp, value) lists per metric from a successful TimeSeries response."""
    if not isinstance(body, dict) or not body.get("success"):
        return {}
    out: dict[str, list[tuple[str, float | None]]] = {}
    for series in body.get("data", []) or []:
        metric = series.get("metric")
        if not metric:
            continue
        # For grouped results we merge into one list per metric (tag each with the result name)
        for result in series.get("results", []) or []:
            name = result.get("name", "")
            for point in result.get("data", []) or []:
                if not isinstance(point, list) or len(point) != 2:
                    continue
                ts, v = point
                key = f"{metric}|{name}"
                out.setdefault(key, []).append((str(ts), v))
    return out


def summarize_values(values: dict[str, list[tuple[str, float | None]]]) -> dict[str, dict[str, Any]]:
    """Aggregate stats per series so we can compare across envs without dumping every row."""
    summary: dict[str, dict[str, Any]] = {}
    for key, points in values.items():
        nums = [v for _, v in points if isinstance(v, int | float)]
        nulls = sum(1 for _, v in points if v is None)
        summary[key] = {
            "n": len(points),
            "n_nulls": nulls,
            "min": min(nums) if nums else None,
            "max": max(nums) if nums else None,
            "sum": sum(nums) if nums else None,
            "avg": (sum(nums) / len(nums)) if nums else None,
            "first": points[0] if points else None,
            "last": points[-1] if points else None,
        }
    return summary


def classify_diff(
    case: TestCase,
    cand_label: str,
    base_label: str,
    cand_status: int,
    base_status: int,
    cand_summary: dict[str, dict[str, Any]],
    base_summary: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Tag each test result with a category for the agent to scan.

    cand_label / base_label are short names like 'local', 'dev', 'prod' — used in notes.
    """
    out_base = {
        f"{cand_label}_status": cand_status,
        f"{base_label}_status": base_status,
    }
    if cand_status != 200 and base_status != 200:
        return {"category": "both-error", **out_base}
    if cand_status != 200:
        return {"category": f"{cand_label}-only-error", **out_base}
    if base_status != 200:
        return {"category": f"{base_label}-only-error", **out_base}

    interval = next((t for t in case.tags if t in {"5m", "1h", "1d", "7d", "1M"}), "?")
    power_metric_names = {
        "power",
        "demand",
        "demand_gross",
        "generation_renewable",
        "generation_renewable_with_storage",
        "curtailment",
        "curtailment_solar_utility",
        "curtailment_wind",
        "flow_imports",
        "flow_exports",
    }

    keys = sorted(set(cand_summary) | set(base_summary))
    per_metric: list[dict[str, Any]] = []
    for k in keys:
        c = cand_summary.get(k, {})
        b = base_summary.get(k, {})
        c_sum = c.get("sum")
        b_sum = b.get("sum")
        ratio = (b_sum / c_sum) if (c_sum and b_sum and c_sum != 0) else None
        per_metric.append(
            {
                "metric": k,
                f"{cand_label}_n": c.get("n"),
                f"{base_label}_n": b.get("n"),
                f"{cand_label}_sum": c_sum,
                f"{base_label}_sum": b_sum,
                f"{cand_label}_avg": c.get("avg"),
                f"{base_label}_avg": b.get("avg"),
                f"ratio_{base_label}_over_{cand_label}_sum": ratio,
            }
        )

    # Tag the overall category
    category = "match"
    notes: list[str] = []
    intervals_per_bucket = {"5m": 1, "1h": 12, "1d": 288, "7d": 2016, "1M": 8640}.get(interval)
    for m in per_metric:
        c_sum = m[f"{cand_label}_sum"]
        b_sum = m[f"{base_label}_sum"]
        if c_sum is None and b_sum is None:
            continue
        if c_sum is None or b_sum is None:
            category = "missing-series"
            notes.append(f"{m['metric']}: only one env returned data")
            continue
        denom = max(abs(c_sum), abs(b_sum), 1e-9)
        rel_diff = abs(c_sum - b_sum) / denom
        if rel_diff < 0.005:
            continue
        metric_name = m["metric"].split("|")[0]
        if metric_name in power_metric_names and intervals_per_bucket and intervals_per_bucket > 1:
            ratio = m[f"ratio_{base_label}_over_{cand_label}_sum"]
            if ratio and abs(ratio - intervals_per_bucket) / intervals_per_bucket < 0.05:
                notes.append(
                    f"{m['metric']}: expected POWER-fix ratio {base_label}/{cand_label}≈{intervals_per_bucket} (got {ratio:.2f})"
                )
                category = "expected-power-fix" if category == "match" else category
                continue
        category = "unexpected-diff"
        notes.append(f"{m['metric']}: {cand_label}_sum={c_sum:.3f} {base_label}_sum={b_sum:.3f} rel_diff={rel_diff:.3%}")

    return {
        "category": category,
        "interval": interval,
        "intervals_per_bucket": intervals_per_bucket,
        **out_base,
        "per_metric": per_metric,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# report


def write_report(
    cases: list[TestCase],
    cand_label: str,
    base_label: str,
    cand: dict[str, dict[str, Any]],
    base: dict[str, dict[str, Any]],
    out: Path,
) -> None:
    rows: list[dict[str, Any]] = []
    for c in cases:
        rc = cand.get(c.id, {})
        rb = base.get(c.id, {})
        cs = summarize_values(extract_values(rc.get("body"))) if rc.get("status") == 200 else {}
        bs = summarize_values(extract_values(rb.get("body"))) if rb.get("status") == 200 else {}
        classification = classify_diff(
            c,
            cand_label,
            base_label,
            rc.get("status", -1),
            rb.get("status", -1),
            cs,
            bs,
        )
        rows.append({"id": c.id, "path": c.path, "tags": c.tags, "classification": classification})

    counts: dict[str, int] = {}
    for row in rows:
        cat = row["classification"]["category"]
        counts[cat] = counts.get(cat, 0) + 1

    (out / "report.json").write_text(
        json.dumps(
            {
                "candidate": cand_label,
                "baseline": base_label,
                "counts": counts,
                "rows": rows,
            },
            indent=2,
            default=str,
        )
    )

    md = [
        f"# E2E surface sweep — {cand_label} (candidate) vs {base_label} (baseline)",
        "",
        f"Total tests: {len(rows)}",
        "",
        "## Category counts",
    ]
    for cat in sorted(counts, key=lambda c: -counts[c]):
        md.append(f"- `{cat}`: {counts[cat]}")
    md.append("")

    section_order = [
        "unexpected-diff",
        f"{cand_label}-only-error",
        f"{base_label}-only-error",
        "both-error",
        "missing-series",
        "expected-power-fix",
        "match",
    ]
    for cat in section_order:
        subset = [r for r in rows if r["classification"]["category"] == cat]
        if not subset:
            continue
        md.append(f"## {cat} ({len(subset)})")
        md.append("")
        for row in subset[:60]:
            md.append(f"### `{row['id']}`")
            cls = row["classification"]
            md.append(f"- {cand_label}_status={cls[f'{cand_label}_status']}  {base_label}_status={cls[f'{base_label}_status']}")
            for note in cls.get("notes", []):
                md.append(f"  - {note}")
            md.append("")
        if len(subset) > 60:
            md.append(f"_…and {len(subset) - 60} more, see report.json_\n")

    (out / "report.md").write_text("\n".join(md))


# ---------------------------------------------------------------------------
# main


async def main_async(targets: list[str], filter_substr: str | None, concurrency: int) -> int:
    if len(targets) < 2:
        sys.exit("Need at least 2 targets to compare (e.g. --targets local,prod).")
    env = load_env(targets)
    cases = build_matrix()
    if filter_substr:
        cases = [c for c in cases if filter_substr in c.id]
    if not cases:
        sys.exit("No test cases after filter.")

    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "responses" / ts
    print(f"[{ts}] running {len(cases)} cases × {len(targets)} envs -> {out}")
    print(f"  targets: {targets}  (candidate={targets[0]}, baseline={targets[1]})")

    results: dict[str, dict[str, dict[str, Any]]] = {}
    coros = []
    for t in targets:
        base_url, api_key = target_creds(env, t)
        coros.append(run_env(base_url, api_key, cases, out / t, concurrency))
    fetched = await asyncio.gather(*coros)
    for t, r in zip(targets, fetched, strict=False):
        results[t] = r

    cand, base = targets[0], targets[1]
    write_report(cases, cand, base, results[cand], results[base], out)

    report = json.loads((out / "report.json").read_text())
    print("\nCategory counts:")
    for cat, n in sorted(report["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {cat}: {n}")
    print(f"\nReport: {out / 'report.md'}")
    print(f"JSON:   {out / 'report.json'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--targets",
        default="local,prod",
        help="comma-separated envs to fetch, e.g. local,prod or dev,prod (first is candidate)",
    )
    ap.add_argument("--filter", help="substring filter on test id")
    ap.add_argument("--concurrency", type=int, default=8)
    args = ap.parse_args()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    return asyncio.run(main_async(targets, args.filter, args.concurrency))


if __name__ == "__main__":
    raise SystemExit(main())
