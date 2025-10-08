import logging
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from opennem.utils.archive import _handle_zip, chain_streams
from opennem.utils.httpx import httpx_factory
from opennem.utils.mime import mime_from_content, mime_from_url

logger = logging.getLogger("opennem.downloader")


async def url_downloader(url: str) -> bytes:
    """Downloads a URL and returns content, handling embedded zips and other MIME's"""

    logger.debug(f"Downloading: {url}")

    http = httpx_factory(proxy=True)

    response = await http.get(url)

    response.raise_for_status()

    content = BytesIO(response.content)

    file_mime = mime_from_content(content)

    if not file_mime:
        file_mime = mime_from_url(url)

    # @TODO handle all this in utils/archive.py
    # and make it all generic to handle other
    # mime types
    if file_mime == "application/zip":
        with ZipFile(content) as zf:
            if len(zf.namelist()) == 1:
                return zf.open(zf.namelist()[0]).read()

            c = []
            stream_count = 0

            for filename in zf.namelist():
                if filename.endswith(".zip"):
                    c.append(_handle_zip(zf.open(filename), "r"))
                    stream_count += 1
                else:
                    c.append(zf.open(filename))

            return chain_streams(c).read()

    return content.getvalue()


def file_opener(path: Path) -> bytes:
    """Opens a local file, handling embedded zips and other MIME's"""

    logger.debug(f"Opening file: {path}")

    if not path.is_file():
        raise Exception(f"File not found: {path}")

    content: BytesIO | None = None

    with path.open("rb") as fh:
        content = BytesIO(fh.read())

    file_mime = mime_from_content(content)

    # @TODO handle all this in utils/archive.py
    # and make it all generic to handle other
    # mime types
    if file_mime == "application/zip":
        with ZipFile(content) as zf:
            if len(zf.namelist()) == 1:
                return zf.open(zf.namelist()[0]).read()

            c = []
            stream_count = 0

            for filename in zf.namelist():
                if filename.endswith(".zip"):
                    c.append(_handle_zip(zf.open(filename), "r"))
                    stream_count += 1
                else:
                    c.append(zf.open(filename))

            return chain_streams(c).read()

    return content.getvalue()


if __name__ == "__main__":
    import asyncio

    url = "https://data.wa.aemo.com.au/public/market-data/wemde/tradingReport/tradingDayReport/previous/"

    content = asyncio.run(url_downloader(url))
    print(content)
