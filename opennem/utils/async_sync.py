"""
Utility module for converting between async and sync functions in OpenNEM.

This module provides decorators to help bridge between asynchronous and
synchronous code, particularly useful when integrating async OpenNEM
functionality with synchronous interfaces or command line tools.
"""

import asyncio
from functools import wraps


def async_to_sync(f):
    """
    Decorator that converts an async function to a synchronous function.

    This decorator wraps an asynchronous function and makes it callable from
    synchronous code by running it in a new event loop using asyncio.run().
    Useful for CLI tools and testing scenarios where async functions need
    to be called from synchronous contexts.

    Args:
        f: The async function to be wrapped

    Returns:
        callable: A synchronous function that will run the async function
        in its own event loop

    Example:
        @async_to_sync
        async def fetch_data():
            # async code here
            pass

        # Can now be called synchronously
        fetch_data()
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper
