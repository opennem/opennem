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
    id: str
    owner_id: str | None = None
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
        async with unkey.client.Client() as c:
            result = await c.keys.verify_key(key=api_key, api_id=settings.unkey_api_id)  # type: ignore

        if not result.is_ok:
            logger.warning("Unkey verification failed")
            return None

        if result.is_err:
            err = result.unwrap_err()
            code = (err.code or unkey.models.ErrorCode.Unknown).value
            logger.info(f"Unkey verification failed: {code}")
            return None

        data = result.unwrap()
        logger.debug(f"Unkey response data: {data}")

        # Check if the code is NOT_FOUND and return None if so
        if data.code == ErrorCode.NotFound:
            logger.info("API key not found")
            return None

        if not data.valid:
            logger.info("API key is not valid")
            return None

        if data.error:
            logger.info(f"API key error: {data.error}")
            return None

        if not data.id:
            logger.info("API key id is not valid no id")
            return None

        try:
            model = UnkneyUser(id=data.id, valid=data.valid, owner_id=data.owner_id, meta=data.meta, error=data.error)
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
    test_key = "on_3ZixTh7Z8gqgW5gF3VoxN4PZ"
    model = asyncio.run(unkey_validate(api_key=test_key))

    print(f"Validation result: {model}")
