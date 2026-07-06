"""Nemweb download timeouts on large files (eg. Next_Day_Dispatch) are transient and
expected - they shouldn't page sentry as errors. Other download failures still should.
See GH #571."""

import pytest
from rnet.exceptions import TimeoutError as RnetTimeoutError

from opennem.core.parsers.aemo import nemweb


def test_timeout_error_logs_as_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    levels: list[str] = []
    monkeypatch.setattr(nemweb.logger, "warning", lambda *a, **kw: levels.append("warning"))
    monkeypatch.setattr(nemweb.logger, "error", lambda *a, **kw: levels.append("error"))

    nemweb._log_download_error("https://nemweb.com.au/some.zip", RnetTimeoutError("TimedOut"))

    assert levels == ["warning"]


def test_other_download_error_logs_as_error(monkeypatch: pytest.MonkeyPatch) -> None:
    levels: list[str] = []
    monkeypatch.setattr(nemweb.logger, "warning", lambda *a, **kw: levels.append("warning"))
    monkeypatch.setattr(nemweb.logger, "error", lambda *a, **kw: levels.append("error"))

    nemweb._log_download_error("https://nemweb.com.au/some.zip", Exception("Failed to download file: Status code 500"))

    assert levels == ["error"]
