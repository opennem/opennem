"""
This module will throttle users who don't provide auth keys and send them to the new API
"""

import logging
import random
from functools import wraps

from fastapi import HTTPException, Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from opennem import settings

logger = logging.getLogger("opennem.api.throttle")


def throttle_request():
    if not 0 <= settings.api_throttle_rate <= 1:
        raise ValueError("Throttle rate must be between 0 and 1")

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise ValueError("Request object not found in function arguments")

            client_ip = request.client.host
            endpoint = request.url.path

            cache_key = f"throttle:{client_ip}:{endpoint}"
            cache: RedisBackend = FastAPICache.get_backend()

            # Get the current request count
            count = await cache.get(cache_key) or 0
            count = int(count)

            # Increment the count
            await cache.set(cache_key, str(count + 1), expire=60)  # Reset count after 60 seconds

            # Apply throttling
            rand_value = random.random()

            logger.info(f"Throttle request: {rand_value} < {settings.api_throttle_rate}")
            print(f"Throttle request: {rand_value} < {settings.api_throttle_rate}")

            if rand_value < settings.api_throttle_rate:
                raise HTTPException(status_code=403, detail="Request throttled")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
