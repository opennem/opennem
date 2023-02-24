"""
    mime module - get mime types from url (filename) or bytes


"""

import logging
import mimetypes
import re
import string
import subprocess
from io import BytesIO
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

        file_mime = magic.from_buffer(_file_buffer, mime=True)
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


def _is_textfile_proc(fn):
    """Linux only proc to check if a file is text"""
    msg = subprocess.Popen(["file", fn], stdout=subprocess.PIPE).communicate()[0]
    return re.search("text", msg) is not None


def is_textfile(fh: BinaryIO) -> bool:
    """Check if a file is a text file by looking at proportion of non-ASCII characters in file buffer"""
    fh.seek(0)
    _buffer = fh.read(512)
    fh.seek(0)

    if not _buffer:
        return True

    if "\0" in _buffer:
        return False

    text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
    _null_trans = string.maketrans("", "")

    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = _buffer.translate(_null_trans, text_characters)

    # If more than 30% non-text characters, then
    # this is considered a binary file
    if float(len(t)) / float(len(_buffer)) > 0.30:
        return False

    return True
