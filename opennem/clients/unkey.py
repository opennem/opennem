"""unkey client for validating api keys"""

import asyncio
import logging

import httpx
from pydantic import ValidationError
from unkey.py import Unkey

from opennem import settings
from opennem.users.schema import OpennemAPIRequestMeta, OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit

logger = logging.getLogger("opennem.clients.unkey")

UNKEY_TIMEOUT_S = 3.0
UNKEY_ATTEMPTS = 2  # one retry

_unkey_client: Unkey | None = None


class UnkeyInvalidUserException(Exception):
    """Unkey answered and the key is not valid."""


class UnkeyUnavailableException(UnkeyInvalidUserException):
    """Unkey did not give an answer (timeout, transport or server error). Never means the key is invalid.

    Subclasses UnkeyInvalidUserException so legacy callers that catch the base keep working.
    """


def _get_unkey_client() -> Unkey:
    """Shared module-level Unkey client: keepalive connection pool, bounded timeout."""
    global _unkey_client

    if _unkey_client is None:
        _unkey_client = Unkey(
            root_key=settings.unkey_root_key,
            async_client=httpx.AsyncClient(
                timeout=httpx.Timeout(UNKEY_TIMEOUT_S),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=60),
            ),
            timeout_ms=int(UNKEY_TIMEOUT_S * 1000),
        )

    return _unkey_client


async def unkey_validate(api_key: str) -> None | OpenNEMUser:
    """
    Validate a key with unkey.
    Raises UnkeyInvalidUserException when Unkey says the key is invalid and
    UnkeyUnavailableException when Unkey could not be reached (retried once).
    """

    if not settings.unkey_root_key:
        raise Exception("No unkey root key set")

    try:
        response = None
        for attempt in range(UNKEY_ATTEMPTS):
            try:
                response = await asyncio.wait_for(
                    _get_unkey_client().keys.verify_key_async(key=api_key), timeout=UNKEY_TIMEOUT_S + 1
                )
                break
            except Exception as e:
                if attempt == UNKEY_ATTEMPTS - 1:
                    raise UnkeyUnavailableException(f"Unkey unreachable: {type(e).__name__}: {e}") from e
                logger.warning(f"Unkey verify failed ({type(e).__name__}), retrying")

        if not response or not response.data:
            logger.warning("Unkey verification failed: no response data")
            raise UnkeyInvalidUserException("Verification failed: no response")

        data = response.data

        if not data.valid:
            logger.info("API key is not valid")
            raise UnkeyInvalidUserException("Verification failed: not valid")

        if not data.key_id:
            logger.info("API key id is not valid no id")
            raise UnkeyInvalidUserException("Verification failed: no id")

        try:
            # Extract owner_id from identity if available
            owner_id = data.identity.external_id if data.identity else None
            logger.debug(f"Unkey response - identity: {data.identity}, owner_id extracted: {owner_id}")

            model = OpenNEMUser(
                id=data.key_id,
                owner_id=owner_id,
                unkey_meta=data.meta,
            )

            # Set meta with credits and expiry
            model.meta = OpennemAPIRequestMeta(remaining=data.credits if data.credits else None, reset=data.expires)

            # Process ratelimits array
            if data.ratelimits and len(data.ratelimits) > 0:
                first_ratelimit = data.ratelimits[0]
                model.rate_limit = OpenNEMUserRateLimit(
                    limit=first_ratelimit.limit, remaining=first_ratelimit.remaining, reset=first_ratelimit.reset
                )

            # Resolve roles from unkey meta (admin only)
            if data.meta and "roles" in data.meta:
                for role in data.meta["roles"]:
                    try:
                        model.roles.append(OpenNEMRoles(role))
                    except ValueError:
                        # Skip unknown roles (legacy pro/academic/user)
                        pass

            return model
        except ValidationError as ve:
            logger.error(f"Pydantic validation error: {ve}")
            for error in ve.errors():
                logger.error(f"Field: {error['loc'][0]}, Error: {error['msg']}")
            raise UnkeyInvalidUserException("Unkey verification failed: model validation error") from ve

    except UnkeyInvalidUserException:
        raise
    except Exception as e:
        logger.warning(f"Unexpected error in unkey_validate: {e}")
        raise UnkeyUnavailableException("Unkey verification failed: unexpected error") from e


# debug entry point
if __name__ == "__main__":
    import os

    test_key = os.environ.get("OPENNEM_UNKEY_TEST_KEY", None)

    if not test_key:
        raise Exception("No test key set")

    model = asyncio.run(unkey_validate(api_key=test_key))

    if not model:
        print("No model")
    else:
        print(model)
