"""
    mime module - get mime types from url (filename) or bytes


"""

import logging
import mimetypes
from io import BytesIO
from typing import BinaryIO, Optional
from zipfile import BadZipFile, ZipFile

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


def is_zip(fh: BinaryIO, test_zip: bool = True) -> bool:
    """Check if a file-like object is a zip file"""
    try:
        zf = ZipFile(fh)

        if not test_zip:
            return True

        # test_result will CRC check each file and return none on success
        test_result = zf.testzip()

        if not test_result:
            return True

    except BadZipFile:
        return False

    return False
