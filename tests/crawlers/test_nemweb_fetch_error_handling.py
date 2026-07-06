"""Fetch-404s for files that have rolled off the nemweb CURRENT directory should age out
(stop being logged/retried as errors here) rather than paging sentry forever - the
ARCHIVE/catchup crawler owns backfilling them. See GH #571."""

from datetime import datetime, timedelta

import pytest

from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority
from opennem.core.parsers.aemo.filenames import AEMOMMSFilename
from opennem.core.parsers.dirlisting import DirlistingEntry
from opennem.crawlers.nemweb import ENTRY_ROLLOFF_AGE, _handle_fetch_error, run_nemweb_aemo_crawl


def _entry(interval_date: datetime | None) -> DirlistingEntry:
    return DirlistingEntry(
        filename="PUBLIC_ROOFTOP_PV_ACTUAL_MEASUREMENT_20260603103000.zip",
        link="https://nemweb.com.au/PUBLIC_ROOFTOP_PV_ACTUAL_MEASUREMENT_20260603103000.zip",
        modified_date=datetime(2026, 6, 3, 10, 30, 0),
        aemo_interval_date=AEMOMMSFilename(filename="ROOFTOP", date=interval_date) if interval_date else None,
    )


def _crawler() -> CrawlerDefinition:
    return CrawlerDefinition(name="au.nemweb.current.rooftop", priority=CrawlerPriority.high, processor=run_nemweb_aemo_crawl)


@pytest.mark.asyncio
async def test_recent_404_is_not_aged_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 404 on a file still inside the rolloff window should just log and retry next run"""
    called = False

    async def _fake_set_crawler_history(*args, **kwargs):  # noqa: ANN002, ANN003, ANN201
        nonlocal called
        called = True

    monkeypatch.setattr("opennem.crawlers.nemweb.set_crawler_history", _fake_set_crawler_history)

    recent_entry = _entry(datetime.now() - timedelta(hours=1))
    await _handle_fetch_error(crawler=_crawler(), entry=recent_entry, error=Exception("HTTP Error 404: not found"))

    assert not called


@pytest.mark.asyncio
async def test_stale_404_ages_out_via_crawler_history(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 404 on a file well past the rolloff window has fallen off CURRENT for good -
    record a zero-result history entry so this crawler stops re-queuing it"""
    recorded: list = []

    async def _fake_set_crawler_history(crawler_name, histories):  # noqa: ANN001, ANN201
        recorded.append((crawler_name, histories))

    monkeypatch.setattr("opennem.crawlers.nemweb.set_crawler_history", _fake_set_crawler_history)

    stale_date = datetime.now() - ENTRY_ROLLOFF_AGE - timedelta(days=1)
    stale_entry = _entry(stale_date)
    crawler = _crawler()

    await _handle_fetch_error(crawler=crawler, entry=stale_entry, error=Exception("HTTP Error 404: not found"))

    assert len(recorded) == 1
    crawler_name, histories = recorded[0]
    assert crawler_name == crawler.name
    assert histories[0].interval == stale_date
    assert histories[0].records == 0


@pytest.mark.asyncio
async def test_non_404_error_never_ages_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-404 fetch errors are real problems - never silently age them out"""
    called = False

    async def _fake_set_crawler_history(*args, **kwargs):  # noqa: ANN002, ANN003, ANN201
        nonlocal called
        called = True

    monkeypatch.setattr("opennem.crawlers.nemweb.set_crawler_history", _fake_set_crawler_history)

    stale_date = datetime.now() - ENTRY_ROLLOFF_AGE - timedelta(days=1)
    stale_entry = _entry(stale_date)

    await _handle_fetch_error(crawler=_crawler(), entry=stale_entry, error=Exception("Connection reset by peer"))

    assert not called


@pytest.mark.asyncio
async def test_missing_interval_date_never_ages_out(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the filename couldn't be parsed into a date there's no age to check against"""
    called = False

    async def _fake_set_crawler_history(*args, **kwargs):  # noqa: ANN002, ANN003, ANN201
        nonlocal called
        called = True

    monkeypatch.setattr("opennem.crawlers.nemweb.set_crawler_history", _fake_set_crawler_history)

    entry_no_date = _entry(None)

    await _handle_fetch_error(crawler=_crawler(), entry=entry_no_date, error=Exception("HTTP Error 404: not found"))

    assert not called
