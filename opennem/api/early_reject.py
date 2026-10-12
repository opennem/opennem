"""Pure ASGI early rejection: dead v3 stats routes (#649) and unknown facility/unit codes (#646).

Runs before routing, auth (Unkey/Clerk), dependencies and ClickHouse, so rejected requests cost no outbound calls.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from urllib.parse import parse_qsl

from starlette.types import ASGIApp, Receive, Scope, Send

from opennem.api.known_codes import has_unknown_codes
from opennem.api.security import is_key_known_valid
from opennem.schema.opennem import OpennemErrorSchema

logger = logging.getLogger("opennem.api.early_reject")

_STATS_PREFIXES = ("/stats/", "/v3/stats/", "/v4/stats/")
# the only live stats routes: v4 ClickHouse backed station stats (v3 variants of these are dead)
_LIVE_STATS_PREFIXES = ("power/station/", "energy/station/")
_FACILITY_DATA_PATHS = ("/v4/data/facilities/", "/data/facilities/")

_GONE_BODY = (
    OpennemErrorSchema(error="Endpoint removed. Use the v4 API: https://docs.openelectricity.org.au", success=False)
    .model_dump_json()
    .encode()
)


def is_dead_stats_path(path: str) -> bool:
    """True for anything under the legacy /stats tree that is not a live v4 station route."""
    for prefix in _STATS_PREFIXES:
        if path.startswith(prefix):
            return prefix == "/v3/stats/" or not path[len(prefix) :].startswith(_LIVE_STATS_PREFIXES)
        if path == prefix[:-1]:
            return True
    return False


def _is_facility_data_path(path: str) -> bool:
    for prefix in _FACILITY_DATA_PATHS:
        if path.startswith(prefix):
            return "/" not in path[len(prefix) :].rstrip("/")
    return False


def _tz_aware(value: str) -> bool:
    """True only when the value parses as ISO and carries a tz. Anything unparseable passes through to normal validation."""
    try:
        return datetime.fromisoformat(value).tzinfo is not None
    except ValueError:
        return False


def _bearer_key(scope: Scope) -> str | None:
    for name, value in scope["headers"]:
        if name == b"authorization":
            scheme, _, token = value.decode("latin-1").partition(" ")
            return token.strip() if scheme.lower() == "bearer" and token.strip() else None
    return None


def _caller_is_known_valid(scope: Scope) -> bool:
    key = _bearer_key(scope)
    return key is not None and is_key_known_valid(key)


def facility_request_rejection(
    query_string: bytes, caller_is_known_valid: Callable[[], bool] = lambda: True
) -> tuple[int, str] | None:
    """Cheap pre-auth checks for /data/facilities. Returns (status, detail) matching the in-route errors, or None.

    The unknown-code 404 reveals which codes exist, so it is only served to callers whose key is already validated
    (in-memory user cache, no Unkey/Clerk call). Everyone else falls through to normal auth.
    """
    if not query_string:
        return None

    facility_code: list[str] = []
    unit_code: list[str] = []
    dates: dict[str, str] = {}  # FastAPI uses the last value of a repeated scalar param
    for key, value in parse_qsl(query_string.decode("latin-1")):
        if key == "facility_code":
            facility_code.append(value)
        elif key == "unit_code":
            unit_code.append(value)
        elif key in ("date_start", "date_end"):
            dates[key] = value

    if (value := dates.get("date_start")) and _tz_aware(value):
        return 400, "Date start must be timezone naive and in network time"
    if (value := dates.get("date_end")) and _tz_aware(value):
        return 400, "Date end must be timezone naive and in network time"

    if (facility_code or unit_code) and has_unknown_codes(facility_code, unit_code) and caller_is_known_valid():
        filter_desc = f"facility={facility_code}" if facility_code else ""
        if unit_code:
            filter_desc += f"{', ' if filter_desc else ''}unit={unit_code}"
        return 404, f"No data available for {filter_desc} in the specified time range"

    return None


async def _send_json(send: Send, status_code: int, body: bytes, cache_seconds: int | None = None) -> None:
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
    if cache_seconds:
        headers.append((b"cache-control", f"public, max-age={cache_seconds}".encode()))
    await send({"type": "http.response.start", "status": status_code, "headers": headers})
    await send({"type": "http.response.body", "body": body})


class EarlyRejectMiddleware:
    """Short circuit requests that can only fail, before any auth or I/O."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] != "OPTIONS":
            path: str = scope["path"]

            if is_dead_stats_path(path):
                await _send_json(send, 410, _GONE_BODY, cache_seconds=3600)
                return

            if _is_facility_data_path(path) and (
                rejection := facility_request_rejection(scope.get("query_string", b""), lambda: _caller_is_known_valid(scope))
            ):
                status_code, detail = rejection
                await _send_json(send, status_code, OpennemErrorSchema(error=detail, success=False).model_dump_json().encode())
                return

        await self.app(scope, receive, send)
