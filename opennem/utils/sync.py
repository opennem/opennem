import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from asgiref.sync import AsyncToSync

logger = logging.getLogger("opennem.utils.async")


def run_async_task_reusable[**P, R](coroutine: Callable[P, Coroutine[Any, Any, R]]):
    sync_call = AsyncToSync(coroutine)

    @functools.wraps(coroutine)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return sync_call(*args, **kwargs)

    return wrapper


def run_async_task_reusable_old(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            logger.info("A new event loop was spawned.")
            asyncio.set_event_loop(loop)
            loop.run_forever()

        loop.run_until_complete(func(*args, **kwargs))

    return wrapper
