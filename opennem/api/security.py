"""
OpenNEM API Security Module

Handles API key validation (Unkey) and user enrichment (Clerk).
Plan resolution: Clerk privateMetadata.plan → OpenNEMPlan enum.
Admin resolution: Clerk privateMetadata.role == "admin".
"""

import asyncio
import hashlib
import hmac
import logging
import time
from typing import Annotated

from cachetools import TTLCache
from clerk_backend_api import Clerk
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from opennem import settings
from opennem.clients.unkey import UnkeyInvalidUserException, UnkeyUnavailableException, unkey_validate
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

logger = logging.getLogger("opennem.api.security")

# Initialize clients
if not settings.unkey_root_key or not settings.clerk_secret_key:
    raise ValueError("No API key or clerk secret key set")

clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)

# Bearer token scheme
api_token_scheme = HTTPBearer()
# Optional bearer scheme: does not 401 on a missing credential so anonymous
# requests can be served (at COMMUNITY limits) by optional-auth endpoints.
api_token_scheme_optional = HTTPBearer(auto_error=False)

# Enriched-user cache (post Unkey + Clerk). Entries are fresh for USER_CACHE_TTL_S; if Unkey/Clerk
# fail, an entry up to USER_CACHE_MAX_STALE_S past that is served instead (stale-if-error).
USER_CACHE_TTL_S = 5 * 60
USER_CACHE_MAX_STALE_S = 5 * 60
NEGATIVE_CACHE_TTL_S = 30
CLERK_TIMEOUT_MS = 3000


def _now() -> float:
    return time.monotonic()


_user_cache: TTLCache[str, tuple[OpenNEMUser, float]] = TTLCache(
    maxsize=10000, ttl=USER_CACHE_TTL_S + USER_CACHE_MAX_STALE_S, timer=lambda: _now()
)
_invalid_key_cache: TTLCache[str, bool] = TTLCache(maxsize=10000, ttl=NEGATIVE_CACHE_TTL_S, timer=lambda: _now())
_inflight: dict[str, asyncio.Task[OpenNEMUser]] = {}
# one stale-while-revalidate refresh per key; the dict also holds the strong ref so tasks aren't GC'd
_background_refreshes: dict[str, asyncio.Task[None]] = {}

# Default internal user for development
_OPENNEM_INTERNAL_USER = OpenNEMUser(
    id="dev",
    owner_id="dev",
    plan=OpenNEMPlan.ENTERPRISE,
    roles=[OpenNEMRoles.admin, OpenNEMRoles.anonymous],
)


def _resolve_plan(private_metadata: dict | None, unkey_meta: dict | None = None) -> OpenNEMPlan:
    """Resolve plan from Clerk privateMetadata, falling back to Unkey key meta, then COMMUNITY."""
    # Try Clerk first
    if private_metadata:
        raw = private_metadata.get("plan")
        if raw:
            try:
                return OpenNEMPlan(raw)
            except ValueError:
                # Legacy "BASIC" → COMMUNITY
                if raw == "BASIC":
                    return OpenNEMPlan.COMMUNITY
                logger.warning(f"Unknown plan code from Clerk: {raw}, defaulting to COMMUNITY")

    # Fallback to Unkey key metadata
    if unkey_meta and "plan" in unkey_meta:
        try:
            return OpenNEMPlan(unkey_meta["plan"])
        except ValueError:
            pass

    return OpenNEMPlan.COMMUNITY


def _resolve_admin(private_metadata: dict | None) -> bool:
    """Check if user has admin role in Clerk privateMetadata."""
    if private_metadata:
        return private_metadata.get("role") == "admin"
    return False


def _cache_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def key_fingerprint(key: str) -> str:
    """Short non-reversible id for logging a key (never log the key or any prefix of it)."""
    return _cache_key(key)[:8]


async def _fetch_user(key: str) -> OpenNEMUser:
    """Unkey verify + Clerk enrichment (no caching).

    Raises UnkeyInvalidUserException only when Unkey says the key is invalid; any other
    exception (timeouts, transport, Clerk errors) is an upstream failure.
    """
    user = await unkey_validate(api_key=key)

    if not user:
        raise UnkeyInvalidUserException("Invalid API key")

    # Enrich with Clerk user data
    if not user.owner_id:
        logger.info(f"No owner_id for user {user.id}, skipping Clerk enrichment")
        # Resolve plan from unkey meta if available
        user.plan = _resolve_plan(None, user.unkey_meta)
        return user

    clerk_user = await clerk_client.users.get_async(user_id=user.owner_id, timeout_ms=CLERK_TIMEOUT_MS)

    if not clerk_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user.full_name = f"{clerk_user.first_name} {clerk_user.last_name}"
    user.email = clerk_user.email_addresses[0].email_address

    private_meta = clerk_user.private_metadata if clerk_user.private_metadata else None

    # Resolve plan from Clerk, with Unkey meta fallback
    user.plan = _resolve_plan(private_meta, user.unkey_meta)

    # Resolve admin from Clerk privateMetadata.role
    if _resolve_admin(private_meta):
        if OpenNEMRoles.admin not in user.roles:
            user.roles.append(OpenNEMRoles.admin)

    return user


def _swallow_task_exception(task: "asyncio.Task[OpenNEMUser]") -> None:
    if not task.cancelled():
        task.exception()


async def _fetch_user_single_flight(key: str, ckey: str) -> OpenNEMUser:
    """One upstream fetch per key at a time; concurrent callers share the result.

    The fetch runs in its own task so a cancelled first caller doesn't fail the others.
    """
    task = _inflight.get(ckey)

    if task is None:
        task = asyncio.create_task(_fetch_user(key))
        task.add_done_callback(_swallow_task_exception)
        task.add_done_callback(lambda _t: _inflight.pop(ckey, None))
        _inflight[ckey] = task

    return await asyncio.shield(task)


def _store_user(ckey: str, user: OpenNEMUser) -> None:
    _user_cache[ckey] = (user.model_copy(deep=True), _now())


def _reject_invalid(ckey: str) -> None:
    """Unkey answered: key is invalid. Drop any cached user and remember the rejection."""
    _user_cache.pop(ckey, None)
    _invalid_key_cache[ckey] = True


async def _refresh_in_background(key: str, ckey: str) -> None:
    """SWR refresh: shares the single-flight fetch; failure keeps serving the stale entry."""
    try:
        user = await _fetch_user_single_flight(key, ckey)
    except UnkeyUnavailableException as e:  # subclass of Invalid: must come first, an outage never evicts
        logger.warning(f"Background auth refresh failed for key {key_fingerprint(key)}: {e}; serving stale")
    except UnkeyInvalidUserException:
        _reject_invalid(ckey)
    except asyncio.CancelledError:
        raise
    except HTTPException as e:
        # Clerk user gone / similar definitive rejection is not an outage: keep behaviour of the blocking path (no evict)
        logger.warning(f"Background auth refresh failed for key {key_fingerprint(key)}: {e.detail}; serving stale")
    except Exception as e:
        logger.warning(f"Background auth refresh failed for key {key_fingerprint(key)}: {e}; serving stale")
    else:
        _store_user(ckey, user)


def _schedule_background_refresh(key: str, ckey: str) -> None:
    """Start at most one background refresh per key (per running loop)."""
    loop = asyncio.get_running_loop()
    existing = _background_refreshes.get(ckey)
    if existing is not None and not existing.done() and existing.get_loop() is loop:
        return

    task = asyncio.create_task(_refresh_in_background(key, ckey))
    _background_refreshes[ckey] = task

    def _done(t: "asyncio.Task[None]") -> None:
        if _background_refreshes.get(ckey) is t:
            _background_refreshes.pop(ckey, None)

    task.add_done_callback(_done)


async def cancel_background_refreshes() -> None:
    """Cancel in-flight SWR refreshes (app shutdown / test teardown)."""
    tasks = list(_background_refreshes.values())
    _background_refreshes.clear()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def is_key_known_valid(key: str) -> bool:
    """True when the key is a bypass key or sits in the user cache within USER_CACHE_TTL_S (in-memory only).

    A stale-but-servable (SWR) entry is deliberately NOT known-valid: the caller falls through
    to normal auth, which serves it and refreshes.
    """
    if _is_bypass_key(key):
        return True
    cached = _user_cache.get(_cache_key(key))
    return cached is not None and _now() - cached[1] < USER_CACHE_TTL_S


async def _resolve_user_from_key(key: str, *, fresh: bool = False) -> OpenNEMUser:
    """Resolve an OpenNEMUser from a raw API key.

    Always raises HTTPException(401) on failure — invalid/short key, unknown key,
    missing Clerk user, or an unexpected Unkey/Clerk error. Callers (required and
    optional auth) share these semantics, so the error handling lives here only.

    The enriched user is cached per key (5 min), concurrent misses share one upstream
    call. Past the TTL (up to 5 min) the cached user is served immediately while one background
    refresh runs (stale-while-revalidate; invalid-key evicts); beyond that, callers block, and on an
    upstream error a cached user within the stale window is still served.
    ``fresh=True`` skips the fresh-cache read (always Unkey + Clerk, still single-flight and
    stale-if-error) and refreshes the cache entry with the result.
    """
    try:
        if not key or len(key) < 10:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        # Dev/internal key bypass → enterprise admin, full access, no Unkey/Clerk.
        # api_dev_key is per-environment; api_internal_key is the shared internal key
        # recognised across every environment (dev + prod). Return a copy so the
        # shared module-level singleton can never be mutated across requests.
        if key == settings.api_dev_key or (settings.api_internal_key and key == settings.api_internal_key):
            return _OPENNEM_INTERNAL_USER.model_copy(deep=True)

        ckey = _cache_key(key)

        if ckey in _invalid_key_cache:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        # copies out: callers mutate the returned user, never the cached one
        cached = _user_cache.get(ckey)
        if cached is not None:
            cached_user, stored_at = cached
            age = _now() - stored_at
            if not fresh and age < USER_CACHE_TTL_S:
                return cached_user.model_copy(deep=True)
            if not fresh and age < USER_CACHE_TTL_S + USER_CACHE_MAX_STALE_S:
                # stale-while-revalidate: serve now, refresh once in the background
                _schedule_background_refresh(key, ckey)
                return cached_user.model_copy(deep=True)

        try:
            user = await _fetch_user_single_flight(key, ckey)
        except HTTPException:
            raise
        except UnkeyUnavailableException as e:
            return _serve_stale_or_raise(ckey, cached, e)
        except UnkeyInvalidUserException as e:
            _reject_invalid(ckey)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key") from e
        except Exception as e:
            return _serve_stale_or_raise(ckey, cached, e)

        _store_user(ckey, user)
        return user.model_copy(deep=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from e


def _serve_stale_or_raise(ckey: str, cached: tuple[OpenNEMUser, float] | None, error: Exception) -> OpenNEMUser:
    """Upstream failed (never negative-cached): serve a cached user up to USER_CACHE_MAX_STALE_S stale."""
    if cached is not None:
        cached_user, stored_at = cached
        stale_s = _now() - stored_at - USER_CACHE_TTL_S
        if stale_s < USER_CACHE_MAX_STALE_S:
            logger.warning(f"Serving stale cached user {cached_user.id} ({stale_s:.0f}s past ttl) after upstream error: {error}")
            return cached_user.model_copy(deep=True)

    logger.warning(f"Authentication error: {error}")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from error


async def get_current_user(
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(api_token_scheme)],
) -> OpenNEMUser:
    """FastAPI dependency: validate API key, resolve plan + roles from Clerk."""
    return await _resolve_user_from_key(authorization.credentials)


async def get_current_user_fresh(
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(api_token_scheme)],
) -> OpenNEMUser:
    """Like get_current_user but never reads the fresh-user cache (e.g. /v4/me shows live plan/role)."""
    return await _resolve_user_from_key(authorization.credentials, fresh=True)


async def get_optional_user(
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(api_token_scheme_optional)],
) -> OpenNEMUser | None:
    """FastAPI dependency for optional auth.

    Returns ``None`` for anonymous requests (no credential) so the endpoint can
    serve them at COMMUNITY limits; resolves and validates the key otherwise so
    a valid key (including the internal/enterprise key) grants its full access.
    A presented-but-invalid key still 401s.

    NOTE: do NOT express optional auth as ``authenticated_user | None = None`` on
    the endpoint — FastAPI silently drops the nested Depends, so the credential is
    never read and every request is treated as anonymous. Use this dependency.
    """
    if authorization is None:
        return None
    return await _resolve_user_from_key(authorization.credentials)


def check_roles(required_roles: list[OpenNEMRoles]):
    """Creates a dependency that checks if user has any of the required roles."""

    async def role_checker(current_user: Annotated[OpenNEMUser, Depends(get_current_user)]) -> OpenNEMUser:
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


def _is_bypass_key(key: str) -> bool:
    """True for the dev/internal bypass keys (constant-time compare)."""
    bypass = [settings.api_dev_key]
    if settings.api_internal_key:
        bypass.append(settings.api_internal_key)
    return any(k and hmac.compare_digest(key.encode(), k.encode()) for k in bypass)


async def get_admin_user(
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(api_token_scheme)],
) -> OpenNEMUser:
    """FastAPI dependency for admin routes: a real Clerk admin, identified via their API key.

    The dev/internal bypass keys resolve to an enterprise admin user in the shared resolver; they are
    rejected (403) before resolving, and the bypass user is rejected again after as defence in depth.
    The admin role must come from Clerk (user has an owner_id), and is read fresh so a revoked admin
    loses access immediately. Missing/invalid key -> 401, valid non-admin -> 403.
    """
    key = authorization.credentials

    if _is_bypass_key(key):
        logger.warning(f"Admin access denied for bypass key {key_fingerprint(key)}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access requires a Clerk admin user")

    user = await _resolve_user_from_key(key, fresh=True)

    is_bypass_user = user.id == _OPENNEM_INTERNAL_USER.id or user.owner_id == _OPENNEM_INTERNAL_USER.owner_id
    if is_bypass_user or not user.owner_id or not user.is_admin:
        logger.warning(f"Admin access denied for user {user.id} (key {key_fingerprint(key)})")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return user


# Common auth dependencies
authenticated_user = Annotated[OpenNEMUser, Depends(get_current_user)]
fresh_authenticated_user = Annotated[OpenNEMUser, Depends(get_current_user_fresh)]
optional_user = Annotated[OpenNEMUser | None, Depends(get_optional_user)]
admin_user = Annotated[OpenNEMUser, Depends(get_admin_user)]
