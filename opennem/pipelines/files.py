import logging
import os
from io import BytesIO
from zipfile import ZipFile

from requests import RequestException

from opennem.utils.handlers import _handle_zip, chain_streams, open
from opennem.utils.http import http
from opennem.utils.mime import decode_bytes, mime_from_content, mime_from_url
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def _fallback_download_handler(url: str) -> bytes:
    """
    This was previously a fallback download handler
    but the name is redundant as it's now the primary
    and takes precedence over the legacy downloader


    """
    r = http.get(url)

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


class LinkExtract(object):
    """
    Parse and extracts links in items.

    If the pipeline item has a "link" it'll download the content
    and attach it to the item as "content" along with some
    basic metadata.

    """

    @check_spider_pipeline
    def process_item(self, item, spider):
        if "link" not in item:
            return item

        url = item["link"]
        fh = None
        content = None
        _, file_extension = os.path.splitext(url)

        try:
            _bytes_obj = _fallback_download_handler(url)
            content = decode_bytes(_bytes_obj)
        except Exception as e:
            logger.error(e)

        if content:
            item["content"] = content
            item["extension"] = file_extension
            return item

        try:
            logger.info("Grabbing: {}".format(url))
            fh = open(url)
        except RequestException:
            logger.info("Bad link: {}".format(url))
        except Exception as e:
            logger.error("Error: {}".format(e))

        if fh:
            content = fh.read()

            item["content"] = content
            item["extension"] = file_extension
            return item
