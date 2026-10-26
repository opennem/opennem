"""
Shared response-cache key builder for API endpoints.

The fastapi-cache default builder hashes every kwarg, including the ClickHouse client and the
`user` repr (rate-limit / meta change per request), so keys were per-user, per-process and
per-request. This builder drops both and keys on the plan tier instead: date-range limits are
validated inside the handlers per tier, so tiers must never share an entry.
"""

import hashlib
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from opennem.api.forecast import FORECAST_METRICS
from opennem.core.time_interval import Interval
from opennem.users.schema import OpenNEMUser

# kwargs that never influence the response body
_EXCLUDED_KWARGS = frozenset({"client", "user"})


def user_tier(user: OpenNEMUser | None) -> str:
    """Cache-relevant identity of a user: plan tier and admin flag only."""
    if user is None:
        return "anon"
    return f"{user.plan.value if hasattr(user.plan, 'value') else user.plan}:{'admin' if user.is_admin else 'user'}"


# Sub-day buckets read raw 5m rows filtered `interval >= date_start AND interval < date_end`, then
# aggregate per bucket (edge buckets are partial, not floored). So the rows returned depend only on
# which 5m grid points fall in [start, end): ceil both to the 5m grid. Day+ intervals use a daily
# view split that depends on exact times, so they stay on exact keys.
_NORMALISED_INTERVALS = frozenset({Interval.INTERVAL, Interval.HALF_HOUR, Interval.HOUR})
_GRID = timedelta(minutes=5)


def _ceil_5m(dt: datetime) -> datetime:
    floored = dt.replace(minute=dt.minute - dt.minute % 5, second=0, microsecond=0)
    return floored if floored == dt else floored + _GRID


def grid_slot_end(kwargs: dict[str, Any]) -> datetime | None:
    """5m-grid end the key normalises date_end to, or None when the window is keyed exactly (see below)."""
    start, end = kwargs.get("date_start"), kwargs.get("date_end")
    interval = kwargs.get("interval", Interval.INTERVAL)
    if not (isinstance(start, datetime) and isinstance(end, datetime)):
        # end None = live (capped to settled interval); start None derives from raw end: keep exact
        return None
    if start.tzinfo is not None or end.tzinfo is not None:
        return None  # rejected by validation; keep exact
    if interval not in _NORMALISED_INTERVALS:
        return None
    if any(m in FORECAST_METRICS for m in kwargs.get("metrics") or []):
        return None  # forecast table has its own date semantics
    return _ceil_5m(end)


def _normalise_window(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Key-only: collapse date_start/date_end to the 5m grid they select; else return kwargs unchanged."""
    slot_end = grid_slot_end(kwargs)
    if slot_end is None:
        return kwargs
    start, end = kwargs["date_start"], kwargs["date_end"]
    # validate_date_range checks `(end - start).days` against the plan limit on the raw values
    return {**kwargs, "date_start": _ceil_5m(start), "date_end": slot_end, "_range_days": (end - start).days}


def tiered_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Request | None = None,
    response: Response | None = None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """Key on endpoint + request params + user tier; ignore client and per-request user state."""
    params = sorted((k, repr(v)) for k, v in _normalise_window(kwargs).items() if k not in _EXCLUDED_KWARGS)
    tier = user_tier(kwargs.get("user"))
    raw = f"{func.__module__}:{func.__name__}:{args}:{params}:{tier}"
    return f"{namespace}:{hashlib.md5(raw.encode()).hexdigest()}"  # noqa: S324
