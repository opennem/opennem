"""rnet's `await resp.bytes()` blocks the event loop for the whole body read: it must run off the loop

Offline: serves a throttled body from a throwaway server on 127.0.0.1.
"""

import asyncio
import gzip
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from opennem.utils.http import http_factory

CHUNK = 64 * 1024
CHUNK_DELAY = 0.03
TICK = 0.05
# the throttled read below takes >0.5s; a live loop ticks every ~50ms
MAX_LAG = 0.25

BODY_SMALL = b'{"data": [1, 2, 3]}'
BODY_LARGE = b'{"data": "' + b"x" * (CHUNK * 20) + b'"}'


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args: object) -> None:
        pass

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.strip("/")
        body = BODY_SMALL if path.startswith("small") else BODY_LARGE
        if path.startswith("gzip"):
            body = gzip.compress(BODY_LARGE)
        if path == "missing":
            self.send_response(404)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"no")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        if path.startswith("gzip"):
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        for i in range(0, len(body), CHUNK):
            self.wfile.write(body[i : i + CHUNK])
            self.wfile.flush()
            if path.startswith(("large", "gzip")):
                time.sleep(CHUNK_DELAY)


@pytest.fixture(scope="module")
def base_url() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


async def _max_lag_during(coro):  # noqa: ANN001, ANN202
    lags: list[float] = []
    stop = asyncio.Event()

    async def ticker() -> None:
        last = time.perf_counter()
        while not stop.is_set():
            await asyncio.sleep(TICK)
            now = time.perf_counter()
            lags.append(now - last - TICK)
            last = now

    task = asyncio.create_task(ticker())
    await asyncio.sleep(TICK * 2)
    try:
        result = await coro
    finally:
        stop.set()
        await task
    return result, max(lags)


@pytest.mark.asyncio
async def test_large_body_read_keeps_loop_ticking(base_url: str) -> None:
    client = http_factory(proxy=False, debug=False)

    resp, max_lag = await _max_lag_during(client.get(f"{base_url}/large"))

    assert resp.content == BODY_LARGE
    assert max_lag < MAX_LAG, f"event loop stalled {max_lag:.2f}s during body read"


@pytest.mark.asyncio
async def test_gzip_body_read_keeps_loop_ticking(base_url: str) -> None:
    client = http_factory(proxy=False, debug=False)

    resp, max_lag = await _max_lag_during(client.get(f"{base_url}/gzip"))

    assert resp.content == BODY_LARGE
    assert max_lag < MAX_LAG, f"event loop stalled {max_lag:.2f}s during body read"


@pytest.mark.asyncio
async def test_body_helper_returns_identical_response(base_url: str) -> None:
    client = http_factory(proxy=False, debug=False)

    small = await client.get(f"{base_url}/small")
    assert small.status_code == 200
    assert small.is_success
    assert small.content == BODY_SMALL
    assert small.text == BODY_SMALL.decode()
    assert small.json() == {"data": [1, 2, 3]}
    assert small.headers["content-type"] == "application/json"

    large = await client.get(f"{base_url}/large")
    assert large.content == BODY_LARGE
    assert large.text == BODY_LARGE.decode()
    assert isinstance(large.content, bytes)


@pytest.mark.asyncio
async def test_error_status_body_still_returned(base_url: str) -> None:
    client = http_factory(proxy=False, debug=False, retry_403=False)

    resp = await client.get(f"{base_url}/missing")

    assert resp.status_code == 404
    assert resp.content == b"no"
    assert resp.text == "no"
