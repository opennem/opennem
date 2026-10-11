import asyncio
import hashlib
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opennem.core.parsers import dirlisting
from opennem.core.parsers.dirlisting import DirlistingEntry, parse_dirlisting_datetime, parse_dirlisting_line

from .conftest import PATH_TESTS_FIXTURES


def load_fixture(filename: str = "nemweb_dirlisting.html") -> str:
    fixture_path = PATH_TESTS_FIXTURES / Path(filename)

    if not fixture_path.is_file():
        raise Exception(f"Not a file: {filename}")

    fixture_content = ""

    with fixture_path.open() as fh:
        fixture_content = fh.read()

    return fixture_content


@pytest.mark.parametrize(
    ["datetime_string", "datetime_expected"],
    [
        ("Monday, November 8, 2021  2:30 PM", datetime.fromisoformat("2021-11-08T14:30")),
        ("Wednesday, December 28, 2022 9:10", datetime.fromisoformat("2022-12-28T09:10")),
    ],
)
def test_parse_dirlisting_datetime(datetime_string: str, datetime_expected: datetime) -> None:
    datetime_subject = parse_dirlisting_datetime(datetime_string)
    assert datetime_expected == datetime_subject, "Datetime parsed correctly"


@pytest.mark.parametrize(
    ["line", "result"],
    [
        (
            "     Monday, November 8, 2021  2:30 PM        18166 "
            '<a href="http://nemweb.com.au/Reports/Current/DispatchIS'
            '_Reports/PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip">'
            "PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip</a>",
            {
                "filename": Path("PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip"),
                "modified_date": datetime.fromisoformat("2021-11-08T14:30:00"),
                # "aemo_created_date": datetime.fromisoformat("2021-11-08T14:35:00"),
                "file_size": 18166,
                "link": "http://nemweb.com.au/Reports/Current/DispatchIS_Reports/"
                "PUBLIC_DISPATCHIS_202111081435_0000000352251582.zip",
            },
        ),
        (
            "Monday, February 11, 2019  4:31 PM        <dir> "
            '<a href="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/DUPLICATE/">DUPLICATE</a>',
            {
                "filename": Path("DUPLICATE"),
                "modified_date": datetime.fromisoformat("2019-02-11T16:31:00"),
                "file_size": None,
                "link": "http://nemweb.com.au/Reports/Current/DispatchIS_Reports/DUPLICATE/",
            },
        ),
    ],
)
def test_dirlisting_line(line: str, result: dict[str, str | datetime | int]) -> None:
    result_model = DirlistingEntry(**result)
    dirlisting_line_result = parse_dirlisting_line(line)

    assert result_model == dirlisting_line_result, "Models match for dirlisting line"


def test_current_format_directory_line_is_skipped_quietly() -> None:
    """nemweb's current listing puts `<dir>` where the size goes; those rows are skipped at debug, not warned"""
    line = 'Tuesday, July 22, 2025 10:23 AM <dir> <A HREF="/Reports/CURRENT/DispatchIS_Reports/DUPLICATE/">DUPLICATE</A>'

    with patch.object(dirlisting, "logger") as logger:
        assert parse_dirlisting_line(line) is None

    logger.warning.assert_not_called()
    logger.debug.assert_called_once()


def test_unmatched_file_line_still_warns() -> None:
    with patch.object(dirlisting, "logger") as logger:
        assert parse_dirlisting_line("this is not a dirlisting line") is None

    logger.warning.assert_called_once()


# golden digest of `get_dirlisting` over the fixture, captured before the parse moved off the event loop
_FIXTURE_URL = "https://nemweb.com.au/Reports/Current/Dispatch_SCADA/"
_FIXTURE_ENTRIES = 578
_FIXTURE_SHA256 = "0253370530f83ab76d4772a70ef185dcf43c82792e01582e968c8b0f22e48009"


def _patched_http(text: str):  # noqa: ANN202
    resp = MagicMock()
    resp.text = text
    return patch.object(dirlisting.http, "get", AsyncMock(return_value=resp))


@pytest.mark.asyncio
async def test_get_dirlisting_fixture_characterization() -> None:
    with _patched_http(load_fixture()):
        listing = await dirlisting.get_dirlisting(_FIXTURE_URL, "Australia/Brisbane")

    assert len(listing.entries) == _FIXTURE_ENTRIES
    assert hashlib.sha256(listing.model_dump_json().encode()).hexdigest() == _FIXTURE_SHA256


@pytest.mark.asyncio
async def test_get_dirlisting_large_listing_keeps_loop_ticking() -> None:
    row = (
        "     Monday, November 8, 2021  2:30 PM        18166 "
        '<a href="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/{name}">{name}</a>'
    )
    names = [f"PUBLIC_DISPATCHIS_2021110814{n % 60:02d}_{n:016d}.zip" for n in range(25_000)]
    html_text = "<pre>" + "<br>".join(row.format(name=name) for name in names) + "</pre>"

    lags: list[float] = []
    stop = asyncio.Event()

    async def ticker() -> None:
        last = time.perf_counter()
        while not stop.is_set():
            await asyncio.sleep(0.05)
            now = time.perf_counter()
            lags.append(now - last - 0.05)
            last = now

    task = asyncio.create_task(ticker())
    await asyncio.sleep(0.1)
    with _patched_http(html_text):
        listing = await dirlisting.get_dirlisting(_FIXTURE_URL, "Australia/Brisbane")
    stop.set()
    await task

    assert len(listing.entries) == len(names)
    assert listing.entries[0].filename == Path(names[0])
    assert max(lags) < 0.25, f"event loop stalled {max(lags):.2f}s during dirlisting parse"
