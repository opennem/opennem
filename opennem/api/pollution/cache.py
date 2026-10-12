"""
Response-body cache for the pollution endpoint.

NPI data is annual and only changes on import, so the finished JSON body is cached (bytes) keyed on the
normalised query plus a data version. The handler never reads the user's plan (no tier date limits), so the key is
not fragmented by user. Any cache failure degrades to computing the response.
"""

import hashlib
import json
import logging
import time
from collections.abc import Iterable
from datetime import datetime

from fastapi_cache import FastAPICache

logger = logging.getLogger("opennem.api.pollution.cache")

POLLUTION_CACHE_TTL = 24 * 60 * 60
_VERSION_KEY = "pollution:version"
# InMemoryBackend treats expire=None as already expired, so the version key gets a long explicit TTL (entries live 24h)
_VERSION_TTL = 365 * 24 * 60 * 60
_WARN_INTERVAL_S = 60.0
_last_warn = 0.0


def _warn(msg: str, exc: Exception) -> None:
    """Warn at most once per interval so a Redis outage does not flood logs."""
    global _last_warn
    now = time.monotonic()
    if now - _last_warn >= _WARN_INTERVAL_S:
        _last_warn = now
        logger.warning("%s: %s: %s", msg, type(exc).__name__, exc)


def _full_key(suffix: str) -> str:
    return f"{FastAPICache.get_prefix()}:{suffix}"


def build_cache_key(
    facility_codes: Iterable[str] | None, pollutant_codes: Iterable[str], date_start: datetime | None, date_end: datetime | None
) -> str:
    """Order-insensitive key; only the year of the dates matters to the query."""
    payload = json.dumps(
        {
            "f": sorted(set(facility_codes)) if facility_codes else None,
            "p": sorted(set(pollutant_codes)),
            "s": date_start.year if date_start else None,
            "e": date_end.year if date_end else None,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


async def _get_version() -> str:
    raw = await FastAPICache.get_backend().get(_full_key(_VERSION_KEY))
    if raw is None:
        return "0"
    return raw.decode() if isinstance(raw, bytes) else str(raw)


async def bump_pollution_version() -> None:
    """Invalidate every cached body; call after an NPI import."""
    await FastAPICache.get_backend().set(_full_key(_VERSION_KEY), str(time.time_ns()).encode(), _VERSION_TTL)


async def cache_get(key: str) -> bytes | None:
    try:
        version = await _get_version()
        value = await FastAPICache.get_backend().get(_full_key(f"pollution:{version}:{key}"))
    except Exception as e:
        _warn("pollution cache read failed, computing", e)
        return None
    if value is None:
        return None
    return value if isinstance(value, bytes) else str(value).encode()


async def cache_set(key: str, body: bytes) -> None:
    try:
        version = await _get_version()
        await FastAPICache.get_backend().set(_full_key(f"pollution:{version}:{key}"), body, POLLUTION_CACHE_TTL)
    except Exception as e:
        _warn("pollution cache write failed", e)


async def bump_pollution_version_external() -> None:
    """Bump from a non-API process (importers/CLI): uses the API's Redis directly; never raises."""
    try:
        from redis import asyncio as aioredis

        from opennem import settings

        client = aioredis.from_url(str(settings.redis_url))
        try:
            await client.set(f"api-cache:{_VERSION_KEY}", str(time.time_ns()), ex=_VERSION_TTL)
        finally:
            await client.aclose()  # pyright: ignore[reportAttributeAccessIssue]
    except Exception as e:
        _warn("pollution cache version bump failed (entries expire within 24h)", e)
