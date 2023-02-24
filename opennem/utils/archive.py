"""
Module to handle zip files and nested zip files.

"""
import io
import os
from asyncio.log import logger
from io import BytesIO
from pathlib import Path
from tempfile import mkdtemp
from typing import IO, Any
from zipfile import ZipFile

from opennem.settings import settings
from opennem.utils.url import get_filename_from_url

from .http import http

# limit how many zips within zips we'll parse
# 0 means all
ZIP_LIMIT = 0


def chain_streams(streams: Any, buffer_size: int = io.DEFAULT_BUFFER_SIZE) -> io.BufferedReader:
    """
    Chain an iterable of streams together into a single buffered stream.
    Usage:
        def generate_open_file_streams():
            for file in filenames:
                yield open(file, 'rb')
        f = chain_streams(generate_open_file_streams())
        f.read()
    """

    class ChainStream(io.RawIOBase):
        def __init__(self) -> None:
            self.leftover = b""
            self.stream_iter = iter(streams)
            try:
                self.stream = next(self.stream_iter)
            except StopIteration:
                self.stream = None

        def readable(self) -> bool:
            return True

        def _read_next_chunk(self, max_length: int) -> bytes:
            if self.leftover:
                return self.leftover
            elif self.stream is not None:
                return self.stream.read(max_length)
            else:
                return b""

        def readinto(self, b: Any) -> int:
            buffer_length = len(b)
            chunk = self._read_next_chunk(buffer_length)
            while len(chunk) == 0:
                # move to next stream
                if self.stream is not None:
                    self.stream.close()
                try:
                    self.stream = next(self.stream_iter)
                    chunk = self._read_next_chunk(buffer_length)
                except StopIteration:
                    # No more streams to chain together
                    self.stream = None
                    return 0  # indicate EOF
            output, self.leftover = (
                chunk[:buffer_length],
                chunk[buffer_length:],
            )
            b[: len(output)] = output

            return len(output)

    return io.BufferedReader(ChainStream(), buffer_size=buffer_size)


def _handle_zip(file_obj: Any, mode: str) -> io.BufferedReader | IO[bytes]:
    """Handles zips of zips"""
    with ZipFile(file_obj) as zf:
        if len(zf.namelist()) == 1:
            return zf.open(zf.namelist()[0])

        c = []
        stream_count = 0

        for filename in zf.namelist():
            if filename.endswith(".zip"):
                if ZIP_LIMIT > 0 and stream_count >= ZIP_LIMIT:
                    continue

                c.append(_handle_zip(zf.open(filename), mode))
                stream_count += 1
            else:
                c.append(zf.open(filename))

        return chain_streams(c)


def fix_central_directory(zfile: BytesIO) -> BytesIO:
    """
    Fixes the central directory on bad zip files
    """
    # @NOTE See http://bugs.python.org/issue10694
    content = zfile.read()

    # reverse find: this string of bytes is the end of
    #  the zip's central directory.
    pos = content.rfind(b"\x50\x4b\x05\x06")

    if pos > 0:
        zfile.seek(pos + 20)
        zfile.truncate()
        zfile.write(b"\x00\x00")  # Zip file comment length: 0 byte length;
        zfile.seek(0)

    return zfile


def fix_central_directory_file(zip_file_path: Path) -> Path:
    """
    Fixes the central directory on bad zip files
    """
    # @NOTE See http://bugs.python.org/issue10694

    with zip_file_path.open("wb") as zfile:
        content = zfile.read()

        # reverse find: this string of bytes is the end of
        #  the zip's central directory.
        pos = content.rfind(b"\x50\x4b\x05\x06")

        if pos > 0:
            zfile.seek(pos + 20)
            zfile.truncate()
            zfile.write(b"\x00\x00")  # Zip file comment length: 0 byte length;
            zfile.seek(0)

        zip_file_path.write_bytes(zfile.read())

    return zip_file_path


def stream_zip_contents(file_obj: IO[bytes], mode: str = "w"):  # type: ignore
    """
    Steram out the entire contents of a zipfile
    handling embedded zips

    mode param is to compat with external libs like smart_open
    """
    with ZipFile(file_obj) as zf:
        # If there is only one file in the archive return it
        if len(zf.namelist()) == 1:
            return zf.open(zf.namelist()[0])

        c = []
        stream_count = 0

        for filename in zf.namelist():
            if filename.endswith(".zip"):
                if ZIP_LIMIT > 0 and stream_count >= ZIP_LIMIT:
                    continue

                c.append(stream_zip_contents(zf.open(filename), mode))
                stream_count += 1
            else:
                c.append(zf.open(filename))

        return chain_streams(c)


def download_and_unzip(url: str) -> str:
    """Download and unzip a multi-zip file"""

    dest_dir = mkdtemp(prefix=f"{settings.tmp_file_prefix}")

    logger.info(f"Saving to {dest_dir}")

    filename = get_filename_from_url(url)

    try:
        response = http.get(url)
    except Exception as e:
        logger.error(e)

    save_path = Path(dest_dir) / filename

    with save_path.open("wb+") as fh:
        fh.write(response.content)

    logger.info(f"Wrote file to {save_path}")

    with ZipFile(save_path) as zf:
        try:
            zf.extractall(dest_dir)
        except Exception as e:
            logger.error(e)
            zf = fix_central_directory_file(save_path)
            zf.extractall(dest_dir)

    os.remove(save_path)

    for _, _, files in os.walk(dest_dir):
        for file in files:
            file_path = Path(dest_dir) / file
            if file_path.suffix.lower() == ".zip":
                with ZipFile(file_path) as zf:
                    zf.extractall(dest_dir)
                os.remove(file_path)

    return dest_dir


if __name__ == "__main__":
    u = "https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/PUBLIC_DISPATCHIS_20220612.zip"
    d = download_and_unzip(u)
    print(d)
