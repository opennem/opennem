import logging
from io import BytesIO
from zipfile import ZipFile

from opennem.utils.handlers import _handle_zip, chain_streams
from opennem.utils.http import http
from opennem.utils.mime import mime_from_content, mime_from_url

logger = logging.getLogger("opennem.downloader")


def url_downloader(url: str) -> bytes:
    """Downloads a URL and returns content, handling embedded zips and other MIME's"""

    logger.debug("Downloading: {}".format(url))

    r = http.get(url, verify=False)

    if not r.ok:
        raise Exception("Bad link returned {}: {}".format(r.status_code, url))

    content = BytesIO(r.content)

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
