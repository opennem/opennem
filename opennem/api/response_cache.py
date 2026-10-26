"""
Raw-body response cache decorator.

fastapi-cache's JsonCoder stores a type-wrapped JSON blob; on every HIT it json.loads it (object_hook parsing
datetimes), then FastAPI validates and re-serialises the whole payload. For the big timeseries bodies that is
30-60 ms of pure CPU per cache hit, which on a 1 vCPU box serialises all concurrent requests.

`cached_json` stores the finished JSON bytes (serialised exactly as FastAPI would for the return annotation) and
returns them as a raw Response on a HIT: no decode, no validation, no re-encode. The MISS path serialises once in a
worker thread and returns the same bytes as a raw Response.
"""

import asyncio
import functools
import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any, ParamSpec, TypeVar

import orjson
from fastapi import Response
from fastapi.encoders import jsonable_encoder
from fastapi_cache.coder import Coder
from fastapi_cache.decorator import cache
from pydantic import TypeAdapter
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse

from opennem.api.cache_keys import grid_slot_end

logger = logging.getLogger("opennem.api.response_cache")

P = ParamSpec("P")
R = TypeVar("R")

# name fastapi-cache injects its response param under (injected_dependency_namespace="__fastapi_cache")
_INJECTED_RESPONSE = "__fastapi_cache_response"
# bump when the stored format changes: old entries (JsonCoder blobs, still in Redis across a deploy) are never read
CACHE_FORMAT = "rawjson-v2"
_INJECTED_REQUEST = "__fastapi_cache_request"
_SKIP_HEADERS = frozenset({"content-length", "content-type"})


def apply_cache_visibility(headers: MutableHeaders | dict[str, str], authorized: bool) -> None:
    """Mark a keyed response `private` (#751) so shared caches (Cloudflare caches by URL, ignoring Authorization)
    never serve it to a keyless client. Only the visibility directive changes: max-age is kept as set by
    fastapi-cache (live/slot TTL on a MISS, remaining ttl on a HIT). Anonymous responses and responses with no
    max-age cache-control (errors, no-store) are left untouched.
    """
    if not authorized:
        return
    cc = headers.get("cache-control")
    if cc is None or "max-age" not in cc.lower():
        return
    if not any(d.strip().lower() in ("private", "no-store") for d in cc.split(",")):
        headers["Cache-Control"] = f"private, {cc}"
    vary = headers.get("vary")
    if vary is None:
        headers["Vary"] = "Authorization"
    elif "authorization" not in vary.lower():
        headers["Vary"] = f"{vary}, Authorization"


def apply_request_cache_visibility(kwargs: Mapping[str, Any]) -> None:
    """Apply `apply_cache_visibility` to the injected sub-response; keyed when the request carried Authorization.

    Falls back to a non-None `user` kwarg when the request was not injected.
    """
    sub_response = kwargs.get(_INJECTED_RESPONSE)
    if not isinstance(sub_response, Response):
        return
    request = kwargs.get(_INJECTED_REQUEST)
    authorized = request.headers.get("authorization") is not None if request is not None else kwargs.get("user") is not None
    apply_cache_visibility(sub_response.headers, authorized)


def private_when_keyed[**Q, T](func: Callable[Q, Awaitable[T]]) -> Callable[Q, Awaitable[T]]:
    """For plain fastapi-cache `@cache` routes: place ABOVE `@cache`, below the router decorator."""

    @functools.wraps(func)
    async def wrapper(*args: Q.args, **kwargs: Q.kwargs) -> T:
        result = await func(*args, **kwargs)
        apply_request_cache_visibility(kwargs)
        return result

    return wrapper


# a request is "live" when its date_end is unset or within this window of now: new intervals land every 5 min,
# so those responses go stale far faster than a range that ended days ago (#726)
LIVE_WINDOW = timedelta(days=1)
# date_end is network-local naive time; NEM is a fixed +10:00 and WEM +8 is well inside LIVE_WINDOW slack
_NEM_TZ = timezone(timedelta(hours=10))


