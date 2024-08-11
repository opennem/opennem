import asyncio
import functools
import logging
import threading
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

from asgiref.sync import AsyncToSync

thread_local = threading.local()


logger = logging.getLogger("opennem.utils.async")

# https://stackoverflow.com/questions/61064782/how-to-use-typevar-with-async-function-in-python
P = ParamSpec("P")
R = TypeVar("R")


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
        loop = asyncio.get_running_loop()  # This only works in Python 3.7+
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def run_async_task_loop[**P, R](coroutine: Callable[P, Coroutine[Any, Any, R]]):
    @functools.wraps(coroutine)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return asyncio.run(coroutine(*args, **kwargs))

    return wrapper


def get_or_create_eventloop():
    try:
        return thread_local.loop
    except AttributeError:
        thread_local.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(thread_local.loop)
        return thread_local.loop


def run_async_task_reusable[**P, R](coroutine: Callable[P, Coroutine[Any, Any, R]]):
    @functools.wraps(coroutine)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = get_or_create_eventloop()
        return loop.run_until_complete(coroutine(*args, **kwargs))

    return wrapper


def run_async_task_reusable_old[**P, R](coroutine: Callable[P, Coroutine[Any, Any, R]]):
    sync_call = AsyncToSync(coroutine)

    @functools.wraps(coroutine)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return sync_call(*args, **kwargs)

    return wrapper
