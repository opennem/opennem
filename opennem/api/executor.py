"""Dedicated default executor for the API process (#736).

`asyncio.to_thread` uses the loop default executor, sized min(32, cpu+4): 5 threads on the 1 vCPU dev box. A cold
timeseries request does several hops (ClickHouse execute, row formatting, encode) and the ClickHouse hops are pure
network wait, so 10-14 parallel requests queued behind 5 threads while the CPU sat idle.

32 threads: ClickHouse waits dominate, so the pool only needs to cover in-flight queries plus the short CPU hops
(GIL-bound, so extra threads add no CPU parallelism but also no meaningful cost). Threads spawn lazily, so an idle
process holds none. Each thread that runs a query lazily opens one thread-local ClickHouse client (one TCP
connection, small buffers), so worst case is 32 connections per API process, well under the server's limit.
Override with API_EXECUTOR_THREADS. ARQ workers keep the stdlib default (this is only installed from the API lifespan).
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

API_EXECUTOR_THREADS = int(os.environ.get("API_EXECUTOR_THREADS", "32"))


def install_api_executor(
    loop: asyncio.AbstractEventLoop | None = None, max_workers: int = API_EXECUTOR_THREADS
) -> ThreadPoolExecutor:
    """Set a sized ThreadPoolExecutor as the running loop's default executor and return it."""
    loop = loop or asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="api-exec")
    loop.set_default_executor(executor)
    return executor
