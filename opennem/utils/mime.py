"""
    mime module - get mime types from url (filename) or bytes


"""

import logging
import mimetypes
from io import BytesIO
from typing import Optional

try:
    import magic

    HAVE_MAGIC = True
except ImportError:
    HAVE_MAGIC = False

mimetypes.init()

logger = logging.getLogger(__name__)

CONTENT_TYPES = ["utf-8", "utf-8-sig", "latin-1"]


def mime_from_content(content: BytesIO) -> Optional[str]:
    """
    Use libmime to get mime type from content stream
    """
    if not HAVE_MAGIC:
        return None

    if isinstance(content, bytes):
        content = BytesIO(content)

    try:
        file_mime = magic.from_buffer(content.read(2048), mime=True)
    except Exception as e:
        logger.error("Error parsing mime from content: {}".format(e))
        return None

    logger.debug("Using magic to get mime type {}".format(file_mime))

    return file_mime


def mime_from_url(url: str) -> Optional[str]:
    """
    Use python mimetypes dir to get mime type from file extension
    """
    file_mime, _ = mimetypes.guess_type(url)
    logger.debug("Using mimetypes to get mime type {}".format(file_mime))
    return file_mime


def decode_bytes(content: bytes) -> str:
    """
    Brute force decode content
    """

    for enc in CONTENT_TYPES:
        try:
            return content.decode(enc)
        except Exception:
            pass

    raise Exception("Could not decode")
