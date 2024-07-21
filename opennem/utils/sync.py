import asyncio
import functools
import logging

logger = logging.getLogger("opennem.utils.async")


def run_async_task_reusable(func):
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
