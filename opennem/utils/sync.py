import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import gevent.monkey
from asgiref.sync import AsyncToSync

logger = logging.getLogger("opennem.utils.async")

gevent.monkey.patch_all()


def run_async_task(async_func):
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        loop = get_running_loop()
        coroutine = async_func(*args, **kwargs)
        future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        return future.result()

    return wrapper


def get_running_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        print("A new event loop was spawned.")
        asyncio.set_event_loop(loop)
        loop.run_forever()
    return loop


def run_async_task_reusable[**P, R](coroutine: Callable[P, Coroutine[Any, Any, R]]):
    sync_call = AsyncToSync(coroutine)

    @functools.wraps(coroutine)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return sync_call(*args, **kwargs)

    return wrapper
