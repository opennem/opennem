"""unkney client for validating api keys"""

import asyncio
import logging

import unkey
from cachetools.func import ttl_cache
from pydantic import BaseModel, ValidationError
from unkey import ErrorCode

from opennem import settings

logger = logging.getLogger("opennem.clients.unkey")


class UnkneyUser(BaseModel):
    valid: bool
    owner_id: str
    meta: dict | None = None
    error: str | None = None


@ttl_cache(maxsize=100, ttl=60 * 5)
async def unkey_validate(api_key: str) -> None | UnkneyUser:
    """Validate a key with unkey"""

    if not settings.unkey_root_key:
        raise Exception("No unkey root key set")

    if not settings.unkey_api_id:
        raise Exception("No unkey app id set")

    client = unkey.Client(api_key=settings.unkey_root_key)
    await client.start()

    try:
        result = await client.keys.verify_key(key=api_key, api_id=settings.unkey_api_id)

        if not result.is_ok:
            logger.warning("Unkey verification failed")
            return None

        data = result.unwrap()
        logger.debug(f"Unkey response data: {data}")

        # Check if the code is NOT_FOUND and return None if so
        if data.code == ErrorCode.NotFound:
            logger.info("API key not found")
            return None

        try:
            model = UnkneyUser(valid=data.valid, owner_id=data.owner_id, meta=data.meta, error=data.error)
            return model
        except ValidationError as ve:
            logger.error(f"Pydantic validation error: {ve}")
            for error in ve.errors():
                logger.error(f"Field: {error['loc'][0]}, Error: {error['msg']}")
            return None

    except Exception as e:
        logger.exception(f"Unexpected error in unkey_validate: {e}")
        return None

    finally:
        await client.close()


# debug entry point
if __name__ == "__main__":
    test_key = "ondev_123123123"
    model = asyncio.run(unkey_validate(api_key=test_key))

    print(f"Validation result: {model}")
