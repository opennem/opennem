"""
mime module - get mime types from url (filename) or bytes

Provides utilities for:
- Detecting MIME types from filenames and content
- Handling text and binary file detection
- Supporting common file formats including images
"""

import logging
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from zipfile import BadZipFile, ZipFile

try:
    import magic

    HAVE_MAGIC = True
except ImportError:
    HAVE_MAGIC = False

mimetypes.init()

logger = logging.getLogger(__name__)

CONTENT_TYPES = ["utf-8", "utf-8-sig", "latin-1"]

# Common MIME types mapping
MIME_TYPES = {
    # Documents
    "parquet": "application/octet-stream",
    "csv": "text/csv",
    "json": "application/json",
    "txt": "text/plain",
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    # Images
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "webp": "image/webp",
    "tiff": "image/tiff",
    "svg": "image/svg+xml",
}


def mime_from_filename(filename: str, default_mime: str | None = "application/octet-stream") -> str | None:
    """
    Detects the content type based on file extension using pathlib

    Args:
        filename: Name of the file
        default_mime: Default MIME type to return if extension not found

    Returns:
        str: MIME type for the file or default_mime if not found
    """
    try:
        extension = Path(filename).suffix.lower().lstrip(".")
        return MIME_TYPES.get(extension, default_mime)
    except Exception as e:
        logger.error(f"Error parsing filename {filename}: {e}")
        return default_mime


def mime_from_content(content: BinaryIO) -> str | None:
    """
    Use libmime to get mime type from content stream
    """
    if not HAVE_MAGIC:
        return None

    if isinstance(content, bytes):
        content = BytesIO(content)

    try:
        _file_buffer: bytes = content.read(2048)

        # rewind it back again
        content.seek(0)

        file_mime = magic.from_buffer(_file_buffer, mime=True)  # type: ignore
    except Exception as e:
        logger.error(f"Error parsing mime from content: {e}")
        return None

    logger.debug(f"Using magic to get mime type {file_mime}")

    return file_mime


def mime_from_url(url: str) -> str | None:
    """
    Use python mimetypes dir to get mime type from file extension
    """
    file_mime, _ = mimetypes.guess_type(url)
    logger.debug(f"Using mimetypes to get mime type {file_mime}")
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