def is_live_edge_request(date_end: datetime | None, now: datetime | None = None) -> bool:
    """True when the response reaches the live edge: no date_end, or one within LIVE_WINDOW of now (or in the future)."""
    if date_end is None:
        return True
    now_local = (now or datetime.now(_NEM_TZ)).astimezone(_NEM_TZ).replace(tzinfo=None)
    if date_end.tzinfo is not None:
        date_end = date_end.astimezone(_NEM_TZ).replace(tzinfo=None)
    return date_end >= now_local - LIVE_WINDOW


# Grid-normalised sub-day windows (#729) key on the 5m slot they end in, so an entry is only ever read by requests
# of that slot. Live TTL for them = time left in the slot + slack, capped here: an entry written at 06:16:30 for
# slot 06:20 lives to ~06:20:30, not 60s, so the cache-warmer's refresh (right after the interval lands) serves
# the whole slot. A cold build before the interval landed is stale for at most the rest of its slot, and the
# warmer force-refreshes it; no setting gate needed because the TTL can never outlive the slot by more than slack.
SLOT_SECONDS = 300
SLOT_TTL_SLACK = 30
# warm-ahead (#752): an entry for the NEXT slot (slot_end 300-600 s away) is built before that slot starts and must
# live until the end of that slot + slack, so the cap covers a full extra slot
SLOT_TTL_CAP = 2 * SLOT_SECONDS + SLOT_TTL_SLACK
_TTL_BUCKET = 10  # round up so lazily built per-TTL cache wrappers stay few


