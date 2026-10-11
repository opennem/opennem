"""
Raw-body response cache decorator.

fastapi-cache's JsonCoder stores a type-wrapped JSON blob; on every HIT it json.loads it (object_hook parsing
datetimes), then FastAPI validates and re-serialises the whole payload. For the big timeseries bodies that is
30-60 ms of pure CPU per cache hit, which on a 1 vCPU box serialises all concurrent requests.

`cached_json` stores the finished JSON bytes (serialised exactly as FastAPI would for the return annotation) and
returns them as a raw Response on a HIT: no decode, no validation, no re-encode. The MISS path is unchanged
(handler result goes through normal FastAPI serialisation).
"""

import functools
import json
import logging
from collections.abc import Awaitable, Callable
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


def _make_coder(adapter: "TypeAdapter[Any] | None", exclude_none: bool) -> type[Coder]:
    class RawJsonCoder(Coder):
        # own cache: decode_as_type is overridden and Coder subclasses share the base one
        _type_field_cache: dict[Any, Any] = {}

        @classmethod
        def encode(cls, value: Any) -> bytes:
            if isinstance(value, JSONResponse):
                return bytes(value.body)
            if adapter is None:
                # what FastAPI + JSONResponse do when the route has no response_model field (plain dict payloads)
                # default= only fires for non-native values (datetime, Decimal, models): same output as jsonable_encoder
                # on the whole payload, without a second full walk of an already-plain dict
                return json.dumps(
                    value, default=jsonable_encoder, ensure_ascii=False, allow_nan=False, separators=(",", ":")
                ).encode("utf-8")
            return adapter.dump_json(value, by_alias=True, exclude_none=exclude_none)

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
    *, expire: int, key_builder: Callable[..., Any], return_type: Any | None = None, exclude_none: bool = False
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[Any]]]:
    """Drop-in for `@cache(expire, key_builder)` with a raw-bytes HIT path.

    return_type is the route's response_model (None for plain dict payloads, which FastAPI jsonable-encodes);
    exclude_none mirrors response_model_exclude_none. Together they make the stored bytes equal what FastAPI
    would have produced on a MISS.
    """

    def versioned_key_builder(*args: Any, **kwargs: Any) -> Any:
        # key_builder gets (func, namespace, ...): version the namespace so raw-bytes entries never collide with old ones
        if len(args) >= 2 and isinstance(args[1], str):
            args = (args[0], f"{args[1]}:{CACHE_FORMAT}", *args[2:])
        else:
            kwargs["namespace"] = f"{kwargs.get('namespace', '')}:{CACHE_FORMAT}"
        return key_builder(*args, **kwargs)

    coder = _make_coder(TypeAdapter(return_type) if return_type is not None else None, exclude_none)

    def wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[Any]]:
        inner = cache(expire=expire, key_builder=versioned_key_builder, coder=coder)(func)

        @functools.wraps(inner)
        async def outer(*args: P.args, **kwargs: P.kwargs) -> Any:
            result = await inner(*args, **kwargs)
            sub_response = kwargs.get(_INJECTED_RESPONSE)
            # a raw Response skips FastAPI's sub-response header merge: carry cache headers over by hand
            if isinstance(result, RawJsonResponse) and isinstance(sub_response, Response):
                for k, v in sub_response.headers.items():
                    if k.lower() not in _SKIP_HEADERS:
                        result.headers[k] = v
            return result

        return outer

    return wrapper
