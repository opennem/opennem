"""External dead-man check: is prod OpenNEM data fresh? Stdlib only.

Env: OE_API_KEY (required), SLACK_WEBHOOK_URL (optional; prints if unset),
STATE_FILE (default .freshness-state.json), API_BASE.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

API_BASE = "https://api.openelectricity.org.au"
THRESHOLD_MINUTES = 20
REALERT_MINUTES = 60
NETWORKS: dict[str, int] = {"NEM": 10, "WEM": 8}  # code -> UTC offset hours


@dataclass(frozen=True)
class Check:
    network: str
    lag_minutes: float | None  # None = unknown (api failure)
    latest: str | None
    error: str | None = None


def network_tz(network: str) -> timezone:
    return timezone(timedelta(hours=NETWORKS[network]))


def build_url(network: str, now: datetime, base: str = API_BASE) -> str:
    start = (now - timedelta(hours=3)).astimezone(network_tz(network)).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}/v4/data/network/{network}?metrics=power&interval=5m&date_start={start}"


def compute_lag_minutes(date_end: str, now: datetime, network: str) -> float:
    dt = datetime.fromisoformat(date_end)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=network_tz(network))
    return (now - dt).total_seconds() / 60


def is_stale(check: Check, threshold: int = THRESHOLD_MINUTES) -> bool:
    return check.lag_minutes is None or check.lag_minutes > threshold


def fetch_check(network: str, api_key: str, now: datetime, base: str = API_BASE) -> Check:
    req = urllib.request.Request(
        build_url(network, now, base),
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json", "User-Agent": "oe-data-freshness"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            if resp.status != 200:
                return Check(network, None, None, f"HTTP {resp.status}")
            body = json.load(resp)
        date_end = body["data"][0]["date_end"]
        return Check(network, compute_lag_minutes(date_end, now, network), date_end)
    except urllib.error.HTTPError as e:
        return Check(network, None, None, f"HTTP {e.code}")
    except Exception as e:  # noqa: BLE001 - any failure counts as stale-unknown
        return Check(network, None, None, f"{type(e).__name__}: {e}")


def describe(c: Check) -> str:
    if c.lag_minutes is None:
        return f"{c.network}: freshness unknown ({c.error})"
    return f"{c.network}: data is {c.lag_minutes:.0f} minutes stale (latest interval {c.latest})"


def decide(state: dict[str, dict[str, str]], checks: list[Check], now: datetime) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Return (slack messages, new state). state: {network: {since, last_alert}} for stale networks."""
    new_state: dict[str, dict[str, str]] = {}
    msgs: list[str] = []
    for c in checks:
        prev = state.get(c.network)
        if is_stale(c):
            if prev is None:
                new_state[c.network] = {"since": now.isoformat(), "last_alert": now.isoformat()}
                msgs.append(f":rotating_light: {describe(c)}")
            else:
                last = datetime.fromisoformat(prev["last_alert"])
                if now - last >= timedelta(minutes=REALERT_MINUTES):
                    new_state[c.network] = {**prev, "last_alert": now.isoformat()}
                    msgs.append(f":rotating_light: still stale: {describe(c)}")
                else:
                    new_state[c.network] = prev
        elif prev is not None:
            msgs.append(f":white_check_mark: {c.network} recovered: latest interval {c.latest} ({c.lag_minutes:.0f} min lag)")
    return msgs, new_state


def post_slack(url: str, text: str) -> None:
    req = urllib.request.Request(
        url, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    urllib.request.urlopen(req, timeout=15).read()  # noqa: S310


def load_state(path: Path) -> dict[str, dict[str, str]]:
    try:
        return json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return {}


def main() -> int:
    api_key = os.environ.get("OE_API_KEY", "")
    if not api_key:
        print("OE_API_KEY not set", file=sys.stderr)
        return 2
    base = os.environ.get("API_BASE", API_BASE)
    path = Path(os.environ.get("STATE_FILE", ".freshness-state.json"))
    now = datetime.now(UTC)
    checks = [fetch_check(n, api_key, now, base) for n in NETWORKS]
    for c in checks:
        print(describe(c))
    msgs, new_state = decide(load_state(path), checks, now)
    hook = os.environ.get("SLACK_WEBHOOK_URL", "")
    sent_all = True
    for m in msgs:
        print("ALERT:", m)
        if hook:
            try:
                post_slack(hook, m)
            except Exception as e:  # noqa: BLE001
                print(f"slack post failed: {e}", file=sys.stderr)
                sent_all = False
        else:
            print("SLACK_WEBHOOK_URL not set; not posting", file=sys.stderr)
            sent_all = False
    # only persist state if alerts delivered, so a failed post retries next run
    if sent_all:
        path.write_text(json.dumps(new_state))
    return 0 if sent_all else 1


if __name__ == "__main__":
    sys.exit(main())
