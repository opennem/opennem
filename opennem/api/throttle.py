"""
This module will throttle users who don't provide auth keys and send them to the new API
"""

import logging
import random
from functools import wraps

from fastapi import Depends, Request

from opennem import settings
from opennem.api.exceptions import OpenNEMThrottleMigrateResponse

logger = logging.getLogger("opennem.api.throttle")


def throttle_request():
    if not 0 <= settings.api_throttle_rate <= 1:
        raise ValueError("Throttle rate must be between 0 and 1")

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request = Depends(), *args, **kwargs):
            rand_value = random.random()

            if rand_value < settings.api_throttle_rate:
                raise OpenNEMThrottleMigrateResponse()

            return await func(*args, **kwargs)

        return wrapper

    return decorator
