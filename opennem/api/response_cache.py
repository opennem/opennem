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
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any, ParamSpec, TypeVar

from fastapi import Response
from fastapi.encoders import jsonable_encoder
from fastapi_cache.coder import Coder
from fastapi_cache.decorator import cache
from pydantic import TypeAdapter
from starlette.responses import JSONResponse

logger = logging.getLogger("opennem.api.response_cache")

P = ParamSpec("P")
R = TypeVar("R")

# name fastapi-cache injects its response param under (injected_dependency_namespace="__fastapi_cache")
_INJECTED_RESPONSE = "__fastapi_cache_response"
# bump when the stored format changes: old entries (JsonCoder blobs, still in Redis across a deploy) are never read
CACHE_FORMAT = "rawjson-v2"
_SKIP_HEADERS = frozenset({"content-length", "content-type"})

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


class PreEncoded:
    """Handler result already serialised to the final JSON bytes (see `cached_json`)."""

    __slots__ = ("body",)

    def __init__(self, body: bytes) -> None:
        self.body = body


def _encode_value(value: Any, adapter: "TypeAdapter[Any] | None", exclude_none: bool) -> bytes:
    if isinstance(value, PreEncoded):
        return value.body
    if isinstance(value, JSONResponse):
        return bytes(value.body)
    if adapter is None:
        # what FastAPI + JSONResponse do when the route has no response_model field (plain dict payloads)
        # default= only fires for non-native values (datetime, Decimal, models): same output as jsonable_encoder
        # on the whole payload, without a second full walk of an already-plain dict
        return json.dumps(value, default=jsonable_encoder, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(
            "utf-8"
        )
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
    whichever TTL applied, so Cloudflare (which caches by URL) never holds a 60s-fresh body for 300s.
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

        @functools.wraps(inner)
        async def outer(*args: P.args, **kwargs: P.kwargs) -> Any:
            date_end = kwargs.get("date_end")
            use_live = live_expire is not None and is_live_edge_request(date_end if isinstance(date_end, datetime) else None)
            result = await (inner_live if use_live else inner)(*args, **kwargs)
            sub_response = kwargs.get(_INJECTED_RESPONSE)
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
