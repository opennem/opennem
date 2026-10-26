"""Check authenticated responses are not served to keyless callers via Cloudflare or origin cache (#745, epic #747).

Read-only GETs. Per route: one keyed request (primes any cache), then N keyless requests. A leak = a keyless 2xx served
from cache (cf-cache-status HIT, or age header) after the keyed one; a keyless 2xx with no cache evidence passes with a note.
Routes carry a random cache-buster so each run starts cold. Key is read at runtime (never printed).
Exit code non-zero on any leak.

Usage (from repo root):
    PYTHONPATH=$PWD uv run --no-sync python bin/check_auth_leak.py
    PYTHONPATH=$PWD uv run --no-sync python bin/check_auth_leak.py --base https://api.openelectricity.org.au \
        --env-file /Users/n/Projects/Opennem/opennem/.env.production
"""

import argparse
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

DEFAULT_BASE = "https://api.oedev.org"
DEFAULT_ENV_FILE = Path("/Users/n/Projects/Opennem/opennem/.env")
SHOWN_HEADERS = ("cf-cache-status", "age", "cache-control")


@dataclass(frozen=True)
class Probe:
    status: int
    cf_cache_status: str | None
    age: str | None
    cache_control: str | None

    def show(self) -> str:
        return f"{self.status} cf-cache-status={self.cf_cache_status} age={self.age} cache-control={self.cache_control}"


def build_routes(nonce: int) -> list[str]:
    day = 10 + nonce % 9
    return [
        f"/v4/data/facilities/NEM?metrics=energy&interval=1d&date_start=2026-10-{day}T00:00:00&date_end=2026-10-22T00:00:00&facility_code=BAYSW",
        f"/v4/facilities/?cb={nonce}",
        f"/v4/facility/au/NEM/ADP?cb={nonce}",
    ]


def judge(keyed: Probe, keyless: list[Probe]) -> tuple[bool, str]:
    """-> (ok, reason). A keyed 2xx is required for the check to mean anything."""
    if not 200 <= keyed.status < 300:
        return False, f"inconclusive: keyed request got {keyed.status}"
    for i, k in enumerate(keyless, 1):
        if 200 <= k.status < 300:
            if (k.cf_cache_status or "").upper() == "HIT" or k.age:
                return False, f"keyless #{i} served 2xx from cache (cf-cache-status={k.cf_cache_status} age={k.age})"
    if any(200 <= k.status < 300 for k in keyless):
        return True, "keyless 2xx but not from cache (route may be public)"
    return True, "keyless rejected"


def read_env_key(env_file: Path, var: str) -> str:
    for line in env_file.read_text().splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == var:
            return value.strip().strip('"').strip("'")
    raise SystemExit(f"{var} not found in {env_file}")


def probe(client: httpx.Client, path: str, key: str | None) -> Probe:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    r = client.get(path, headers=headers)
    h = r.headers
    return Probe(r.status_code, h.get("cf-cache-status"), h.get("age"), h.get("cache-control"))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    p.add_argument("--key-var", default="API_DEV_KEY")
    p.add_argument("--keyless-requests", type=int, default=2)
    p.add_argument("--route", action="append", help="extra path to check (repeatable), e.g. /v4/me")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    key = read_env_key(args.env_file, args.key_var)
    routes = build_routes(random.randint(1000, 999999)) + (args.route or [])
    failed = 0
    with httpx.Client(base_url=args.base, timeout=60) as client:
        for path in routes:
            keyed = probe(client, path, key)
            keyless = [probe(client, path, None) for _ in range(args.keyless_requests)]
            ok, reason = judge(keyed, keyless)
            failed += not ok
            print(f"{'PASS' if ok else 'FAIL'} {path[:60]} -- {reason}")
            print(f"    keyed  : {keyed.show()}")
            for k in keyless:
                print(f"    keyless: {k.show()}")
    print(f"{len(routes) - failed}/{len(routes)} routes pass")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
