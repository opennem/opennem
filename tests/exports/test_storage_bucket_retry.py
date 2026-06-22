"""The R2 uploader must build its client with a retry config so transient
InternalError (s3 500) responses are retried instead of aborting exports."""

import pytest

from opennem.exporter.storage_bucket import _S3_RETRY_CONFIG, CloudflareR2Uploader


def test_retry_config_uses_standard_mode_with_extra_attempts() -> None:
    assert _S3_RETRY_CONFIG.retries["mode"] == "standard"
    assert _S3_RETRY_CONFIG.retries["max_attempts"] >= 5


@pytest.mark.asyncio
async def test_client_is_created_with_retry_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    class _FakeSession:
        def client(self, **kwargs):  # noqa: ANN003, ANN201
            captured.update(kwargs)
            return object()

    monkeypatch.setattr("opennem.exporter.storage_bucket.aioboto3.Session", lambda: _FakeSession())

    await CloudflareR2Uploader()._get_s3_client()

    assert captured["config"] is _S3_RETRY_CONFIG
