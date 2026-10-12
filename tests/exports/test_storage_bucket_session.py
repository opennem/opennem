"""Shared aioboto3 session + boot warm-up for the R2 uploader. Offline: no network, no real uploads."""

import time
from collections.abc import Iterator

import pytest

from opennem.exporter import storage_bucket
from opennem.exporter.storage_bucket import CloudflareR2Uploader, get_s3_session, warm_s3_client


class _FakeClient:
    def __init__(self, calls: list) -> None:
        self.calls = calls

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *a: object) -> None:
        return None

    async def put_object(self, **kwargs: object) -> None:
        self.calls.append(kwargs)


@pytest.fixture(autouse=True)
def _reset_cache() -> Iterator[None]:
    get_s3_session.cache_clear()
    yield
    get_s3_session.cache_clear()


@pytest.fixture
def fake_session(monkeypatch: pytest.MonkeyPatch) -> dict:
    state: dict = {"sessions": 0, "client_kwargs": [], "puts": []}

    class _Session:
        def __init__(self) -> None:
            state["sessions"] += 1

        def client(self, **kwargs: object) -> _FakeClient:
            state["client_kwargs"].append(kwargs)
            return _FakeClient(state["puts"])

    monkeypatch.setattr(storage_bucket.aioboto3, "Session", _Session)
    return state


@pytest.mark.asyncio
async def test_many_uploads_create_one_session(fake_session: dict) -> None:
    up = CloudflareR2Uploader(bucket_name="b", bucket_url="https://x/")
    for i in range(5):
        assert await up.upload_bytes(b"abc", f"k{i}", "application/json") == 3

    assert fake_session["sessions"] == 1
    assert len(fake_session["client_kwargs"]) == 5  # client still per upload
    kw = fake_session["client_kwargs"][0]
    assert kw["service_name"] == "s3"
    assert kw["config"] is storage_bucket._S3_RETRY_CONFIG
    assert fake_session["puts"][0] == {"Bucket": "b", "Key": "k0", "Body": b"abc", "ContentType": "application/json"}


@pytest.mark.asyncio
async def test_warm_up_loads_model_once_and_shares_session(fake_session: dict) -> None:
    await warm_s3_client()
    assert fake_session["sessions"] == 1
    assert len(fake_session["client_kwargs"]) == 1
    await CloudflareR2Uploader(bucket_name="b", bucket_url="https://x/").upload_bytes(b"a", "k")
    assert fake_session["sessions"] == 1


@pytest.mark.asyncio
async def test_warm_up_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(storage_bucket, "get_s3_session", boom)
    await warm_s3_client()


@pytest.mark.asyncio
async def test_second_client_creation_faster_than_first() -> None:
    """Real aioboto3 session, no network: client creation loads the model only once."""
    session = get_s3_session()
    kw = {
        "service_name": "s3",
        "endpoint_url": "http://127.0.0.1:9",
        "aws_access_key_id": "a",
        "aws_secret_access_key": "b",
        "region_name": "apac",
    }
    t0 = time.perf_counter()
    async with session.client(**kw):
        pass
    first = time.perf_counter() - t0
    t0 = time.perf_counter()
    async with session.client(**kw):
        pass
    second = time.perf_counter() - t0
    assert second < first
