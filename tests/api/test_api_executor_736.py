"""#736: API default executor is sized and still visible to the loop monitor's depth probe."""

import asyncio
import threading
import time

import pytest

from opennem.api.executor import install_api_executor
from opennem.utils.loop_monitor import get_executor_depth

pytestmark = pytest.mark.asyncio


async def test_executor_sized_and_depth_visible() -> None:
    executor = install_api_executor(max_workers=8)
    try:
        assert get_executor_depth() == 0
        names: set[str] = set()

        def _work() -> None:
            names.add(threading.current_thread().name)
            time.sleep(0.05)

        await asyncio.gather(*(asyncio.to_thread(_work) for _ in range(16)))
        assert 1 < len(names) <= 8
        assert all(n.startswith("api-exec") for n in names)
        assert get_executor_depth() == 0
    finally:
        executor.shutdown(wait=True)