def slot_live_ttl(slot_end: datetime, floor: int, now: datetime | None = None) -> int:
    """Live TTL for a request whose key slot ends at `slot_end` (naive NEM-local).

    Current slot (0-300 s left) and the next slot (300-600 s left, warm-ahead entries) get TTL = time left + slack, so
    expiry is always slot_end + slack (+ bucket rounding). `floor` for a past slot or anything further ahead.
    """
    now_local = (now or datetime.now(_NEM_TZ)).astimezone(_NEM_TZ).replace(tzinfo=None)
    remaining = (slot_end - now_local).total_seconds()
    if remaining < 0 or remaining > 2 * SLOT_SECONDS:
        return floor  # past slot or further ahead than the next one: keep the short TTL
    ttl = -(-int(remaining + SLOT_TTL_SLACK) // _TTL_BUCKET) * _TTL_BUCKET
    return max(floor, min(SLOT_TTL_CAP, ttl))


class PreEncoded:
    """Handler result already serialised to the final JSON bytes (see `cached_json`)."""

    __slots__ = ("body",)

    def __init__(self, body: bytes) -> None:
        self.body = body


def _encode_plain(value: Any) -> bytes:
    """Serialise a plain dict payload the way FastAPI + JSONResponse would (compact, utf-8, no ASCII escaping).

    orjson handles native types (str/int/float/bool/None, datetime incl. tz offset + microseconds, enum, uuid,
    dataclass); `jsonable_encoder` is only the `default` for the rest (Decimal, pydantic models, sets...), so the
    hook no longer fires per datetime. Differences from stdlib json: NaN/inf serialise as null instead of raising
    (stdlib path used allow_nan=False and 500'd); anything orjson rejects (non-str dict keys, ints over 64 bit,
    unsupported types after the hook) falls back to the stdlib encoder, so output stays equal.
    """
    try:
        return orjson.dumps(value, default=jsonable_encoder)
    except (TypeError, orjson.JSONEncodeError):
        return json.dumps(value, default=jsonable_encoder, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(
            "utf-8"
        )


def _encode_value(value: Any, adapter: "TypeAdapter[Any] | None", exclude_none: bool) -> bytes:
    if isinstance(value, PreEncoded):
        return value.body
    if isinstance(value, JSONResponse):
        return bytes(value.body)
    if adapter is None:
        return _encode_plain(value)
    return adapter.dump_json(value, by_alias=True, exclude_none=exclude_none)


def _make_coder(adapter: "TypeAdapter[Any] | None", exclude_none: bool) -> type[Coder]:
    class RawJsonCoder(Coder):
        # own cache: decode_as_type is overridden and Coder subclasses share the base one
        _type_field_cache: dict[Any, Any] = {}

        @classmethod
        def encode(cls, value: Any) -> bytes:
            return _encode_value(value, adapter, exclude_none)

        @classmethod
        def decode(cls, value: bytes) -> Any:
            return value

        @classmethod
        def decode_as_type(cls, value: bytes, *, type_: Any) -> Any:
            return RawJsonResponse(content=value)

    return RawJsonCoder


class RawJsonResponse(Response):
    media_type = "application/json"


def cached_json(
    *,
    expire: int,
    key_builder: Callable[..., Any],
    return_type: Any | None = None,
    exclude_none: bool = False,
    live_expire: int | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[Any]]]:
    """Drop-in for `@cache(expire, key_builder)` with a raw-bytes HIT path.

    return_type is the route's response_model (None for plain dict payloads, which FastAPI jsonable-encodes);
    exclude_none mirrors response_model_exclude_none. Together they make the stored bytes equal what FastAPI
    would have produced on a MISS.

    live_expire: shorter TTL for live-edge requests (date_end kwarg unset or within LIVE_WINDOW of now), see
    `is_live_edge_request`. Both TTLs share one key space (same key, tier included): a key's date_end only ever moves
    from live to historical, so a stale long entry can't be served to a live request. Cache-Control max-age follows
    whichever TTL applied, so Cloudflare (which caches by URL) never holds a 60s-fresh body for 300s. Grid-normalised
    sub-day windows get the longer slot-bounded TTL from `slot_live_ttl` (max-age follows it the same way).
    """

    def versioned_key_builder(*args: Any, **kwargs: Any) -> Any:
        # key_builder gets (func, namespace, ...): version the namespace so raw-bytes entries never collide with old ones
        if len(args) >= 2 and isinstance(args[1], str):
            args = (args[0], f"{args[1]}:{CACHE_FORMAT}", *args[2:])
        else:
            kwargs["namespace"] = f"{kwargs.get('namespace', '')}:{CACHE_FORMAT}"
        return key_builder(*args, **kwargs)

    adapter = TypeAdapter(return_type) if return_type is not None else None
    coder = _make_coder(adapter, exclude_none)

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[Any]]:
        @functools.wraps(func)
        async def encoded(*args: P.args, **kwargs: P.kwargs) -> Any:
            # serialise ONCE, off the event loop: fastapi-cache would encode for the store and FastAPI would then walk
            # the same payload again with jsonable_encoder (about 2x the CPU on big timeseries bodies)
            result = await func(*args, **kwargs)
            if isinstance(result, Response):
                return result
            return PreEncoded(await asyncio.to_thread(_encode_value, result, adapter, exclude_none))

        inner = cache(expire=expire, key_builder=versioned_key_builder, coder=coder)(encoded)
        inner_live = (
            cache(expire=live_expire, key_builder=versioned_key_builder, coder=coder)(encoded)
            if live_expire is not None
            else inner
        )

        slot_variants: dict[int, Callable[..., Awaitable[Any]]] = {}

        def slot_variant(ttl: int) -> Callable[..., Awaitable[Any]]:
            if ttl not in slot_variants:
                slot_variants[ttl] = cache(expire=ttl, key_builder=versioned_key_builder, coder=coder)(encoded)
            return slot_variants[ttl]

        @functools.wraps(inner)
        async def outer(*args: P.args, **kwargs: P.kwargs) -> Any:
            date_end = kwargs.get("date_end")
            use_live = live_expire is not None and is_live_edge_request(date_end if isinstance(date_end, datetime) else None)
            chosen = inner_live if use_live else inner
            if use_live and live_expire is not None and (slot_end := grid_slot_end(kwargs)) is not None:
                ttl = slot_live_ttl(slot_end, live_expire)
                if ttl != live_expire:
                    chosen = slot_variant(ttl)
            result = await chosen(*args, **kwargs)
            sub_response = kwargs.get(_INJECTED_RESPONSE)
            apply_request_cache_visibility(kwargs)  # miss + hit + 304 (sub_response is returned as is)
            if isinstance(result, PreEncoded):  # MISS: hand FastAPI the finished bytes, no second serialisation
                result = RawJsonResponse(content=result.body)
            # a raw Response skips FastAPI's sub-response header merge: carry cache headers over by hand
            if isinstance(result, RawJsonResponse) and isinstance(sub_response, Response):
                for k, v in sub_response.headers.items():
                    if k.lower() not in _SKIP_HEADERS:
                        result.headers[k] = v
            return result

        return outer

    return wrapper
